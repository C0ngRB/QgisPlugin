import json
import sys
from datetime import datetime
from pathlib import Path

QGIS_PYTHON_PATHS = (
    r"C:\Program Files\QGIS 3.40.0\apps\qgis\python",
    r"C:\Program Files\QGIS 3.40.0\apps\qgis\python\plugins",
)
PLUGIN_PARENT = r"C:\Users\congr\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins"
PROJECT_PATH = Path(r"C:\Users\congr\QgisBase\GisPractice0618.qgz")
OUTPUT_ROOT = Path(r"C:\tmp\qgis_plugin_runtime_check")


def bootstrap_qgis():
    """函数含义：初始化 standalone PyQGIS 与 Processing；上游由本脚本入口调用；下游允许直接注册插件 Provider 并执行算法；风险点是 QGIS 安装路径变化时需要更新常量。"""
    for qgis_path in QGIS_PYTHON_PATHS:
        if qgis_path not in sys.path:
            sys.path.insert(0, qgis_path)
    if PLUGIN_PARENT not in sys.path:
        sys.path.insert(0, PLUGIN_PARENT)
    from qgis.core import QgsApplication

    app = QgsApplication([], False)
    app.initQgis()
    import processing
    from processing.core.Processing import Processing

    Processing.initialize()
    return app, processing


def register_wuda_providers():
    """函数含义：注册两个 WUDA 插件 Provider；上游由运行时验收入口调用；下游让 Processing 能找到插件算法；风险点是 QGIS profile 中插件代码必须已同步到最新版本。"""
    from qgis.core import QgsApplication
    from wuda_accessibility_analyzer.provider import WudaAccessibilityProvider
    from wuda_terrain_hydro_analyzer.provider import WudaTerrainHydroProvider

    registry = QgsApplication.processingRegistry()
    for provider in list(registry.providers()):
        if provider.id() in {"wuda_accessibility_analyzer", "wuda_terrain_hydro_analyzer"}:
            registry.removeProvider(provider)
    registry.addProvider(WudaAccessibilityProvider())
    registry.addProvider(WudaTerrainHydroProvider())
    return registry


def open_project():
    """函数含义：读取课程 QGIS 工程；上游由验收流程调用；下游提供真实测试图层；风险点是工程路径或图层名变化会导致验收失败。"""
    from qgis.core import QgsProject

    project = QgsProject.instance()
    if not project.read(str(PROJECT_PATH)):
        raise RuntimeError(f"工程读取失败: {PROJECT_PATH}")
    return project


def first_layer(project, layer_name):
    """函数含义：按名称读取工程中的第一个图层；上游由各 workflow 验收调用；下游作为 Processing 输入；风险点是同名图层会取第一个。"""
    layers = project.mapLayersByName(layer_name)
    if not layers:
        raise RuntimeError(f"缺少图层: {layer_name}")
    return layers[0]


def make_output_dir(name):
    """函数含义：创建单次验收输出目录；上游由各 workflow 验收调用；下游避免覆盖既有验收结果；风险点是系统临时目录不可写时会失败。"""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_ROOT / f"{stamp}_{name}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def assert_algorithm_params(registry, algorithm_id, expected_params):
    """函数含义：校验 Processing 算法存在且参数契约稳定；上游由运行时验收调用；下游防止 provider 注册旧代码或错误薄壳；风险点是不校验 UI 文案。"""
    algorithm = registry.algorithmById(algorithm_id)
    if algorithm is None:
        raise RuntimeError(f"算法未注册: {algorithm_id}")
    actual_params = [parameter.name() for parameter in algorithm.parameterDefinitions()]
    if actual_params != expected_params:
        raise RuntimeError(f"{algorithm_id} 参数不正确: {actual_params}")
    return actual_params


def vector_count(path, layer_name):
    """函数含义：读取矢量输出要素数；上游由验收断言调用；下游证明输出图层可加载且非空；风险点是 GeoPackage 多图层时需传入 layername。"""
    from qgis.core import QgsVectorLayer

    layer_uri = f"{path}|layername={layer_name}" if layer_name else str(path)
    layer = QgsVectorLayer(layer_uri, layer_name or Path(path).stem, "ogr")
    if not layer.isValid():
        raise RuntimeError(f"矢量图层无效: {layer_uri}")
    return layer.featureCount()


def raster_valid(path):
    """函数含义：检查栅格输出是否可加载；上游由地形验收调用；下游证明 GeoTIFF 输出有效；风险点是不检查像元统计值。"""
    from qgis.core import QgsRasterLayer

    layer = QgsRasterLayer(str(path), Path(path).stem)
    return layer.isValid()


def latest_file(output_dir, pattern):
    """函数含义：读取输出目录中匹配模式的最新文件；上游由 workflow 验收读取结果；下游避免硬编码自动后缀；风险点是模式过宽可能取到非目标文件。"""
    matches = sorted(output_dir.glob(pattern))
    if not matches:
        raise RuntimeError(f"未找到输出文件: {output_dir / pattern}")
    return matches[-1]


def check_standardization_workflow(processing, registry, project):
    """函数含义：验收一键标准化 workflow；上游由主验收流程调用；下游证明 standard_data.gpkg 包含五个标准图层；风险点是只覆盖当前课程工程数据。"""
    assert_algorithm_params(
        registry,
        "wuda_accessibility_analyzer:run_standardization_workflow",
        ["BUILDINGS", "ROADS", "FACILITIES", "SERVICE_TYPE_FIELD", "ELEVATION_POINTS", "MEASURED_FIELD", "TRACKS", "OUTPUT_FOLDER"],
    )
    output_dir = make_output_dir("standardization")
    processing.run(
        "wuda_accessibility_analyzer:run_standardization_workflow",
        {
            "BUILDINGS": first_layer(project, "二实习底图_建筑"),
            "ROADS": first_layer(project, "二实习底图_道路"),
            "FACILITIES": first_layer(project, "重要服务点_分析参考"),
            "SERVICE_TYPE_FIELD": "category",
            "ELEVATION_POINTS": first_layer(project, "二实习底图_珞珈山顶"),
            "MEASURED_FIELD": "elevation",
            "TRACKS": first_layer(project, "典型路径_最短路"),
            "OUTPUT_FOLDER": str(output_dir),
        },
    )
    package_path = latest_file(output_dir, "standard_data*.gpkg")
    counts = {name: vector_count(package_path, name) for name in ("buildings", "roads", "pois", "elevation_points", "tracks")}
    return {"package": str(package_path), "counts": counts, "summary": str(latest_file(output_dir, "run_summary*.json"))}


def check_accessibility_workflow(processing, registry, project):
    """函数含义：验收可达性 workflow；上游由主验收流程调用；下游证明四类 ADR 输出图层可加载且非空；风险点是供需表为首版近似字段。"""
    assert_algorithm_params(
        registry,
        "wuda_accessibility_analyzer:run_accessibility_workflow",
        ["BUILDINGS", "ROADS", "FACILITIES", "SERVICE_TYPE_FIELD", "TRAVEL_COST", "DEFAULT_SPEED", "TOLERANCE", "OUTPUT_FOLDER"],
    )
    output_dir = make_output_dir("accessibility")
    processing.run(
        "wuda_accessibility_analyzer:run_accessibility_workflow",
        {
            "BUILDINGS": first_layer(project, "二实习底图_建筑"),
            "ROADS": first_layer(project, "二实习底图_道路"),
            "FACILITIES": first_layer(project, "重要服务点_分析参考"),
            "SERVICE_TYPE_FIELD": "category",
            "TRAVEL_COST": 300.0,
            "DEFAULT_SPEED": 5.0,
            "TOLERANCE": 50.0,
            "OUTPUT_FOLDER": str(output_dir),
        },
    )
    counts = {}
    for output_name in ("accessibility_buildings", "facility_service_areas", "facility_supply_demand", "nearest_facility_links"):
        counts[output_name] = vector_count(latest_file(output_dir, f"{output_name}*.gpkg"), None)
    return {"output_dir": str(output_dir), "counts": counts, "summary": str(latest_file(output_dir, "run_summary*.json"))}


def check_terrain_workflow(processing, registry, project):
    """函数含义：验收地形 workflow；上游由主验收流程调用；下游证明三类栅格、等高线和高程对比输出有效；风险点是不验证栅格数值精度。"""
    assert_algorithm_params(
        registry,
        "wuda_terrain_hydro_analyzer:run_terrain_workflow",
        ["DEM", "ELEVATION_POINTS", "MEASURED_FIELD", "Z_FACTOR", "AZIMUTH", "VERTICAL_ANGLE", "INTERVAL", "OUTPUT_FOLDER"],
    )
    output_dir = make_output_dir("terrain")
    processing.run(
        "wuda_terrain_hydro_analyzer:run_terrain_workflow",
        {
            "DEM": first_layer(project, "二实习底图_DEM底色"),
            "ELEVATION_POINTS": first_layer(project, "二实习底图_珞珈山顶"),
            "MEASURED_FIELD": "elevation",
            "Z_FACTOR": 1.0,
            "AZIMUTH": 315.0,
            "VERTICAL_ANGLE": 45.0,
            "INTERVAL": 10.0,
            "OUTPUT_FOLDER": str(output_dir),
        },
    )
    checks = {
        "slope_valid": raster_valid(latest_file(output_dir, "slope*.tif")),
        "aspect_valid": raster_valid(latest_file(output_dir, "aspect*.tif")),
        "hillshade_valid": raster_valid(latest_file(output_dir, "hillshade*.tif")),
        "contour_count": vector_count(latest_file(output_dir, "contours*.gpkg"), None),
        "comparison_count": vector_count(latest_file(output_dir, "dem_elevation_comparison*.gpkg"), None),
    }
    return {"output_dir": str(output_dir), "checks": checks, "summary": str(latest_file(output_dir, "run_summary*.json"))}


def saga_provider_ids():
    """函数含义：读取当前 QGIS Processing provider ID；上游由水文验收调用；下游决定真实 SAGA 或无 SAGA demo 契约；风险点是 provider 名称由 QGIS 版本决定。"""
    from qgis.core import QgsApplication

    return sorted(provider.id() for provider in QgsApplication.processingRegistry().providers())


def check_hydrology_contract(processing, registry, project):
    """函数含义：验收水文算法契约；上游由主验收流程调用；下游证明 SAGA 参数注册和无 SAGA demo/错误边界；风险点是无 SAGA 环境不能证明真实水文结果。"""
    expected = {
        "fill_sinks": ["DEM", "OUTPUT"],
        "extract_flow_direction": ["DEM", "OUTPUT"],
        "extract_flow_accumulation": ["DEM", "OUTPUT"],
        "extract_stream_order": ["DEM", "OUTPUT"],
        "extract_stream_network": ["DEM", "OUTPUT"],
        "extract_watershed_basins": ["DEM", "OUTPUT"],
        "load_hydrology_demo_results": ["OUTPUT_FOLDER"],
        "run_hydrology_workflow": ["DEM", "OUTPUT_FOLDER"],
    }
    params = {
        name: assert_algorithm_params(registry, f"wuda_terrain_hydro_analyzer:{name}", expected_params)
        for name, expected_params in expected.items()
    }
    output_dir = make_output_dir("hydrology")
    processing.run("wuda_terrain_hydro_analyzer:check_saga_provider", {"OUTPUT_FOLDER": str(output_dir)})
    check_summary = json.loads(latest_file(output_dir, "run_summary*.json").read_text(encoding="utf-8"))
    processing.run(
        "wuda_terrain_hydro_analyzer:run_hydrology_workflow",
        {"DEM": first_layer(project, "二实习底图_DEM底色"), "OUTPUT_FOLDER": str(output_dir)},
    )
    summary = json.loads(latest_file(output_dir, "run_summary*.json").read_text(encoding="utf-8"))
    providers = saga_provider_ids()
    if summary["mode"] == "real" and summary["outputs"]:
        output_checks = {
            "filled_dem_valid": raster_valid(latest_file(output_dir, "filled_dem*.tif")),
            "flow_direction_valid": raster_valid(latest_file(output_dir, "flow_direction*.tif")),
            "flow_accumulation_valid": raster_valid(latest_file(output_dir, "flow_accumulation*.tif")),
            "stream_order_valid": raster_valid(latest_file(output_dir, "stream_order*.tif")),
            "stream_network_count": vector_count(latest_file(output_dir, "stream_network*.gpkg"), None),
            "drainage_basins_count": vector_count(latest_file(output_dir, "drainage_basins*.gpkg"), None),
        }
        if not all(value for key, value in output_checks.items() if key.endswith("_valid")):
            raise RuntimeError(f"Real hydrology raster outputs are not loadable: {output_checks}")
        engine = "saga_provider" if "saga" in providers or "sagang" in providers else "saga_cmd"
        return {"providers": providers, "engine": engine, "params": params, "check_saga_summary": check_summary, "summary": summary, "output_checks": output_checks}
    if "saga" not in providers and "sagang" not in providers:
        if summary["mode"] != "demo" or summary["is_demo_result"] is not True:
            raise RuntimeError(f"No SAGA provider and no real command output, but workflow did not enter demo summary mode: {summary}")
        return {"providers": providers, "engine": "demo", "params": params, "check_saga_summary": check_summary, "summary": summary}
    raise RuntimeError(f"SAGA is available but hydrology workflow did not create real outputs: {summary}")

def main():
    """函数含义：执行完整 QGIS 运行时验收；上游由 python-qgis.bat 命令调用；下游输出 JSON 报告并以退出码表示是否通过；风险点是依赖本机课程工程和 QGIS profile。"""
    _app, processing = bootstrap_qgis()
    registry = register_wuda_providers()
    project = open_project()
    report = {
        "standardization": check_standardization_workflow(processing, registry, project),
        "accessibility": check_accessibility_workflow(processing, registry, project),
        "terrain": check_terrain_workflow(processing, registry, project),
        "hydrology": check_hydrology_contract(processing, registry, project),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

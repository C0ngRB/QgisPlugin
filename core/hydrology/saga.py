from pathlib import Path

from core.io.output_naming import unique_output_path
from core.qgis_processing.runner import run_processing_algorithm
from core.reporting.summary import write_run_summary

DEMO_FILE_NAMES = (
    "demo_filled_dem.tif",
    "demo_flow_direction.tif",
    "demo_flow_accumulation.tif",
    "demo_stream_order.tif",
    "demo_stream_network.gpkg",
    "demo_drainage_basins.gpkg",
)

SAGA_ALGORITHM_CANDIDATES = {
    "fill_sinks": ("sagang:fillsinkswangliu", "saga:fillsinkswangliu", "saga:fillsinks", "sagang:fillsinksxxlwangliu"),
    "extract_flow_direction": ("sagang:flowaccumulationtopdown", "saga:flowaccumulationtopdown"),
    "extract_flow_accumulation": ("sagang:flowaccumulationtopdown", "saga:flowaccumulationtopdown"),
    "extract_stream_order": ("sagang:strahlerorder", "saga:strahlerorder"),
    "extract_stream_network": ("sagang:channelnetworkanddrainagebasins", "saga:channelnetworkanddrainagebasins"),
    "extract_watershed_basins": ("sagang:channelnetworkanddrainagebasins", "saga:channelnetworkanddrainagebasins"),
}


def saga_provider_available():
    """函数含义：检测 QGIS SAGA Provider 是否可用；上游由水文算法和手工验收调用；下游决定真实水文或 demo 模式；风险点是只能在 QGIS Python 环境中调用。"""
    from qgis.core import QgsApplication

    return QgsApplication.processingRegistry().providerById("saga") is not None or QgsApplication.processingRegistry().providerById("sagang") is not None


def require_saga_algorithm(algorithm_key):
    """函数含义：解析 ADR 水文步骤对应的 SAGA Processing 算法 ID；上游由真实水文细粒度函数调用；下游确保只调用 SAGA Provider；风险点是不同 QGIS/SAGA 版本算法 ID 可能不同，找不到时必须显式失败。"""
    from qgis.core import QgsApplication

    if not saga_provider_available():
        raise RuntimeError("SAGA Provider 不可用，不能执行真实水文分析；请安装/启用 SAGA，或提供真实 demo/sample 结果。")
    registry = QgsApplication.processingRegistry()
    for algorithm_id in SAGA_ALGORITHM_CANDIDATES[algorithm_key]:
        if registry.algorithmById(algorithm_id) is not None:
            return algorithm_id
    raise RuntimeError(f"SAGA Provider 已加载，但未找到 {algorithm_key} 对应的受支持算法 ID。")


def fill_sinks(dem_layer, output, context, feedback):
    """函数含义：执行 SAGA 填洼步骤；上游由 fill_sinks 算法或水文 workflow 传入 DEM；下游输出 filled_dem.tif；风险点是无 SAGA 时必须失败，不能改用 GRASS 或 native 替代。"""
    return _run_single_output_saga("fill_sinks", {"ELEV": dem_layer, "DEM": output}, "DEM", context, feedback)


def extract_flow_direction(dem_layer, output, context, feedback):
    """函数含义：执行 SAGA 流向派生步骤；上游由 extract_flow_direction 算法传入 DEM；下游输出 flow_direction.tif；风险点是算法 ID 和参数随 SAGA 版本变化，失败时必须暴露错误。"""
    return _run_single_output_saga("extract_flow_direction", {"ELEVATION": dem_layer, "FLOW": output}, "FLOW", context, feedback)


def extract_flow_accumulation(dem_layer, output, context, feedback):
    """函数含义：执行 SAGA 流量累积派生步骤；上游由 extract_flow_accumulation 算法传入 DEM；下游输出 flow_accumulation.tif；风险点是无 SAGA 时不能生成近似伪结果。"""
    return _run_single_output_saga("extract_flow_accumulation", {"ELEVATION": dem_layer, "FLOW": output}, "FLOW", context, feedback)


def extract_stream_order(dem_layer, output, context, feedback):
    """函数含义：执行 SAGA Strahler Order 步骤；上游由 extract_stream_order 算法传入 DEM；下游输出 stream_order.tif；风险点是输入 DEM 应为水文处理后的 DEM。"""
    return _run_single_output_saga("extract_stream_order", {"DEM": dem_layer, "STRAHLER": output}, "STRAHLER", context, feedback)


def extract_stream_network(dem_layer, output, context, feedback):
    """函数含义：执行 SAGA 河网提取步骤；上游由 extract_stream_network 算法传入 DEM；下游输出 stream_network.gpkg；风险点是阈值使用 SAGA 默认值，课程报告需说明。"""
    return _run_single_output_saga("extract_stream_network", {"DEM": dem_layer, "SEGMENTS": output}, "SEGMENTS", context, feedback)


def extract_watershed_basins(dem_layer, output, context, feedback):
    """函数含义：执行 SAGA 流域盆地提取步骤；上游由 extract_watershed_basins 算法传入 DEM；下游输出 drainage_basins.gpkg；风险点是无真实 SAGA 输出时不能用演示边界冒充。"""
    return _run_single_output_saga("extract_watershed_basins", {"DEM": dem_layer, "BASINS": output}, "BASINS", context, feedback)


def run_hydrology_workflow(dem_layer, output_folder, context, feedback, demo_dir=None):
    """函数含义：执行水文 workflow 或在无 SAGA 时进入 demo 契约；上游由 run_hydrology_workflow 算法传入 DEM 和输出目录；下游生成真实水文结果或 demo 模式摘要；风险点是无 SAGA 且无真实 demo 数据时只能记录原因，不能造假图层。"""
    resolved_output_folder = Path(output_folder)
    resolved_output_folder.mkdir(parents=True, exist_ok=True)
    if not saga_provider_available():
        return load_hydrology_demo_results(demo_dir, output_folder, "SAGA Provider 不可用，未执行真实水文流程。", "wuda_terrain_hydro_analyzer:run_hydrology_workflow")
    outputs = {}
    outputs["filled_dem"] = fill_sinks(dem_layer, str(unique_output_path(resolved_output_folder / "filled_dem.tif")), context, feedback)["OUTPUT"]
    outputs["flow_direction"] = extract_flow_direction(outputs["filled_dem"], str(unique_output_path(resolved_output_folder / "flow_direction.tif")), context, feedback)["OUTPUT"]
    outputs["flow_accumulation"] = extract_flow_accumulation(outputs["filled_dem"], str(unique_output_path(resolved_output_folder / "flow_accumulation.tif")), context, feedback)["OUTPUT"]
    outputs["stream_order"] = extract_stream_order(outputs["filled_dem"], str(unique_output_path(resolved_output_folder / "stream_order.tif")), context, feedback)["OUTPUT"]
    outputs["stream_network"] = extract_stream_network(outputs["filled_dem"], str(unique_output_path(resolved_output_folder / "stream_network.gpkg")), context, feedback)["OUTPUT"]
    outputs["drainage_basins"] = extract_watershed_basins(outputs["filled_dem"], str(unique_output_path(resolved_output_folder / "drainage_basins.gpkg")), context, feedback)["OUTPUT"]
    summary_path = write_run_summary(resolved_output_folder, "wuda_terrain_hydro_analyzer:run_hydrology_workflow", outputs=list(outputs.values()), mode="real", warnings=[])
    return {"OUTPUT_FOLDER": str(resolved_output_folder), "OUTPUTS": outputs, "SUMMARY": str(summary_path), "MODE": "real"}


def load_hydrology_demo_results(demo_dir, output_folder, reason, algorithm_id="wuda_terrain_hydro_analyzer:load_hydrology_demo_results"):
    """函数含义：复制已打包的真实 demo/sample 水文结果并写 demo 摘要；上游由 load_hydrology_demo_results 或无 SAGA workflow 调用；下游给验收提供 demo 模式证据；风险点是当前仓库没有真实 demo 数据时必须只写摘要不生成伪图层。"""
    resolved_output_folder = Path(output_folder)
    resolved_output_folder.mkdir(parents=True, exist_ok=True)
    resolved_demo_dir = Path(demo_dir) if demo_dir else None
    outputs = []
    warnings = [reason]
    if resolved_demo_dir and resolved_demo_dir.exists():
        for file_name in DEMO_FILE_NAMES:
            source = resolved_demo_dir / file_name
            if source.exists():
                target = unique_output_path(resolved_output_folder / file_name)
                target.write_bytes(source.read_bytes())
                outputs.append(str(target))
    if not outputs:
        warnings.append("插件包未包含真实 demo/sample 水文结果；未生成任何 demo 空间图层。")
    summary_path = write_run_summary(resolved_output_folder, algorithm_id, outputs=outputs, mode="demo", warnings=warnings)
    return {"OUTPUT_FOLDER": str(resolved_output_folder), "OUTPUTS": outputs, "SUMMARY": str(summary_path), "MODE": "demo"}


def _run_single_output_saga(algorithm_key, parameters, output_key, context, feedback):
    """函数含义：执行单输出 SAGA 水文算法；上游由具体水文函数传入参数；下游统一调用 Processing 并返回 OUTPUT 键；风险点是参数名需与 SAGA 版本匹配，不匹配时让 QGIS 抛出错误。"""
    algorithm_id = require_saga_algorithm(algorithm_key)
    result = run_processing_algorithm(algorithm_id, parameters, context, feedback)
    return {"OUTPUT": result.get(output_key) or result.get("OUTPUT")}
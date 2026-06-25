import os
import shutil
import subprocess
import sys
import tempfile
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

SAGA_CMD_TOOLS = {
    "fill_sinks": ("ta_preprocessor", "4"),
    "extract_flow_direction": ("ta_preprocessor", "4"),
    "extract_flow_accumulation": ("ta_hydrology", "0"),
    "extract_stream_order": ("ta_channels", "6"),
    "extract_stream_network": ("ta_channels", "5"),
    "extract_watershed_basins": ("ta_channels", "5"),
}


def saga_provider_available():
    """函数含义：检测 QGIS SAGA Provider 是否可用；上游由水文算法和手工验收调用；下游决定真实水文或 demo 模式；风险点是只能在 QGIS Python 环境中调用。"""
    from qgis.core import QgsApplication

    return QgsApplication.processingRegistry().providerById("saga") is not None or QgsApplication.processingRegistry().providerById("sagang") is not None


def saga_cmd_path():
    """Purpose: find saga_cmd.exe in the active QGIS/OSGeo4W install; upstream callers are hydrology algorithms; downstream runs real SAGA when the QGIS provider is absent; risk is that executable discovery does not prove every tool can run."""
    env_path = os.environ.get("SAGA_CMD")
    if env_path and Path(env_path).exists():
        return str(Path(env_path))
    found = shutil.which("saga_cmd") or shutil.which("saga_cmd.exe")
    if found:
        return found
    for candidate in _saga_cmd_candidates():
        if candidate.exists():
            return str(candidate)
    return None


def saga_cmd_available():
    """Purpose: report whether SAGA command-line execution is discoverable; upstream callers are workflow mode checks and tests; downstream permits real hydrology without the Processing provider; risk is that this is only an existence check."""
    return saga_cmd_path() is not None


def saga_available():
    """Purpose: report whether any supported SAGA engine exists; upstream caller is the hydrology workflow; downstream chooses real execution or demo summary; risk is that provider probing can fail outside QGIS and must not hide saga_cmd."""
    try:
        provider_available = saga_provider_available()
    except Exception:
        provider_available = False
    return provider_available or saga_cmd_available()


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
    if not saga_available():
        return load_hydrology_demo_results(demo_dir, output_folder, "SAGA Provider and saga_cmd.exe are unavailable; real hydrology was not executed.", "wuda_terrain_hydro_analyzer:run_hydrology_workflow")
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
    """Purpose: execute one SAGA hydrology output; upstream callers are fine-grained hydrology functions; downstream uses Processing first and saga_cmd second; risk is that both paths must remain real SAGA, never GRASS/native substitutes."""
    try:
        provider_available = saga_provider_available()
    except Exception:
        provider_available = False
    if provider_available:
        algorithm_id = require_saga_algorithm(algorithm_key)
        result = run_processing_algorithm(algorithm_id, parameters, context, feedback)
        return {"OUTPUT": result.get(output_key) or result.get("OUTPUT")}
    return {"OUTPUT": _run_saga_cmd_single_output(algorithm_key, parameters, output_key, feedback)}


def _run_saga_cmd_single_output(algorithm_key, parameters, output_key, feedback):
    """Purpose: run one hydrology output through saga_cmd.exe; upstream caller is the provider-missing SAGA wrapper; downstream writes GeoTIFF/GeoPackage outputs; risk is command failure must raise instead of leaving empty files."""
    saga_cmd = saga_cmd_path()
    if not saga_cmd:
        raise RuntimeError("SAGA Provider unavailable and saga_cmd.exe was not found; real hydrology cannot run.")
    dem_path = _layer_source_path(parameters.get("ELEV") or parameters.get("ELEVATION") or parameters.get("DEM"))
    output_path = _filesystem_output_path(parameters[output_key])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wuda_saga_") as temp_dir:
        command = _saga_cmd_command(algorithm_key, dem_path, output_path, Path(temp_dir))
        _run_saga_process(saga_cmd, command, feedback)
    if not output_path.exists():
        raise RuntimeError(f"SAGA finished without creating the target output: {output_path}")
    return str(output_path)


def _saga_cmd_command(algorithm_key, dem_path, output_path, temp_dir):
    """Purpose: build saga_cmd arguments for ADR hydrology steps; upstream caller is the command wrapper; downstream passes the list to subprocess; risk is these parameters are bound to SAGA 9.x and tests must expose version drift."""
    library, tool_id = SAGA_CMD_TOOLS[algorithm_key]
    if algorithm_key == "fill_sinks":
        return [library, tool_id, "-ELEV", dem_path, "-FILLED", str(output_path), "-FDIR", str(temp_dir / "flow_direction.tif"), "-WSHED", str(temp_dir / "watershed_basins.tif")]
    if algorithm_key == "extract_flow_direction":
        return [library, tool_id, "-ELEV", dem_path, "-FILLED", str(temp_dir / "filled_dem.tif"), "-FDIR", str(output_path), "-WSHED", str(temp_dir / "watershed_basins.tif")]
    if algorithm_key == "extract_flow_accumulation":
        return [library, tool_id, "-ELEVATION", dem_path, "-FLOW", str(output_path)]
    if algorithm_key == "extract_stream_order":
        return [library, tool_id, "-DEM", dem_path, "-STRAHLER", str(output_path)]
    if algorithm_key == "extract_stream_network":
        return [library, tool_id, "-DEM", dem_path, "-SEGMENTS", str(output_path), "-BASINS", str(temp_dir / "drainage_basins.gpkg"), "-THRESHOLD", "5"]
    return [library, tool_id, "-DEM", dem_path, "-SEGMENTS", str(temp_dir / "stream_network.gpkg"), "-BASINS", str(output_path), "-THRESHOLD", "5"]


def _run_saga_process(saga_cmd, command, feedback):
    """Purpose: run the saga_cmd subprocess and forward concise logs; upstream caller is the command wrapper; downstream creates real SAGA output files; risk is system PROJ_LIB pollution, so the child env is cleaned."""
    env = os.environ.copy()
    env.pop("PROJ_LIB", None)
    proj_data = _qgis_proj_data_path()
    if proj_data:
        env["PROJ_DATA"] = str(proj_data)
    saga_bin = str(Path(saga_cmd).parent)
    env["PATH"] = saga_bin + os.pathsep + env.get("PATH", "")
    completed = subprocess.run([saga_cmd, *command], capture_output=True, text=True, env=env, check=False)
    if feedback and completed.stdout:
        feedback.pushInfo(_tail_text(completed.stdout))
    if completed.returncode != 0:
        raise RuntimeError(f"saga_cmd failed: {_tail_text(completed.stderr or completed.stdout)}")


def _layer_source_path(layer_or_path):
    """Purpose: resolve a QGIS raster layer or path to a filesystem path; upstream caller is saga_cmd execution; downstream supplies the DEM input; risk is only file-backed rasters are supported."""
    source = layer_or_path.source() if hasattr(layer_or_path, "source") else str(layer_or_path)
    return source.split("|", 1)[0]


def _filesystem_output_path(output):
    """Purpose: collapse a QGIS output URI to a SAGA-writable file path; upstream caller is saga_cmd execution; downstream passes the path as an output parameter; risk is GeoPackage layername suffixes are ignored."""
    return Path(str(output).split("|", 1)[0])


def _saga_cmd_candidates():
    """Purpose: list saga_cmd.exe candidates from the current process; upstream caller is saga_cmd_path; downstream reduces manual configuration; risk is limited to standard QGIS/OSGeo4W layouts."""
    roots = []
    try:
        from qgis.core import QgsApplication

        prefix = Path(QgsApplication.prefixPath())
        roots.append(prefix.parents[1])
    except Exception:
        pass
    executable = Path(sys.executable)
    roots.extend([parent for parent in executable.parents if parent.name.lower().startswith(("qgis", "osgeo4w"))])
    roots.append(Path(r"C:\Program Files\QGIS 3.40.0"))
    return [root / "apps" / "saga" / "saga_cmd.exe" for root in roots]


def _qgis_proj_data_path():
    """Purpose: locate QGIS proj.db for the child process; upstream caller builds the saga_cmd environment; downstream avoids PostgreSQL or other PROJ installs; risk is non-standard installs may need external PROJ_DATA."""
    command_path = saga_cmd_path()
    if not command_path:
        return None
    candidate = Path(command_path).parents[2] / "share" / "proj"
    if (candidate / "proj.db").exists():
        return candidate
    return None


def _tail_text(text, max_chars=1200):
    """Purpose: keep the tail of SAGA logs for QGIS messages and exceptions; upstream caller is subprocess handling; downstream avoids flooding errors with progress output; risk is very short tails can omit clues."""
    return text[-max_chars:].strip()

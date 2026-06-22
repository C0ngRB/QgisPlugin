from pathlib import Path

from core.reporting.summary import write_run_summary
from core.standardization.geopackage import write_standard_geopackage
from core.standardization.vector import (
    standardize_buildings,
    standardize_elevation_points,
    standardize_pois,
    standardize_roads,
    standardize_tracks,
)

TEMPORARY_OUTPUT = "TEMPORARY_OUTPUT"


def run_standardization_workflow(buildings_layer, roads_layer, pois_layer, service_type_field, elevation_points_layer, measured_field, tracks_layer, output_folder, context, feedback):
    """函数含义：一键生成标准化 GeoPackage；上游由两个插件的 run_standardization_workflow 算法传入原始业务图层和字段；下游复用标准化细粒度函数并写出 standard_data.gpkg 与 run_summary.json；风险点是字段参数必须来自用户显式选择，不能自动猜测。"""
    resolved_output_folder = Path(output_folder)
    resolved_output_folder.mkdir(parents=True, exist_ok=True)
    standardized = {
        "buildings": _named_layer(standardize_buildings(buildings_layer, TEMPORARY_OUTPUT, context, feedback)["OUTPUT"], "buildings", context),
        "roads": _named_layer(standardize_roads(roads_layer, 5.0, TEMPORARY_OUTPUT, context, feedback)["OUTPUT"], "roads", context),
        "pois": _named_layer(standardize_pois(pois_layer, service_type_field, TEMPORARY_OUTPUT, context, feedback)["OUTPUT"], "pois", context),
        "elevation_points": _named_layer(standardize_elevation_points(elevation_points_layer, measured_field, TEMPORARY_OUTPUT, context, feedback)["OUTPUT"], "elevation_points", context),
        "tracks": _named_layer(standardize_tracks(tracks_layer, TEMPORARY_OUTPUT, context, feedback)["OUTPUT"], "tracks", context),
    }
    package_result = write_standard_geopackage(
        standardized["buildings"],
        standardized["roads"],
        standardized["pois"],
        standardized["elevation_points"],
        standardized["tracks"],
        resolved_output_folder / "standard_data.gpkg",
        context,
        feedback,
    )
    summary_path = write_run_summary(
        resolved_output_folder,
        "common:run_standardization_workflow",
        outputs=[package_result["OUTPUT"]],
        warnings=["道路标准化使用默认步行速度 5.0 km/h；如需调整，请运行细粒度 standardize_roads。"],
    )
    return {"OUTPUT_FOLDER": str(resolved_output_folder), "PACKAGE": package_result["OUTPUT"], "SUMMARY": str(summary_path)}

def _named_layer(layer_ref, layer_name, context):
    """函数含义：解析并命名标准化中间图层；上游由标准化 workflow 在打包前调用；下游让 native:package 写出 ADR 标准图层名；风险点是临时输出可能是图层对象也可能是 context 内的图层 ID。"""
    layer = layer_ref
    if not hasattr(layer, "setName") and hasattr(context, "getMapLayer"):
        resolved_layer = context.getMapLayer(layer_ref)
        if resolved_layer is not None:
            layer = resolved_layer
    if hasattr(layer, "setName"):
        layer.setName(layer_name)
    return layer
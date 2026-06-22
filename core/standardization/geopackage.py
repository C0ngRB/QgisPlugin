from pathlib import Path

from core.io.output_naming import unique_output_path
from core.qgis_processing.runner import run_processing_algorithm


def write_standard_geopackage(buildings_layer, roads_layer, pois_layer, elevation_points_layer, tracks_layer, output_path, context, feedback):
    """函数含义：把标准化业务图层写入一个 GeoPackage；上游由 write_standard_geopackage Processing 算法传入各标准图层；下游调用 native:package 生成 standard_data.gpkg；风险点是输出图层名取自输入图层名，调用方应传入已命名的标准图层。"""
    resolved_output = unique_output_path(Path(output_path))
    return run_processing_algorithm(
        "native:package",
        {
            "LAYERS": [buildings_layer, roads_layer, pois_layer, elevation_points_layer, tracks_layer],
            "OUTPUT": str(resolved_output),
            "OVERWRITE": False,
            "SAVE_STYLES": False,
            "SAVE_METADATA": True,
            "SELECTED_FEATURES_ONLY": False,
            "EXPORT_RELATED_LAYERS": False,
        },
        context,
        feedback,
    )
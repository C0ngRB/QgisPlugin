from pathlib import Path

from core.io.output_naming import unique_output_path
from core.reporting.summary import write_run_summary
from core.terrain.basic_terrain import extract_aspect, extract_contours, extract_hillshade, extract_slope
from core.terrain.elevation_compare import compare_dem_with_elevation_points


def run_terrain_workflow(dem_layer, elevation_points_layer, measured_field, output_folder, z_factor, azimuth, vertical_angle, contour_interval, context, feedback):
    """函数含义：一键生成基础地形分析成果；上游由 run_terrain_workflow Processing 算法传入 DEM、高程点和地形参数；下游复用坡度、坡向、晕渲、等高线和高程对比细粒度函数；风险点是 DEM 坐标单位与高程单位不一致时必须由用户调整 Z 因子。"""
    resolved_output_folder = Path(output_folder)
    resolved_output_folder.mkdir(parents=True, exist_ok=True)
    outputs = {
        "slope": extract_slope(dem_layer, z_factor, str(unique_output_path(resolved_output_folder / "slope.tif")), context, feedback)["OUTPUT"],
        "aspect": extract_aspect(dem_layer, z_factor, str(unique_output_path(resolved_output_folder / "aspect.tif")), context, feedback)["OUTPUT"],
        "hillshade": extract_hillshade(dem_layer, z_factor, azimuth, vertical_angle, str(unique_output_path(resolved_output_folder / "hillshade.tif")), context, feedback)["OUTPUT"],
        "contours": extract_contours(dem_layer, contour_interval, str(unique_output_path(resolved_output_folder / "contours.gpkg")), context, feedback)["OUTPUT"],
        "dem_elevation_comparison": compare_dem_with_elevation_points(elevation_points_layer, measured_field, dem_layer, str(unique_output_path(resolved_output_folder / "dem_elevation_comparison.gpkg")), context, feedback)["OUTPUT"],
    }
    summary_path = write_run_summary(
        resolved_output_folder,
        "wuda_terrain_hydro_analyzer:run_terrain_workflow",
        outputs=list(outputs.values()),
        warnings=[],
    )
    return {"OUTPUT_FOLDER": str(resolved_output_folder), "OUTPUTS": outputs, "SUMMARY": str(summary_path)}
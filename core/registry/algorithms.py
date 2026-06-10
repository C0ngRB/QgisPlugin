ACCESSIBILITY_PROVIDER_ID = "wuda_accessibility_analyzer"
TERRAIN_HYDRO_PROVIDER_ID = "wuda_terrain_hydro_analyzer"

STANDARDIZATION_ALGORITHMS = (
    "validate_input_layers",
    "reproject_to_analysis_crs",
    "standardize_buildings",
    "standardize_roads",
    "standardize_pois",
    "standardize_elevation_points",
    "standardize_tracks",
    "write_standard_geopackage",
)

ACCESSIBILITY_ALGORITHMS = (
    "calculate_road_length",
    "build_network_cost",
    "generate_facility_buffers",
    "calculate_nearest_facility",
    "calculate_service_area",
    "calculate_shortest_path",
    "calculate_facility_suitability",
    "run_standardization_workflow",
    "run_accessibility_workflow",
)

TERRAIN_HYDRO_ALGORITHMS = (
    "extract_slope",
    "extract_aspect",
    "extract_hillshade",
    "extract_contours",
    "compare_dem_with_elevation_points",
    "check_saga_provider",
    "fill_sinks",
    "extract_flow_direction",
    "extract_flow_accumulation",
    "extract_stream_order",
    "extract_stream_network",
    "extract_watershed_basins",
    "load_hydrology_demo_results",
    "run_standardization_workflow",
    "run_terrain_workflow",
    "run_hydrology_workflow",
)

DISPLAY_NAMES = {
    "validate_input_layers": "校验输入图层",
    "reproject_to_analysis_crs": "转换到分析 CRS",
    "standardize_buildings": "标准化建筑图层",
    "standardize_roads": "标准化道路图层",
    "standardize_pois": "标准化 POI 图层",
    "standardize_elevation_points": "标准化高程点",
    "standardize_tracks": "标准化轨迹",
    "write_standard_geopackage": "写入标准 GeoPackage",
    "calculate_road_length": "计算道路长度",
    "build_network_cost": "构建网络成本字段",
    "generate_facility_buffers": "生成设施缓冲区",
    "calculate_nearest_facility": "计算最近设施",
    "calculate_service_area": "计算网络服务区",
    "calculate_shortest_path": "计算最短路径",
    "calculate_facility_suitability": "计算设施适宜性",
    "extract_slope": "提取坡度",
    "extract_aspect": "提取坡向",
    "extract_hillshade": "提取晕渲",
    "extract_contours": "提取等高线",
    "compare_dem_with_elevation_points": "DEM 与高程点对比",
    "check_saga_provider": "检查 SAGA Provider",
    "fill_sinks": "填洼",
    "extract_flow_direction": "提取流向",
    "extract_flow_accumulation": "提取流量累积",
    "extract_stream_order": "提取河网级别",
    "extract_stream_network": "提取河网",
    "extract_watershed_basins": "提取流域盆地",
    "load_hydrology_demo_results": "加载水文演示结果",
    "run_standardization_workflow": "运行数据标准化工作流",
    "run_accessibility_workflow": "运行可达性工作流",
    "run_terrain_workflow": "运行地形分析工作流",
    "run_hydrology_workflow": "运行水文分析工作流",
}


def provider_algorithms(provider_id):
    """函数含义：返回指定插件应注册的算法名；上游由插件 Provider、UI 和测试调用；下游保证两个插件的算法边界一致；风险点是未知 provider_id 必须直接失败。"""
    if provider_id == ACCESSIBILITY_PROVIDER_ID:
        return STANDARDIZATION_ALGORITHMS + ACCESSIBILITY_ALGORITHMS
    if provider_id == TERRAIN_HYDRO_PROVIDER_ID:
        return STANDARDIZATION_ALGORITHMS + TERRAIN_HYDRO_ALGORITHMS
    raise ValueError(f"未知 Provider ID: {provider_id}")


def algorithm_display_name(algorithm_name):
    """函数含义：返回算法中文显示名；上游由 Provider 和 UI 调用；下游统一工具箱文案；风险点是注册表缺项会让 UI 出现英文内部名。"""
    return DISPLAY_NAMES.get(algorithm_name, algorithm_name)

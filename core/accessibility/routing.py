from core.qgis_processing.network_runner import run_native_network_algorithm


SHORTEST_STRATEGY = 0
BIDIRECTIONAL = 2
TEMPORARY_OUTPUT = "TEMPORARY_OUTPUT"


def calculate_service_area(roads_layer, start_points_layer, travel_cost, default_speed_kmh, tolerance, output, context, feedback):
    """函数含义：基于 QGIS native 网络算法从设施点生成服务区线；上游由 calculate_service_area Processing 算法传入道路、设施和成本阈值；下游调用 native:serviceareafromlayer 输出可制图线图层；风险点是输出为网络可达线段，不是面状覆盖区。"""
    result = run_native_network_algorithm(
        "serviceareafromlayer",
        {
            "INPUT": roads_layer,
            "STRATEGY": SHORTEST_STRATEGY,
            "DIRECTION_FIELD": "",
            "VALUE_FORWARD": "",
            "VALUE_BACKWARD": "",
            "VALUE_BOTH": "",
            "DEFAULT_DIRECTION": BIDIRECTIONAL,
            "SPEED_FIELD": "",
            "DEFAULT_SPEED": default_speed_kmh,
            "TOLERANCE": tolerance,
            "START_POINTS": start_points_layer,
            "TRAVEL_COST": travel_cost,
            "TRAVEL_COST2": 0,
            "INCLUDE_BOUNDS": False,
            "POINT_TOLERANCE": tolerance,
            "OUTPUT_LINES": output,
            "OUTPUT": TEMPORARY_OUTPUT,
            "OUTPUT_NON_ROUTABLE": TEMPORARY_OUTPUT,
        },
        context,
        feedback,
    )
    return {"OUTPUT": result["OUTPUT_LINES"]}


def calculate_shortest_path(roads_layer, start_point, end_points_layer, default_speed_kmh, tolerance, output, context, feedback):
    """函数含义：基于 QGIS native 网络算法从一个起点到目标图层生成最短路径；上游由 calculate_shortest_path Processing 算法传入道路、起点和终点图层；下游调用 native:shortestpathpointtolayer 输出路径线图层；风险点是首版按最短距离策略，不按完整 OD 矩阵批量求解。"""
    result = run_native_network_algorithm(
        "shortestpathpointtolayer",
        {
            "INPUT": roads_layer,
            "STRATEGY": SHORTEST_STRATEGY,
            "DIRECTION_FIELD": "",
            "VALUE_FORWARD": "",
            "VALUE_BACKWARD": "",
            "VALUE_BOTH": "",
            "DEFAULT_DIRECTION": BIDIRECTIONAL,
            "SPEED_FIELD": "",
            "DEFAULT_SPEED": default_speed_kmh,
            "TOLERANCE": tolerance,
            "START_POINT": start_point,
            "END_POINTS": end_points_layer,
            "POINT_TOLERANCE": tolerance,
            "OUTPUT": output,
            "OUTPUT_NON_ROUTABLE": TEMPORARY_OUTPUT,
        },
        context,
        feedback,
    )
    return {"OUTPUT": result["OUTPUT"]}
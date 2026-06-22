from core.qgis_processing.runner import run_processing_algorithm


def calculate_nearest_facility(source_layer, facility_layer, neighbors, max_distance, output, context, feedback):
    """函数含义：生成源要素到最近设施的校核连线；上游由 calculate_nearest_facility Processing 算法传入源图层和设施图层；下游调用 QGIS native:shortestline 输出线图层；风险点是这是几何最近距离，不是网络路径成本。"""
    return run_processing_algorithm(
        "native:shortestline",
        {
            "SOURCE": source_layer,
            "DESTINATION": facility_layer,
            "METHOD": 0,
            "NEIGHBORS": neighbors,
            "DISTANCE": max_distance,
            "OUTPUT": output,
        },
        context,
        feedback,
    )

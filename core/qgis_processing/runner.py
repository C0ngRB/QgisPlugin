def run_processing_algorithm(algorithm_id, parameters, context, feedback):
    """函数含义：统一调用 QGIS Processing 算法；上游由 core 空间分析流程调用；下游执行 QGIS native/GDAL/SAGA 算法；风险点是 algorithm_id 或参数不兼容会抛出 QGIS 异常。"""
    import processing

    return processing.run(
        algorithm_id,
        parameters,
        context=context,
        feedback=feedback,
        is_child_algorithm=True,
    )

from core.qgis_processing.runner import run_processing_algorithm


def generate_facility_buffers(input_layer, distance, output, context, feedback):
    """函数含义：生成设施服务缓冲区面图层；上游由 generate_facility_buffers Processing 算法传入设施图层和距离；下游调用 QGIS native:buffer 并返回输出图层；风险点是距离单位取决于输入图层 CRS。"""
    return run_processing_algorithm(
        "native:buffer",
        {
            "INPUT": input_layer,
            "DISTANCE": distance,
            "SEGMENTS": 16,
            "END_CAP_STYLE": 0,
            "JOIN_STYLE": 0,
            "MITER_LIMIT": 2,
            "DISSOLVE": False,
            "OUTPUT": output,
        },
        context,
        feedback,
    )
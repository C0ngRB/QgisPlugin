from core.qgis_processing.runner import run_processing_algorithm


FIELD_TYPE_DECIMAL = 0


def calculate_road_length(input_layer, output, context, feedback):
    """函数含义：为道路线图层计算 length_m 字段；上游由 calculate_road_length Processing 算法传入道路图层；下游调用 QGIS native:fieldcalculator 输出线图层；风险点是长度单位取决于图层 CRS，必须使用米制投影。"""
    return run_processing_algorithm(
        "native:fieldcalculator",
        {
            "INPUT": input_layer,
            "FIELD_NAME": "length_m",
            "FIELD_TYPE": FIELD_TYPE_DECIMAL,
            "FIELD_LENGTH": 20,
            "FIELD_PRECISION": 3,
            "FORMULA": "$length",
            "OUTPUT": output,
        },
        context,
        feedback,
    )


def build_network_cost(input_layer, default_speed_kmh, output, context, feedback):
    """函数含义：为道路线图层构建 length_m 和 access_cost 字段；上游由 build_network_cost Processing 算法传入道路和默认速度；下游连续调用字段计算器输出线图层；风险点是默认速度不代表真实分路段速度。"""
    length_result = run_processing_algorithm(
        "native:fieldcalculator",
        {
            "INPUT": input_layer,
            "FIELD_NAME": "length_m",
            "FIELD_TYPE": FIELD_TYPE_DECIMAL,
            "FIELD_LENGTH": 20,
            "FIELD_PRECISION": 3,
            "FORMULA": "$length",
            "OUTPUT": "TEMPORARY_OUTPUT",
        },
        context,
        feedback,
    )
    return run_processing_algorithm(
        "native:fieldcalculator",
        {
            "INPUT": length_result["OUTPUT"],
            "FIELD_NAME": "access_cost",
            "FIELD_TYPE": FIELD_TYPE_DECIMAL,
            "FIELD_LENGTH": 20,
            "FIELD_PRECISION": 3,
            "FORMULA": f"$length / ({default_speed_kmh} * 1000 / 3600)",
            "OUTPUT": output,
        },
        context,
        feedback,
    )

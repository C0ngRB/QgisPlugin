from core.qgis_processing.runner import run_processing_algorithm


FIELD_TYPE_DECIMAL = 0
FIELD_TYPE_STRING = 2
TEMPORARY_OUTPUT = "TEMPORARY_OUTPUT"
SAMPLED_DEM_FIELD = "sampled_dem_1"


def compare_dem_with_elevation_points(points_layer, measured_field, dem_layer, output, context, feedback):
    """函数含义：把高程点实测字段与 DEM 采样值对比；上游由 compare_dem_with_elevation_points Processing 算法传入点图层、实测字段和 DEM；下游输出带误差字段的点图层；风险点是 DEM 采样字段名由 QGIS rastersampling 的波段后缀决定。"""
    sampled_result = run_processing_algorithm(
        "native:rastersampling",
        {
            "INPUT": points_layer,
            "RASTERCOPY": dem_layer,
            "COLUMN_PREFIX": "sampled_dem_",
            "OUTPUT": TEMPORARY_OUTPUT,
        },
        context,
        feedback,
    )
    measured_result = _add_decimal_field(sampled_result["OUTPUT"], "measured_elev_m", f'"{measured_field}"', TEMPORARY_OUTPUT, context, feedback)
    dem_result = _add_decimal_field(measured_result["OUTPUT"], "dem_elev_m", f'"{SAMPLED_DEM_FIELD}"', TEMPORARY_OUTPUT, context, feedback)
    diff_result = _add_decimal_field(dem_result["OUTPUT"], "elev_diff_m", '"dem_elev_m" - "measured_elev_m"', TEMPORARY_OUTPUT, context, feedback)
    abs_result = _add_decimal_field(diff_result["OUTPUT"], "abs_diff_m", 'abs("elev_diff_m")', TEMPORARY_OUTPUT, context, feedback)
    return run_processing_algorithm(
        "native:fieldcalculator",
        {
            "INPUT": abs_result["OUTPUT"],
            "FIELD_NAME": "source_method",
            "FIELD_TYPE": FIELD_TYPE_STRING,
            "FIELD_LENGTH": 80,
            "FIELD_PRECISION": 0,
            "FORMULA": f"'field:{measured_field}'",
            "OUTPUT": output,
        },
        context,
        feedback,
    )


def _add_decimal_field(input_layer, field_name, formula, output, context, feedback):
    """函数含义：追加一个 decimal 计算字段；上游由 DEM 高程对比流程逐步补齐标准字段；下游调用 native:fieldcalculator 返回中间或最终图层；风险点是公式中的字段名必须已存在于输入图层。"""
    return run_processing_algorithm(
        "native:fieldcalculator",
        {
            "INPUT": input_layer,
            "FIELD_NAME": field_name,
            "FIELD_TYPE": FIELD_TYPE_DECIMAL,
            "FIELD_LENGTH": 20,
            "FIELD_PRECISION": 3,
            "FORMULA": formula,
            "OUTPUT": output,
        },
        context,
        feedback,
    )
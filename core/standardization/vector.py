from core.qgis_processing.runner import run_processing_algorithm


FIELD_TYPE_DECIMAL = 0
FIELD_TYPE_INTEGER = 1
FIELD_TYPE_STRING = 2
TEMPORARY_OUTPUT = "TEMPORARY_OUTPUT"


def reproject_to_analysis_crs(input_layer, target_crs, output, context, feedback):
    """函数含义：把输入矢量图层转换到分析 CRS；上游由 reproject_to_analysis_crs Processing 算法传入图层和目标 CRS；下游调用 native:reprojectlayer 输出标准化前置图层；风险点是原始 CRS 缺失时 QGIS 会失败或输出错误位置。"""
    return run_processing_algorithm("native:reprojectlayer", {"INPUT": input_layer, "TARGET_CRS": target_crs, "CONVERT_CURVED_GEOMETRIES": False, "OUTPUT": output}, context, feedback)


def standardize_buildings(input_layer, output, context, feedback):
    """函数含义：生成带基础标准字段的建筑图层；上游由 standardize_buildings Processing 算法传入建筑面；下游修复几何并追加 id、source_id、population_weight、geometry_status 和 representative_point_source；风险点是首版不推断楼层、高度和屋顶高程。"""
    fixed = run_processing_algorithm("native:fixgeometries", {"INPUT": input_layer, "METHOD": 1, "OUTPUT": TEMPORARY_OUTPUT}, context, feedback)["OUTPUT"]
    with_id = _add_integer_field(fixed, "id", "$id", TEMPORARY_OUTPUT, context, feedback)
    with_source = _add_integer_field(with_id["OUTPUT"], "source_id", "$id", TEMPORARY_OUTPUT, context, feedback)
    with_weight = _add_decimal_field(with_source["OUTPUT"], "population_weight", "1.0", TEMPORARY_OUTPUT, context, feedback)
    with_status = _add_string_field(with_weight["OUTPUT"], "geometry_status", "fixed", TEMPORARY_OUTPUT, context, feedback)
    return _add_string_field(with_status["OUTPUT"], "representative_point_source", "point_on_surface", output, context, feedback)


def standardize_roads(input_layer, default_speed_kmh, output, context, feedback):
    """函数含义：生成带基础标准字段的道路线图层；上游由 standardize_roads Processing 算法传入原始道路；下游调用 QGIS native 工具修复几何并追加 length/access/walkable/status 字段；风险点是首版不做交叉打断和端点吸附。"""
    fixed = run_processing_algorithm("native:fixgeometries", {"INPUT": input_layer, "METHOD": 1, "OUTPUT": TEMPORARY_OUTPUT}, context, feedback)["OUTPUT"]
    with_id = _add_integer_field(fixed, "id", "$id", TEMPORARY_OUTPUT, context, feedback)
    with_source = _add_integer_field(with_id["OUTPUT"], "source_id", "$id", TEMPORARY_OUTPUT, context, feedback)
    with_length = _add_decimal_field(with_source["OUTPUT"], "length_m", "$length", TEMPORARY_OUTPUT, context, feedback)
    with_cost = _add_decimal_field(with_length["OUTPUT"], "access_cost", f"$length / ({default_speed_kmh} * 1000 / 3600)", TEMPORARY_OUTPUT, context, feedback)
    with_walkable = _add_integer_field(with_cost["OUTPUT"], "walkable", "1", TEMPORARY_OUTPUT, context, feedback)
    return _add_string_field(with_walkable["OUTPUT"], "geometry_status", "fixed", output, context, feedback)


def standardize_pois(input_layer, service_type_field, output, context, feedback):
    """函数含义：生成带基础标准字段的 POI 图层；上游由 standardize_pois Processing 算法传入点图层和服务类型字段；下游追加 service_type、capacity、weight、geometry_status 等字段；风险点是未知服务类型暂按原字段值保留，不做中文枚举映射。"""
    with_id = _add_integer_field(input_layer, "id", "$id", TEMPORARY_OUTPUT, context, feedback)
    with_source = _add_integer_field(with_id["OUTPUT"], "source_id", "$id", TEMPORARY_OUTPUT, context, feedback)
    with_type = _add_string_formula_field(with_source["OUTPUT"], "service_type", f'attribute(@feature, \'{service_type_field}\')', TEMPORARY_OUTPUT, context, feedback)
    with_capacity = _add_integer_field(with_type["OUTPUT"], "capacity", "50", TEMPORARY_OUTPUT, context, feedback)
    with_weight = _add_decimal_field(with_capacity["OUTPUT"], "weight", "1.0", TEMPORARY_OUTPUT, context, feedback)
    return _add_string_field(with_weight["OUTPUT"], "geometry_status", "valid", output, context, feedback)


def standardize_elevation_points(input_layer, measured_field, output, context, feedback):
    """函数含义：生成带基础标准字段的高程点图层；上游由 standardize_elevation_points Processing 算法传入点图层和实测高程字段；下游追加 measured_elev_m、source_method 和 geometry_status；风险点是 DEM 采样对比仍由 terrain 算法负责。"""
    with_id = _add_integer_field(input_layer, "id", "$id", TEMPORARY_OUTPUT, context, feedback)
    with_source = _add_integer_field(with_id["OUTPUT"], "source_id", "$id", TEMPORARY_OUTPUT, context, feedback)
    with_elev = _add_decimal_field(with_source["OUTPUT"], "measured_elev_m", f'attribute(@feature, \'{measured_field}\')', TEMPORARY_OUTPUT, context, feedback)
    with_method = _add_string_field(with_elev["OUTPUT"], "source_method", f"field:{measured_field}", TEMPORARY_OUTPUT, context, feedback)
    return _add_string_field(with_method["OUTPUT"], "geometry_status", "valid", output, context, feedback)


def standardize_tracks(input_layer, output, context, feedback):
    """函数含义：生成带基础标准字段的轨迹线图层；上游由 standardize_tracks Processing 算法传入线图层；下游追加 length_m、source_method 和 geometry_status；风险点是首版不计算累计爬升和最高最低高程。"""
    fixed = run_processing_algorithm("native:fixgeometries", {"INPUT": input_layer, "METHOD": 1, "OUTPUT": TEMPORARY_OUTPUT}, context, feedback)["OUTPUT"]
    with_id = _add_integer_field(fixed, "id", "$id", TEMPORARY_OUTPUT, context, feedback)
    with_source = _add_integer_field(with_id["OUTPUT"], "source_id", "$id", TEMPORARY_OUTPUT, context, feedback)
    with_length = _add_decimal_field(with_source["OUTPUT"], "length_m", "$length", TEMPORARY_OUTPUT, context, feedback)
    with_method = _add_string_field(with_length["OUTPUT"], "source_method", "line_geometry", TEMPORARY_OUTPUT, context, feedback)
    return _add_string_field(with_method["OUTPUT"], "geometry_status", "fixed", output, context, feedback)


def _add_decimal_field(input_layer, field_name, formula, output, context, feedback):
    """函数含义：追加 decimal 标准字段；上游由标准化流程按字段顺序调用；下游调用 QGIS 字段计算器；风险点是公式依赖输入图层的几何和字段。"""
    return run_processing_algorithm("native:fieldcalculator", {"INPUT": input_layer, "FIELD_NAME": field_name, "FIELD_TYPE": FIELD_TYPE_DECIMAL, "FIELD_LENGTH": 20, "FIELD_PRECISION": 3, "FORMULA": formula, "OUTPUT": output}, context, feedback)


def _add_integer_field(input_layer, field_name, formula, output, context, feedback):
    """函数含义：追加 integer 标准字段；上游由标准化流程按字段顺序调用；下游调用 QGIS 字段计算器；风险点是公式结果必须可转为整数。"""
    return run_processing_algorithm("native:fieldcalculator", {"INPUT": input_layer, "FIELD_NAME": field_name, "FIELD_TYPE": FIELD_TYPE_INTEGER, "FIELD_LENGTH": 10, "FIELD_PRECISION": 0, "FORMULA": formula, "OUTPUT": output}, context, feedback)


def _add_string_field(input_layer, field_name, value, output, context, feedback):
    """函数含义：追加固定字符串标准字段；上游由标准化流程标记处理状态时调用；下游调用 QGIS 字段计算器；风险点是 value 中的单引号需要替换。"""
    safe_value = str(value).replace("'", " ")
    return _add_string_formula_field(input_layer, field_name, f"'{safe_value}'", output, context, feedback)


def _add_string_formula_field(input_layer, field_name, formula, output, context, feedback):
    """函数含义：追加字符串表达式字段；上游由标准化流程计算映射字段时调用；下游调用 QGIS 字段计算器；风险点是公式必须返回字符串。"""
    return run_processing_algorithm("native:fieldcalculator", {"INPUT": input_layer, "FIELD_NAME": field_name, "FIELD_TYPE": FIELD_TYPE_STRING, "FIELD_LENGTH": 120, "FIELD_PRECISION": 0, "FORMULA": formula, "OUTPUT": output}, context, feedback)
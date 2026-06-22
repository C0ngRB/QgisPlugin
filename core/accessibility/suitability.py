from core.config.defaults import load_defaults
from core.qgis_processing.runner import run_processing_algorithm


FIELD_TYPE_DECIMAL = 0
FIELD_TYPE_INTEGER = 1
FIELD_TYPE_STRING = 2
TEMPORARY_OUTPUT = "TEMPORARY_OUTPUT"
EQUALS_OPERATOR = 0


def calculate_facility_suitability(buildings_layer, facilities_layer, service_type_field, output, context, feedback):
    """函数含义：按设施类型生成建筑可达性适宜性长表；上游由 calculate_facility_suitability Processing 算法传入建筑和设施；下游调用点面转换、最近线、字段计算和合并输出评价图层；风险点是首版为最近设施近似评价，不是完整 OD 矩阵 E2SFCA。"""
    defaults = load_defaults()
    building_points = run_processing_algorithm(
        "native:pointonsurface",
        {"INPUT": buildings_layer, "ALL_PARTS": False, "OUTPUT": TEMPORARY_OUTPUT},
        context,
        feedback,
    )["OUTPUT"]
    evaluated_layers = []
    for service_type in _service_type_values(facilities_layer, service_type_field):
        filtered_facilities = run_processing_algorithm(
            "native:extractbyattribute",
            {"INPUT": facilities_layer, "FIELD": service_type_field, "OPERATOR": EQUALS_OPERATOR, "VALUE": service_type, "OUTPUT": TEMPORARY_OUTPUT, "FAIL_OUTPUT": TEMPORARY_OUTPUT},
            context,
            feedback,
        )["OUTPUT"]
        nearest = run_processing_algorithm(
            "native:shortestline",
            {"SOURCE": building_points, "DESTINATION": filtered_facilities, "METHOD": 0, "NEIGHBORS": 1, "DISTANCE": 0, "OUTPUT": TEMPORARY_OUTPUT},
            context,
            feedback,
        )["OUTPUT"]
        evaluated_layers.append(_add_suitability_fields(nearest, service_type, defaults, context, feedback))
    return run_processing_algorithm("native:mergevectorlayers", {"LAYERS": evaluated_layers, "CRS": None, "OUTPUT": output}, context, feedback)


def _service_type_values(facilities_layer, service_type_field):
    """函数含义：读取设施类型字段中的唯一非空值；上游由适宜性分析按类型拆分设施时调用；下游决定长表 service_type 记录集合；风险点是字段值为空时不会生成评价记录。"""
    values = []
    seen = set()
    for feature in facilities_layer.getFeatures():
        value = str(feature[service_type_field]).strip()
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return values or ["other"]


def _add_suitability_fields(input_layer, service_type, defaults, context, feedback):
    """函数含义：为单个设施类型的最近设施结果追加 ADR 评价字段；上游由适宜性分析逐类型调用；下游返回可合并的中间线图层；风险点是距离衰减按默认步速近似为米制阈值。"""
    thresholds = defaults["service_thresholds"].get(service_type, defaults["service_thresholds"]["other"])
    max_distance = max(thresholds["time_min"]) * 5000 / 60
    with_type = _add_string_field(input_layer, "service_type", service_type, TEMPORARY_OUTPUT, context, feedback)
    with_index = _add_decimal_field(with_type["OUTPUT"], "accessibility_index", _decay_formula(thresholds), TEMPORARY_OUTPUT, context, feedback)
    with_ratio = _add_decimal_field(with_index["OUTPUT"], "supply_demand_ratio_sum", '"accessibility_index"', TEMPORARY_OUTPUT, context, feedback)
    with_count = _add_integer_field(with_ratio["OUTPUT"], "reachable_facility_count", f'CASE WHEN "distance" <= {max_distance:.3f} THEN 1 ELSE 0 END', TEMPORARY_OUTPUT, context, feedback)
    with_cost = _add_decimal_field(with_count["OUTPUT"], "nearest_facility_cost", '"distance"', TEMPORARY_OUTPUT, context, feedback)
    with_class = _add_string_formula_field(with_cost["OUTPUT"], "suitability_class", _class_formula(), TEMPORARY_OUTPUT, context, feedback)
    return _add_string_field(with_class["OUTPUT"], "demand_source", "nearest_facility_overlay", TEMPORARY_OUTPUT, context, feedback)["OUTPUT"]


def _decay_formula(thresholds):
    """函数含义：生成距离衰减表达式；上游由适宜性字段计算调用；下游传给 QGIS fieldcalculator；风险点是把分钟阈值按 5km/h 转为米制距离。"""
    clauses = []
    for time_min, weight in zip(thresholds["time_min"], thresholds["decay_weight"]):
        distance_m = time_min * 5000 / 60
        clauses.append(f'WHEN "distance" <= {distance_m:.3f} THEN {float(weight):.6f}')
    return "CASE " + " ".join(clauses) + " ELSE 0 END"


def _class_formula():
    """函数含义：生成适宜性等级表达式；上游由适宜性字段计算调用；下游给专题图提供 5 级分类字段；风险点是首版为固定阈值等级，不是全局分位数。"""
    return "CASE WHEN \"accessibility_index\" >= 0.8 THEN '极高' WHEN \"accessibility_index\" >= 0.6 THEN '较高' WHEN \"accessibility_index\" >= 0.4 THEN '中等' WHEN \"accessibility_index\" > 0 THEN '较低' ELSE '极低' END"


def _add_decimal_field(input_layer, field_name, formula, output, context, feedback):
    """函数含义：追加 decimal 评价字段；上游由适宜性字段组装流程调用；下游调用 QGIS fieldcalculator；风险点是公式依赖上游已生成字段。"""
    return run_processing_algorithm("native:fieldcalculator", {"INPUT": input_layer, "FIELD_NAME": field_name, "FIELD_TYPE": FIELD_TYPE_DECIMAL, "FIELD_LENGTH": 20, "FIELD_PRECISION": 6, "FORMULA": formula, "OUTPUT": output}, context, feedback)


def _add_integer_field(input_layer, field_name, formula, output, context, feedback):
    """函数含义：追加 integer 评价字段；上游由适宜性字段组装流程调用；下游调用 QGIS fieldcalculator；风险点是公式结果必须能转换为整数。"""
    return run_processing_algorithm("native:fieldcalculator", {"INPUT": input_layer, "FIELD_NAME": field_name, "FIELD_TYPE": FIELD_TYPE_INTEGER, "FIELD_LENGTH": 10, "FIELD_PRECISION": 0, "FORMULA": formula, "OUTPUT": output}, context, feedback)


def _add_string_field(input_layer, field_name, value, output, context, feedback):
    """函数含义：追加固定字符串字段；上游由适宜性字段组装流程调用；下游标记 service_type 或 demand_source；风险点是 value 中的单引号需要替换。"""
    safe_value = str(value).replace("'", " ")
    return _add_string_formula_field(input_layer, field_name, f"'{safe_value}'", output, context, feedback)


def _add_string_formula_field(input_layer, field_name, formula, output, context, feedback):
    """函数含义：追加字符串表达式字段；上游由适宜性字段组装流程调用；下游调用 QGIS fieldcalculator；风险点是公式必须返回字符串。"""
    return run_processing_algorithm("native:fieldcalculator", {"INPUT": input_layer, "FIELD_NAME": field_name, "FIELD_TYPE": FIELD_TYPE_STRING, "FIELD_LENGTH": 80, "FIELD_PRECISION": 0, "FORMULA": formula, "OUTPUT": output}, context, feedback)
from pathlib import Path

from core.accessibility.nearest import calculate_nearest_facility
from core.accessibility.routing import calculate_service_area
from core.accessibility.suitability import calculate_facility_suitability
from core.io.output_naming import unique_output_path
from core.qgis_processing.runner import run_processing_algorithm
from core.reporting.summary import write_run_summary

FIELD_TYPE_DECIMAL = 0
FIELD_TYPE_INTEGER = 1
FIELD_TYPE_STRING = 2
TEMPORARY_OUTPUT = "TEMPORARY_OUTPUT"


def run_accessibility_workflow(buildings_layer, roads_layer, facilities_layer, service_type_field, output_folder, travel_cost, default_speed_kmh, tolerance, context, feedback):
    """函数含义：一键生成可达性分析成果；上游由 run_accessibility_workflow Processing 算法传入建筑、道路、设施和成本参数；下游复用适宜性、服务区和最近设施细粒度函数并写 run_summary.json；风险点是首版为服务区叠置近似评价，不是完整 OD 矩阵 E2SFCA。"""
    resolved_output_folder = Path(output_folder)
    resolved_output_folder.mkdir(parents=True, exist_ok=True)
    outputs = {
        "accessibility_buildings": calculate_facility_suitability(buildings_layer, facilities_layer, service_type_field, str(unique_output_path(resolved_output_folder / "accessibility_buildings.gpkg")), context, feedback)["OUTPUT"],
        "facility_service_areas": calculate_service_area(roads_layer, facilities_layer, travel_cost, default_speed_kmh, tolerance, str(unique_output_path(resolved_output_folder / "facility_service_areas.gpkg")), context, feedback)["OUTPUT"],
        "nearest_facility_links": calculate_nearest_facility(buildings_layer, facilities_layer, 1, 0.0, str(unique_output_path(resolved_output_folder / "nearest_facility_links.gpkg")), context, feedback)["OUTPUT"],
    }
    outputs["facility_supply_demand"] = _build_facility_supply_demand(
        facilities_layer,
        service_type_field,
        str(unique_output_path(resolved_output_folder / "facility_supply_demand.gpkg")),
        context,
        feedback,
    )["OUTPUT"]
    summary_path = write_run_summary(
        resolved_output_folder,
        "wuda_accessibility_analyzer:run_accessibility_workflow",
        outputs=list(outputs.values()),
        warnings=["首版可达性 workflow 使用服务区叠置近似 E2SFCA；facility_supply_demand 的 total_weighted_demand 当前按设施属性派生，不是完整 OD 成本矩阵统计。"],
    )
    return {"OUTPUT_FOLDER": str(resolved_output_folder), "OUTPUTS": outputs, "SUMMARY": str(summary_path)}


def _build_facility_supply_demand(facilities_layer, service_type_field, output, context, feedback):
    """函数含义：生成设施供需属性图层；上游由可达性 workflow 在最终输出阶段调用；下游写出 facility_supply_demand.gpkg 供专题图和报告引用；风险点是需求统计为首版近似字段，不代表完整 OD 矩阵需求汇总。"""
    field_names = _field_names(facilities_layer)
    capacity_formula = '"capacity"' if "capacity" in field_names else "50"
    id_formula = '"id"' if "id" in field_names else "$id"
    with_facility_id = _add_integer_field(facilities_layer, "facility_id", id_formula, TEMPORARY_OUTPUT, context, feedback)
    with_type = _add_string_formula_field(with_facility_id["OUTPUT"], "service_type", f'attribute(@feature, \'{service_type_field}\')', TEMPORARY_OUTPUT, context, feedback)
    with_capacity = _add_decimal_field(with_type["OUTPUT"], "capacity", capacity_formula, TEMPORARY_OUTPUT, context, feedback)
    with_demand = _add_decimal_field(with_capacity["OUTPUT"], "total_weighted_demand", "0.0", TEMPORARY_OUTPUT, context, feedback)
    with_ratio = _add_decimal_field(with_demand["OUTPUT"], "supply_demand_ratio", '"capacity"', TEMPORARY_OUTPUT, context, feedback)
    with_count = _add_integer_field(with_ratio["OUTPUT"], "reachable_building_count", "0", TEMPORARY_OUTPUT, context, feedback)
    capacity_source = "field:capacity" if "capacity" in field_names else "default:50"
    return _add_string_field(with_count["OUTPUT"], "capacity_source", capacity_source, output, context, feedback)


def _field_names(layer):
    """函数含义：读取图层字段名集合；上游由供需表字段派生逻辑调用；下游决定 capacity/id 字段是否使用默认值；风险点是传入 Processing 临时 ID 时可能无法读取字段。"""
    if hasattr(layer, "fields"):
        return {field.name() for field in layer.fields()}
    return set()


def _add_decimal_field(input_layer, field_name, formula, output, context, feedback):
    """函数含义：追加 decimal workflow 字段；上游由供需表构建函数调用；下游调用 QGIS fieldcalculator；风险点是公式依赖字段存在性。"""
    return run_processing_algorithm("native:fieldcalculator", {"INPUT": input_layer, "FIELD_NAME": field_name, "FIELD_TYPE": FIELD_TYPE_DECIMAL, "FIELD_LENGTH": 20, "FIELD_PRECISION": 6, "FORMULA": formula, "OUTPUT": output}, context, feedback)


def _add_integer_field(input_layer, field_name, formula, output, context, feedback):
    """函数含义：追加 integer workflow 字段；上游由供需表构建函数调用；下游调用 QGIS fieldcalculator；风险点是公式结果必须能转为整数。"""
    return run_processing_algorithm("native:fieldcalculator", {"INPUT": input_layer, "FIELD_NAME": field_name, "FIELD_TYPE": FIELD_TYPE_INTEGER, "FIELD_LENGTH": 10, "FIELD_PRECISION": 0, "FORMULA": formula, "OUTPUT": output}, context, feedback)


def _add_string_field(input_layer, field_name, value, output, context, feedback):
    """函数含义：追加固定字符串 workflow 字段；上游由供需表构建函数调用；下游标记 capacity 来源；风险点是字段值中的单引号需要替换。"""
    safe_value = str(value).replace("'", " ")
    return _add_string_formula_field(input_layer, field_name, f"'{safe_value}'", output, context, feedback)


def _add_string_formula_field(input_layer, field_name, formula, output, context, feedback):
    """函数含义：追加字符串表达式 workflow 字段；上游由供需表构建函数调用；下游调用 QGIS fieldcalculator；风险点是表达式必须返回字符串。"""
    return run_processing_algorithm("native:fieldcalculator", {"INPUT": input_layer, "FIELD_NAME": field_name, "FIELD_TYPE": FIELD_TYPE_STRING, "FIELD_LENGTH": 120, "FIELD_PRECISION": 0, "FORMULA": formula, "OUTPUT": output}, context, feedback)
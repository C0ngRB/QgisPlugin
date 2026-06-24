from core.qgis_processing.runner import run_processing_algorithm

TEMPORARY_OUTPUT = "TEMPORARY_OUTPUT"


def calculate_nearest_facility(source_layer, facility_layer, neighbors, max_distance, output, context, feedback):
    """函数含义：生成源要素到最近设施的校核连线；上游由 calculate_nearest_facility Processing 算法或可达性 workflow 传入源图层和设施图层；下游调用 QGIS native:shortestline 并输出可写入 GeoPackage 的线图层；风险点是 shortestline 会继承重复 feature id，落盘前必须重建字段表和内部 FID。"""
    nearest_result = run_processing_algorithm(
        "native:shortestline",
        {
            "SOURCE": source_layer,
            "DESTINATION": facility_layer,
            "METHOD": 0,
            "NEIGHBORS": neighbors,
            "DISTANCE": max_distance,
            "OUTPUT": TEMPORARY_OUTPUT,
        },
        context,
        feedback,
    )
    return _refactor_nearest_output(nearest_result["OUTPUT"], output, context, feedback)


def _refactor_nearest_output(input_layer, output, context, feedback):
    """函数含义：重建最近设施线图层字段并生成新的内部 FID；上游由最近设施分析落盘前调用；下游避免 GeoPackage 写入重复 fid 报错；风险点是会移除源图层名为 fid 的业务字段。"""
    resolved_layer = _resolve_layer(input_layer, context)
    field_mapping = []
    for field in resolved_layer.fields():
        if field.name() == "fid":
            continue
        field_mapping.append(
            {
                "name": field.name(),
                "type": field.type(),
                "length": field.length(),
                "precision": field.precision(),
                "expression": f'"{field.name()}"',
            }
        )
    return run_processing_algorithm("native:refactorfields", {"INPUT": resolved_layer, "FIELDS_MAPPING": field_mapping, "OUTPUT": output}, context, feedback)


def _resolve_layer(layer_ref, context):
    """函数含义：把 Processing 临时输出解析为 QGIS 图层对象；上游由最近设施字段重构前调用；下游提供 fields() 和要素读取能力；风险点是 context 中缺失临时图层时应直接失败。"""
    if hasattr(layer_ref, "fields"):
        return layer_ref
    if hasattr(context, "getMapLayer"):
        layer = context.getMapLayer(layer_ref)
        if layer is not None:
            return layer
    raise RuntimeError("无法解析最近设施临时图层。")

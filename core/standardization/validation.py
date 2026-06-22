import json
from datetime import datetime, timezone
from pathlib import Path

from core.io.output_naming import unique_output_path


def validate_input_layer(input_layer, output_folder):
    """函数含义：校验单个输入图层并写入 JSON 摘要；上游由 validate_input_layers Processing 算法传入 QGIS 图层；下游生成 validation_report.json 供标准化流程追踪；风险点是当前增量只校验图层可用性、CRS 和要素数。"""
    target_dir = Path(output_folder)
    target_dir.mkdir(parents=True, exist_ok=True)
    report_path = unique_output_path(target_dir / "validation_report.json")
    crs = input_layer.sourceCrs()
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "layer_name": input_layer.sourceName(),
        "is_valid": input_layer.isValid(),
        "feature_count": input_layer.featureCount(),
        "crs_authid": crs.authid() if crs.isValid() else "",
        "geometry_type": int(input_layer.wkbType()),
        "fields": [field.name() for field in input_layer.fields()],
        "errors": [] if input_layer.isValid() and crs.isValid() else ["图层无效或 CRS 无效。"],
    }
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    return report_path
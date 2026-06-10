import json
from datetime import datetime, timezone
from pathlib import Path

from core.io.output_naming import unique_output_path


def write_run_summary(output_dir, algorithm_id, outputs, mode="real", warnings=None):
    """函数含义：写入单次算法运行摘要；上游由核心业务流程或插件 Algorithm 调用；下游生成 run_summary.json 并返回路径；风险点是输出目录不可写会直接失败。"""
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = unique_output_path(resolved_output_dir / "run_summary.json")
    summary = {
        "algorithm_id": algorithm_id,
        "mode": mode,
        "is_demo_result": mode == "demo",
        "outputs": [str(output) for output in outputs],
        "warnings": warnings or [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with summary_path.open("w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, ensure_ascii=False, indent=2)
    return summary_path

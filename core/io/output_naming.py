from pathlib import Path


def unique_output_path(target_path, suffix_width=3):
    """函数含义：生成不覆盖已有文件的输出路径；上游由算法和 summary 写入流程调用；下游返回可安全写入的新路径；风险点是并发运行时仍可能在返回后被外部进程占用。"""
    path = Path(target_path)
    if not path.exists():
        return path

    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{index:0{suffix_width}d}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1

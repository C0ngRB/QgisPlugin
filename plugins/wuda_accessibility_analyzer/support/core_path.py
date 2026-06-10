import sys
from pathlib import Path


def ensure_core_import_path(current_file):
    """函数含义：把源码态或发布态 core 加入导入路径；上游由插件 Provider、UI 和算法模块调用；下游允许导入共享 core；风险点是路径顺序必须优先当前插件包内复制的 core。"""
    plugin_dir = Path(current_file).resolve().parent
    while plugin_dir.name != "wuda_accessibility_analyzer":
        plugin_dir = plugin_dir.parent

    candidates = (plugin_dir, plugin_dir.parent.parent)
    for candidate in candidates:
        if (candidate / "core").exists():
            resolved = str(candidate)
            if resolved not in sys.path:
                sys.path.insert(0, resolved)

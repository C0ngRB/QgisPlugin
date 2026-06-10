import json
from pathlib import Path


def load_defaults(config_path=None):
    """函数含义：读取默认参数配置；上游由 core 算法和测试调用；下游返回服务阈值、默认容量和命名规则；风险点是配置文件缺失或 JSON 格式错误会中止运行。"""
    resolved_path = Path(config_path) if config_path else Path(__file__).with_name("defaults.json")
    with resolved_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)

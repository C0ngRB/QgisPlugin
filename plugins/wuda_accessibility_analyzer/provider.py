from qgis.core import QgsProcessingProvider

from .algorithms.registered_algorithm import RegisteredAccessibilityAlgorithm
from .support.core_path import ensure_core_import_path

ensure_core_import_path(__file__)

from core.registry.algorithms import ACCESSIBILITY_PROVIDER_ID, provider_algorithms


class WudaAccessibilityProvider(QgsProcessingProvider):
    """类含义：可达性插件 Processing Provider；上游由插件生命周期注册；下游向 QGIS 工具箱暴露标准化和可达性算法；风险点是算法 ID 必须与 core 注册表一致。"""

    def id(self):
        """函数含义：返回 Provider 内部 ID；上游由 QGIS Processing 注册表调用；下游组成完整算法 ID；风险点是修改会破坏模型历史引用。"""
        return ACCESSIBILITY_PROVIDER_ID

    def name(self):
        """函数含义：返回 Provider 显示名；上游由 QGIS Processing UI 调用；下游展示工具箱分类；风险点是只影响显示不影响算法 ID。"""
        return "WUDA 可达性分析"

    def longName(self):
        """函数含义：返回 Provider 完整显示名；上游由 QGIS Processing UI 调用；下游展示工具箱标题；风险点是名称过长会影响可读性。"""
        return self.name()

    def loadAlgorithms(self):
        """函数含义：按 core 注册表注册算法；上游由 QGIS Processing 初始化 Provider 时调用；下游生成工具箱算法列表；风险点是注册表缺项会导致算法不可见。"""
        for algorithm_name in provider_algorithms(ACCESSIBILITY_PROVIDER_ID):
            self.addAlgorithm(RegisteredAccessibilityAlgorithm(algorithm_name))

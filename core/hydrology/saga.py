def saga_provider_available():
    """函数含义：检测 QGIS SAGA Provider 是否可用；上游由水文算法和手工验收调用；下游决定真实水文或 demo 模式；风险点是只能在 QGIS Python 环境中调用。"""
    from qgis.core import QgsApplication

    return QgsApplication.processingRegistry().providerById("saga") is not None

def classFactory(iface):
    """函数含义：创建地形水文插件实例；上游由 QGIS 插件加载器调用；下游返回插件生命周期对象；风险点是 iface 只能在 QGIS Desktop 中提供。"""
    from .plugin import WudaTerrainHydroAnalyzerPlugin

    return WudaTerrainHydroAnalyzerPlugin(iface)

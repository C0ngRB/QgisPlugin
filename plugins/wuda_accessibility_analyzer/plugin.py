from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication

from .provider import WudaAccessibilityProvider
from .ui.panel import WudaAccessibilityPanel


class WudaAccessibilityAnalyzerPlugin:
    """类含义：可达性插件生命周期控制器；上游由 QGIS 插件加载器创建；下游注册菜单和 Processing Provider；风险点是卸载时必须清理全局注册状态。"""

    def __init__(self, iface):
        """函数含义：保存 QGIS iface 并初始化插件对象；上游由 classFactory 传入 iface；下游供 initGui 注册 UI 和 Provider；风险点是此处不应执行耗时分析。"""
        self.iface = iface
        self.action = None
        self.panel = None
        self.provider = WudaAccessibilityProvider()

    def initGui(self):
        """函数含义：注册插件菜单和 Processing Provider；上游由 QGIS 启用插件时调用；下游让用户能打开向导和算法窗口；风险点是重复调用会造成菜单重复。"""
        self.action = QAction("WUDA 可达性分析", self.iface.mainWindow())
        self.action.triggered.connect(self.open_panel)
        self.iface.addPluginToMenu("WUDA 可达性分析", self.action)
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        """函数含义：卸载插件菜单和 Provider；上游由 QGIS 禁用插件时调用；下游清理插件对 QGIS 的注册影响；风险点是空对象需要跳过。"""
        if self.action is not None:
            self.iface.removePluginMenu("WUDA 可达性分析", self.action)
            self.action = None
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def open_panel(self):
        """函数含义：打开可达性分析向导面板；上游由菜单动作触发；下游让用户进入 Processing 原生算法窗口；风险点是面板不直接执行分析。"""
        if self.panel is None:
            self.panel = WudaAccessibilityPanel(self.iface)
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()

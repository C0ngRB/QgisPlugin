from qgis.PyQt.QtWidgets import QCheckBox, QDialog, QLabel, QPushButton, QVBoxLayout

from ..support.core_path import ensure_core_import_path

ensure_core_import_path(__file__)

from core.registry.algorithms import TERRAIN_HYDRO_PROVIDER_ID, algorithm_display_name, provider_algorithms


class WudaTerrainHydroPanel(QDialog):
    """类含义：地形水文插件向导入口；上游由插件菜单打开；下游调用 QGIS 原生 Processing 算法窗口；风险点是不能在 UI 中直接执行 processing.run。"""

    def __init__(self, iface):
        """函数含义：构建 workflow 和高级算法按钮；上游由 plugin.open_panel 传入 iface；下游按按钮打开算法窗口；风险点是算法 ID 必须来自 core 注册表。"""
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.setWindowTitle("WUDA 地形水文分析")
        self.setMinimumWidth(460)

        self.layout = QVBoxLayout()
        self.mode_checkbox = QCheckBox("高级模式")
        self.mode_checkbox.stateChanged.connect(self.render_buttons)
        self.layout.addWidget(QLabel("选择工作流入口，或切换高级模式打开细粒度算法。"))
        self.layout.addWidget(self.mode_checkbox)
        self.setLayout(self.layout)
        self.render_buttons()

    def render_buttons(self):
        """函数含义：根据当前模式渲染算法按钮；上游由初始化和高级模式开关触发；下游生成打开 Processing 窗口的按钮；风险点是重复渲染前必须清理旧按钮。"""
        while self.layout.count() > 2:
            item = self.layout.takeAt(2)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        workflow_names = ("run_standardization_workflow", "run_terrain_workflow", "run_hydrology_workflow")
        algorithm_names = provider_algorithms(TERRAIN_HYDRO_PROVIDER_ID) if self.mode_checkbox.isChecked() else workflow_names
        for algorithm_name in algorithm_names:
            button = QPushButton(algorithm_display_name(algorithm_name))
            button.clicked.connect(lambda checked=False, name=algorithm_name: self.open_processing_dialog(name))
            self.layout.addWidget(button)

    def open_processing_dialog(self, algorithm_name):
        """函数含义：打开 QGIS Processing 原生算法窗口；上游由算法按钮触发；下游交给 QGIS 参数面板执行；风险点是 iface 方法依赖 QGIS 版本。"""
        self.iface.openProcessingDialog(f"{TERRAIN_HYDRO_PROVIDER_ID}:{algorithm_name}")

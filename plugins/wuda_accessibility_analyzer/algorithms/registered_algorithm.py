from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterDistance,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFolderDestination,
)

from ..support.core_path import ensure_core_import_path

ensure_core_import_path(__file__)

from core.accessibility.facility_buffers import generate_facility_buffers
from core.registry.algorithms import ACCESSIBILITY_PROVIDER_ID, algorithm_display_name
from core.reporting.summary import write_run_summary


class RegisteredAccessibilityAlgorithm(QgsProcessingAlgorithm):
    """类含义：可达性插件通用薄 Algorithm；上游由 Provider 按注册表创建；下游把执行契约交给 core；风险点是当前阶段未实现的算法必须显式失败。"""

    OUTPUT_FOLDER = "OUTPUT_FOLDER"
    FACILITIES = "FACILITIES"
    DISTANCE = "DISTANCE"
    OUTPUT = "OUTPUT"
    IMPLEMENTED_ALGORITHMS = {
        "generate_facility_buffers",
        "run_standardization_workflow",
        "run_accessibility_workflow",
    }

    def __init__(self, algorithm_name):
        """函数含义：绑定单个注册算法名；上游由 Provider 遍历 core 注册表调用；下游让同一个薄类承载多个算法入口；风险点是 algorithm_name 必须来自注册表。"""
        super().__init__()
        self.algorithm_name = algorithm_name

    def name(self):
        """函数含义：返回算法内部名；上游由 QGIS Processing 注册表调用；下游组成完整算法 ID；风险点是必须保持 snake_case 稳定。"""
        return self.algorithm_name

    def displayName(self):
        """函数含义：返回算法中文显示名；上游由 QGIS Processing 工具箱调用；下游展示给用户；风险点是文案必须和注册表一致。"""
        return algorithm_display_name(self.algorithm_name)

    def group(self):
        """函数含义：返回算法分组名；上游由 QGIS Processing 工具箱调用；下游组织工具列表；风险点是分组过碎会降低可发现性。"""
        return "标准化与可达性"

    def groupId(self):
        """函数含义：返回算法分组 ID；上游由 QGIS Processing 注册表调用；下游稳定保存工具箱分组；风险点是改名会影响模型展示。"""
        return "standardization_accessibility"

    def shortHelpString(self):
        """函数含义：返回算法帮助文本；上游由 QGIS 参数面板展示；下游说明当前算法能力边界；风险点是不能承诺尚未实现的真实空间计算。"""
        if self.algorithm_name == "generate_facility_buffers":
            return "输入设施图层和服务距离，输出真实缓冲区面图层；距离单位取决于输入图层 CRS。"
        return "当前阶段提供插件注册、参数入口和运行摘要契约；真实空间分析按后续阶段在 core 中补齐。"

    def createInstance(self):
        """函数含义：创建同名算法新实例；上游由 QGIS Processing 克隆算法时调用；下游隔离每次执行状态；风险点是不能返回共享实例。"""
        return RegisteredAccessibilityAlgorithm(self.algorithm_name)

    def initAlgorithm(self, config=None):
        """函数含义：声明当前算法参数；上游由 QGIS Processing 打开参数面板时调用；下游生成用户输入表单；风险点是未实现算法仍只暴露摘要输出目录。"""
        if self.algorithm_name == "generate_facility_buffers":
            self.addParameter(
                QgsProcessingParameterFeatureSource(
                    self.FACILITIES,
                    "设施图层（点、线或面）",
                    [QgsProcessing.TypeVectorAnyGeometry],
                )
            )
            self.addParameter(
                QgsProcessingParameterDistance(
                    self.DISTANCE,
                    "服务距离",
                    defaultValue=300.0,
                    parentParameterName=self.FACILITIES,
                )
            )
            self.addParameter(
                QgsProcessingParameterFeatureSink(
                    self.OUTPUT,
                    "设施服务缓冲区",
                    QgsProcessing.TypeVectorPolygon,
                )
            )
            return

        self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_FOLDER, "输出目录"))

    def processAlgorithm(self, parameters, context, feedback):
        """函数含义：执行已实现的可达性算法入口；上游由 QGIS Processing 运行器调用；下游生成真实图层、摘要或显式拒绝未实现算法；风险点是不得生成假空间分析结果。"""
        if self.algorithm_name not in self.IMPLEMENTED_ALGORITHMS:
            raise QgsProcessingException(f"{self.displayName()} 尚未在当前阶段实现真实空间分析。")

        if self.algorithm_name == "generate_facility_buffers":
            distance = self.parameterAsDouble(parameters, self.DISTANCE, context)
            output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
            if distance <= 0:
                raise QgsProcessingException("服务距离必须大于 0。")
            result = generate_facility_buffers(
                parameters[self.FACILITIES],
                distance,
                output,
                context,
                feedback,
            )
            return {self.OUTPUT: result["OUTPUT"]}

        output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
        summary_path = write_run_summary(
            output_folder,
            f"{ACCESSIBILITY_PROVIDER_ID}:{self.algorithm_name}",
            outputs=[],
            warnings=["当前阶段仅验证插件工作流入口和摘要契约，未生成空间分析结果。"],
        )
        feedback.pushInfo(f"已写入运行摘要：{summary_path}")
        return {self.OUTPUT_FOLDER: output_folder}

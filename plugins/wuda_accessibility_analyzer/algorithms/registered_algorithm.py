from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterDistance,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
)

from ..support.core_path import ensure_core_import_path

ensure_core_import_path(__file__)

from core.accessibility.facility_buffers import generate_facility_buffers
from core.accessibility.nearest import calculate_nearest_facility
from core.accessibility.network import build_network_cost, calculate_road_length
from core.io.qgis_output import unique_qgis_output_path
from core.registry.algorithms import ACCESSIBILITY_PROVIDER_ID, algorithm_display_name
from core.reporting.summary import write_run_summary


class RegisteredAccessibilityAlgorithm(QgsProcessingAlgorithm):
    """类含义：可达性插件通用薄 Algorithm；上游由 Provider 按注册表创建；下游把执行契约交给 core；风险点是当前阶段未实现的算法必须显式失败。"""

    OUTPUT_FOLDER = "OUTPUT_FOLDER"
    FACILITIES = "FACILITIES"
    ROADS = "ROADS"
    SOURCE = "SOURCE"
    DISTANCE = "DISTANCE"
    NEIGHBORS = "NEIGHBORS"
    DEFAULT_SPEED = "DEFAULT_SPEED"
    OUTPUT = "OUTPUT"
    VECTOR_OUTPUT_ALGORITHMS = {
        "calculate_road_length",
        "build_network_cost",
        "generate_facility_buffers",
        "calculate_nearest_facility",
    }
    IMPLEMENTED_ALGORITHMS = VECTOR_OUTPUT_ALGORITHMS | {
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
        if self.algorithm_name == "calculate_road_length":
            return "输入道路线图层，输出带 length_m 字段的真实线图层；长度单位取决于输入 CRS。"
        if self.algorithm_name == "build_network_cost":
            return "输入道路线图层和默认速度，输出带 length_m 与 access_cost 字段的真实线图层。"
        if self.algorithm_name == "calculate_nearest_facility":
            return "输入源图层和设施图层，输出几何最近设施校核连线；该结果不是网络路径成本。"
        return "当前阶段提供插件注册、参数入口和运行摘要契约；真实空间分析按后续阶段在 core 中补齐。"

    def createInstance(self):
        """函数含义：创建同名算法新实例；上游由 QGIS Processing 克隆算法时调用；下游隔离每次执行状态；风险点是不能返回共享实例。"""
        return RegisteredAccessibilityAlgorithm(self.algorithm_name)

    def initAlgorithm(self, config=None):
        """函数含义：声明当前算法参数；上游由 QGIS Processing 打开参数面板时调用；下游生成用户输入表单；风险点是未实现算法仍只暴露摘要输出目录。"""
        if self.algorithm_name in {"calculate_road_length", "build_network_cost"}:
            self._add_roads_parameter()
            if self.algorithm_name == "build_network_cost":
                self.addParameter(
                    QgsProcessingParameterNumber(
                        self.DEFAULT_SPEED,
                        "默认步行速度（千米/时）",
                        type=QgsProcessingParameterNumber.Double,
                        defaultValue=5.0,
                        minValue=0.1,
                    )
                )
            self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.displayName(), QgsProcessing.TypeVectorLine))
            return

        if self.algorithm_name == "calculate_nearest_facility":
            self.addParameter(
                QgsProcessingParameterFeatureSource(
                    self.SOURCE,
                    "源图层（建筑或需求点）",
                    [QgsProcessing.TypeVectorAnyGeometry],
                )
            )
            self.addParameter(
                QgsProcessingParameterFeatureSource(
                    self.FACILITIES,
                    "设施图层",
                    [QgsProcessing.TypeVectorAnyGeometry],
                )
            )
            self.addParameter(
                QgsProcessingParameterNumber(
                    self.NEIGHBORS,
                    "最近设施数量",
                    type=QgsProcessingParameterNumber.Integer,
                    defaultValue=1,
                    minValue=1,
                )
            )
            self.addParameter(
                QgsProcessingParameterDistance(
                    self.DISTANCE,
                    "最大搜索距离（0 表示不限制）",
                    defaultValue=0.0,
                    parentParameterName=self.SOURCE,
                )
            )
            self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, "最近设施校核连线", QgsProcessing.TypeVectorLine))
            return

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
            self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, "设施服务缓冲区", QgsProcessing.TypeVectorPolygon))
            return

        self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_FOLDER, "输出目录"))

    def processAlgorithm(self, parameters, context, feedback):
        """函数含义：执行已实现的可达性算法入口；上游由 QGIS Processing 运行器调用；下游生成真实图层、摘要或显式拒绝未实现算法；风险点是不得生成假空间分析结果。"""
        if self.algorithm_name not in self.IMPLEMENTED_ALGORITHMS:
            raise QgsProcessingException(f"{self.displayName()} 尚未在当前阶段实现真实空间分析。")

        if self.algorithm_name == "calculate_road_length":
            result = calculate_road_length(parameters[self.ROADS], unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)), context, feedback)
            return {self.OUTPUT: result["OUTPUT"]}

        if self.algorithm_name == "build_network_cost":
            speed = self.parameterAsDouble(parameters, self.DEFAULT_SPEED, context)
            if speed <= 0:
                raise QgsProcessingException("默认步行速度必须大于 0。")
            result = build_network_cost(parameters[self.ROADS], speed, unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)), context, feedback)
            return {self.OUTPUT: result["OUTPUT"]}

        if self.algorithm_name == "calculate_nearest_facility":
            neighbors = self.parameterAsInt(parameters, self.NEIGHBORS, context)
            max_distance = self.parameterAsDouble(parameters, self.DISTANCE, context)
            if neighbors < 1:
                raise QgsProcessingException("最近设施数量必须至少为 1。")
            result = calculate_nearest_facility(
                parameters[self.SOURCE],
                parameters[self.FACILITIES],
                neighbors,
                max_distance,
                unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)),
                context,
                feedback,
            )
            return {self.OUTPUT: result["OUTPUT"]}

        if self.algorithm_name == "generate_facility_buffers":
            distance = self.parameterAsDouble(parameters, self.DISTANCE, context)
            if distance <= 0:
                raise QgsProcessingException("服务距离必须大于 0。")
            result = generate_facility_buffers(
                parameters[self.FACILITIES],
                distance,
                unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)),
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

    def _add_roads_parameter(self):
        """函数含义：追加道路线输入参数；上游由 initAlgorithm 为道路相关算法调用；下游统一约束输入为线图层；风险点是非米制 CRS 会导致长度和成本解释错误。"""
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ROADS,
                "道路线图层",
                [QgsProcessing.TypeVectorLine],
            )
        )

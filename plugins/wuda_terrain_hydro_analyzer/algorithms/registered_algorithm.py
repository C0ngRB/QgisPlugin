from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorDestination,
)

from ..support.core_path import ensure_core_import_path

ensure_core_import_path(__file__)

from core.hydrology.saga import saga_provider_available
from core.io.qgis_output import unique_qgis_output_path
from core.registry.algorithms import TERRAIN_HYDRO_PROVIDER_ID, algorithm_display_name
from core.reporting.summary import write_run_summary
from core.terrain.basic_terrain import extract_aspect, extract_contours, extract_hillshade, extract_slope
from core.terrain.elevation_compare import compare_dem_with_elevation_points


class RegisteredTerrainHydroAlgorithm(QgsProcessingAlgorithm):
    """类含义：地形水文插件通用薄 Algorithm；上游由 Provider 按注册表创建；下游把执行契约交给 core；风险点是当前阶段未实现的算法必须显式失败。"""

    OUTPUT_FOLDER = "OUTPUT_FOLDER"
    DEM = "DEM"
    ELEVATION_POINTS = "ELEVATION_POINTS"
    MEASURED_FIELD = "MEASURED_FIELD"
    Z_FACTOR = "Z_FACTOR"
    AZIMUTH = "AZIMUTH"
    VERTICAL_ANGLE = "VERTICAL_ANGLE"
    INTERVAL = "INTERVAL"
    OUTPUT = "OUTPUT"
    TERRAIN_ALGORITHMS = {"extract_slope", "extract_aspect", "extract_hillshade", "extract_contours"}
    IMPLEMENTED_ALGORITHMS = TERRAIN_ALGORITHMS | {"compare_dem_with_elevation_points", "check_saga_provider", "run_terrain_workflow", "run_hydrology_workflow"}

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
        return "标准化、地形与水文"

    def groupId(self):
        """函数含义：返回算法分组 ID；上游由 QGIS Processing 注册表调用；下游稳定保存工具箱分组；风险点是改名会影响模型展示。"""
        return "standardization_terrain_hydro"

    def shortHelpString(self):
        """函数含义：返回算法帮助文本；上游由 QGIS 参数面板展示；下游说明当前算法能力边界；风险点是不能承诺尚未实现的真实空间计算。"""
        if self.algorithm_name in self.TERRAIN_ALGORITHMS:
            return "输入 DEM 栅格，输出真实地形分析图层；坡度、坡向和晕渲输出 GeoTIFF，等高线输出矢量线图层。"
        if self.algorithm_name == "compare_dem_with_elevation_points":
            return "输入 DEM 和带实测高程字段的点图层，输出 DEM 采样值与高程误差字段。"
        return "当前阶段提供插件注册、SAGA 检测入口和运行摘要契约；真实水文分析按后续阶段在 core 中补齐。"

    def createInstance(self):
        """函数含义：创建同名算法新实例；上游由 QGIS Processing 克隆算法时调用；下游隔离每次执行状态；风险点是不能返回共享实例。"""
        return RegisteredTerrainHydroAlgorithm(self.algorithm_name)

    def initAlgorithm(self, config=None):
        """函数含义：声明当前算法参数；上游由 QGIS Processing 打开参数面板时调用；下游生成用户输入表单；风险点是未实现算法仍只暴露摘要输出目录。"""
        if self.algorithm_name in self.TERRAIN_ALGORITHMS:
            self.addParameter(QgsProcessingParameterRasterLayer(self.DEM, "DEM 栅格"))
            if self.algorithm_name in {"extract_slope", "extract_aspect", "extract_hillshade"}:
                self.addParameter(QgsProcessingParameterNumber(self.Z_FACTOR, "Z 因子", type=QgsProcessingParameterNumber.Double, defaultValue=1.0))
            if self.algorithm_name == "extract_hillshade":
                self.addParameter(QgsProcessingParameterNumber(self.AZIMUTH, "光照方位角", type=QgsProcessingParameterNumber.Double, defaultValue=315.0))
                self.addParameter(QgsProcessingParameterNumber(self.VERTICAL_ANGLE, "光照高度角", type=QgsProcessingParameterNumber.Double, defaultValue=45.0))
            if self.algorithm_name == "extract_contours":
                self.addParameter(QgsProcessingParameterNumber(self.INTERVAL, "等高距", type=QgsProcessingParameterNumber.Double, defaultValue=10.0, minValue=0.0001))
                self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, "等高线", QgsProcessing.TypeVectorLine))
                return
            self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT, self.displayName()))
            return

        if self.algorithm_name == "compare_dem_with_elevation_points":
            self.addParameter(QgsProcessingParameterRasterLayer(self.DEM, "DEM 栅格"))
            self.addParameter(QgsProcessingParameterFeatureSource(self.ELEVATION_POINTS, "高程点图层", [QgsProcessing.TypeVectorPoint]))
            self.addParameter(QgsProcessingParameterField(self.MEASURED_FIELD, "实测高程字段", type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.ELEVATION_POINTS))
            self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, "DEM 与高程点对比", QgsProcessing.TypeVectorPoint))
            return

        self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_FOLDER, "输出目录"))

    def processAlgorithm(self, parameters, context, feedback):
        """函数含义：执行已实现的地形水文算法入口；上游由 QGIS Processing 运行器调用；下游生成真实图层、摘要或显式拒绝未实现算法；风险点是不得生成假空间分析结果。"""
        if self.algorithm_name not in self.IMPLEMENTED_ALGORITHMS:
            raise QgsProcessingException(f"{self.displayName()} 尚未在当前阶段实现真实空间分析。")

        if self.algorithm_name in self.TERRAIN_ALGORITHMS:
            output = unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context))
            dem_layer = parameters[self.DEM]
            if self.algorithm_name == "extract_slope":
                result = extract_slope(dem_layer, self.parameterAsDouble(parameters, self.Z_FACTOR, context), output, context, feedback)
            elif self.algorithm_name == "extract_aspect":
                result = extract_aspect(dem_layer, self.parameterAsDouble(parameters, self.Z_FACTOR, context), output, context, feedback)
            elif self.algorithm_name == "extract_hillshade":
                result = extract_hillshade(dem_layer, self.parameterAsDouble(parameters, self.Z_FACTOR, context), self.parameterAsDouble(parameters, self.AZIMUTH, context), self.parameterAsDouble(parameters, self.VERTICAL_ANGLE, context), output, context, feedback)
            else:
                interval = self.parameterAsDouble(parameters, self.INTERVAL, context)
                if interval <= 0:
                    raise QgsProcessingException("等高距必须大于 0。")
                result = extract_contours(dem_layer, interval, output, context, feedback)
            return {self.OUTPUT: result["OUTPUT"]}

        if self.algorithm_name == "compare_dem_with_elevation_points":
            measured_field = self.parameterAsString(parameters, self.MEASURED_FIELD, context)
            if not measured_field:
                raise QgsProcessingException("必须选择实测高程字段。")
            result = compare_dem_with_elevation_points(parameters[self.ELEVATION_POINTS], measured_field, parameters[self.DEM], unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)), context, feedback)
            return {self.OUTPUT: result["OUTPUT"]}

        output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
        warnings = ["当前阶段仅验证插件工作流入口和摘要契约，未生成空间分析结果。"]
        if self.algorithm_name == "check_saga_provider":
            is_available = saga_provider_available()
            warnings = [] if is_available else ["SAGA Provider 不可用，后续真实水文流程应进入 demo/sample 模式。"]

        summary_path = write_run_summary(output_folder, f"{TERRAIN_HYDRO_PROVIDER_ID}:{self.algorithm_name}", outputs=[], mode="real", warnings=warnings)
        feedback.pushInfo(f"已写入运行摘要：{summary_path}")
        return {self.OUTPUT_FOLDER: output_folder}
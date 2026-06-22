from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFileDestination,
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
from core.standardization.geopackage import write_standard_geopackage
from core.standardization.validation import validate_input_layer
from core.standardization.vector import (
    reproject_to_analysis_crs,
    standardize_buildings,
    standardize_elevation_points,
    standardize_pois,
    standardize_roads,
    standardize_tracks,
)
from core.workflows.standardization import run_standardization_workflow
from core.terrain.basic_terrain import extract_aspect, extract_contours, extract_hillshade, extract_slope
from core.terrain.elevation_compare import compare_dem_with_elevation_points


class RegisteredTerrainHydroAlgorithm(QgsProcessingAlgorithm):
    """类含义：地形水文插件通用薄 Algorithm；上游由 Provider 按注册表创建；下游把执行契约交给 core；风险点是当前阶段未实现的算法必须显式失败。"""

    OUTPUT_FOLDER = "OUTPUT_FOLDER"
    INPUT = "INPUT"
    TARGET_CRS = "TARGET_CRS"
    BUILDINGS = "BUILDINGS"
    FACILITIES = "FACILITIES"
    SERVICE_TYPE_FIELD = "SERVICE_TYPE_FIELD"
    DEM = "DEM"
    ELEVATION_POINTS = "ELEVATION_POINTS"
    ROADS = "ROADS"
    TRACKS = "TRACKS"
    MEASURED_FIELD = "MEASURED_FIELD"
    DEFAULT_SPEED = "DEFAULT_SPEED"
    Z_FACTOR = "Z_FACTOR"
    AZIMUTH = "AZIMUTH"
    VERTICAL_ANGLE = "VERTICAL_ANGLE"
    INTERVAL = "INTERVAL"
    OUTPUT = "OUTPUT"
    STANDARDIZATION_ALGORITHMS = {
        "validate_input_layers",
        "reproject_to_analysis_crs",
        "standardize_buildings",
        "standardize_roads",
        "standardize_pois",
        "standardize_elevation_points",
        "standardize_tracks",
        "write_standard_geopackage",
    }
    TERRAIN_ALGORITHMS = {"extract_slope", "extract_aspect", "extract_hillshade", "extract_contours"}
    IMPLEMENTED_ALGORITHMS = STANDARDIZATION_ALGORITHMS | TERRAIN_ALGORITHMS | {"compare_dem_with_elevation_points", "check_saga_provider", "run_terrain_workflow", "run_hydrology_workflow"}

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
        help_text = {
            "validate_input_layers": "输入矢量图层，写出 validation_report.json，记录 CRS、字段和要素数。",
            "reproject_to_analysis_crs": "输入矢量图层和分析 CRS，输出转换后的矢量图层。",
            "standardize_buildings": "输入建筑面图层，输出带基础标准字段的建筑图层。",
            "standardize_roads": "输入道路线图层，输出带 length_m、access_cost、walkable、geometry_status 字段的标准道路。",
            "standardize_pois": "输入 POI 点图层和服务类型字段，输出带 service_type、capacity、weight 的标准 POI。",
            "standardize_elevation_points": "输入高程点和实测高程字段，输出带 measured_elev_m 的标准高程点。",
            "standardize_tracks": "输入轨迹线图层，输出带 length_m 和 source_method 的标准轨迹。",
            "write_standard_geopackage": "输入标准化业务图层，输出 standard_data.gpkg。",
            "compare_dem_with_elevation_points": "输入 DEM 和带实测高程字段的点图层，输出 DEM 采样值与高程误差字段。",
        }
        if self.algorithm_name in self.TERRAIN_ALGORITHMS:
            return "输入 DEM 栅格，输出真实地形分析图层；坡度、坡向和晕渲输出 GeoTIFF，等高线输出矢量线图层。"
        return help_text.get(self.algorithm_name, "当前阶段提供插件注册、SAGA 检测入口和运行摘要契约；真实水文分析按后续阶段在 core 中补齐。")

    def createInstance(self):
        """函数含义：创建同名算法新实例；上游由 QGIS Processing 克隆算法时调用；下游隔离每次执行状态；风险点是不能返回共享实例。"""
        return RegisteredTerrainHydroAlgorithm(self.algorithm_name)

    def initAlgorithm(self, config=None):
        """函数含义：声明当前算法参数；上游由 QGIS Processing 打开参数面板时调用；下游生成用户输入表单；风险点是未实现算法仍只暴露摘要输出目录。"""
        if self.algorithm_name == "validate_input_layers":
            self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, "输入矢量图层", [QgsProcessing.TypeVectorAnyGeometry]))
            self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_FOLDER, "输出目录"))
            return
        if self.algorithm_name == "reproject_to_analysis_crs":
            self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, "输入矢量图层", [QgsProcessing.TypeVectorAnyGeometry]))
            self.addParameter(QgsProcessingParameterCrs(self.TARGET_CRS, "分析 CRS", defaultValue="EPSG:4526"))
            self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, "转换后图层", QgsProcessing.TypeVectorAnyGeometry))
            return
        if self.algorithm_name == "run_standardization_workflow":
            self._add_standardization_workflow_parameters()
            return
        if self.algorithm_name in self.STANDARDIZATION_ALGORITHMS:
            self._add_standardization_parameters()
            return
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
        if self.algorithm_name == "run_standardization_workflow":
            service_type_field = self.parameterAsString(parameters, self.SERVICE_TYPE_FIELD, context)
            measured_field = self.parameterAsString(parameters, self.MEASURED_FIELD, context)
            if not service_type_field or not measured_field:
                raise QgsProcessingException("必须选择服务类型字段和实测高程字段。")
            result = run_standardization_workflow(
                parameters[self.BUILDINGS],
                parameters[self.ROADS],
                parameters[self.FACILITIES],
                service_type_field,
                parameters[self.ELEVATION_POINTS],
                measured_field,
                parameters[self.TRACKS],
                self.parameterAsString(parameters, self.OUTPUT_FOLDER, context),
                context,
                feedback,
            )
            feedback.pushInfo(f"已写入标准数据包：{result['PACKAGE']}")
            feedback.pushInfo(f"已写入运行摘要：{result['SUMMARY']}")
            return {self.OUTPUT_FOLDER: result["OUTPUT_FOLDER"]}
        if self.algorithm_name in self.STANDARDIZATION_ALGORITHMS:
            return self._run_standardization(parameters, context, feedback)
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


    def _add_standardization_workflow_parameters(self):
        """函数含义：声明一键标准化 workflow 输入参数；上游由 initAlgorithm 处理 run_standardization_workflow 时调用；下游让用户显式选择五类业务图层和关键字段；风险点是字段不能自动猜测。"""
        self.addParameter(QgsProcessingParameterFeatureSource(self.BUILDINGS, "建筑图层", [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.ROADS, "道路线图层", [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.FACILITIES, "POI 点图层", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterField(self.SERVICE_TYPE_FIELD, "服务类型字段", type=QgsProcessingParameterField.Any, parentLayerParameterName=self.FACILITIES))
        self.addParameter(QgsProcessingParameterFeatureSource(self.ELEVATION_POINTS, "高程点图层", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterField(self.MEASURED_FIELD, "实测高程字段", type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.ELEVATION_POINTS))
        self.addParameter(QgsProcessingParameterFeatureSource(self.TRACKS, "轨迹线图层", [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_FOLDER, "输出目录"))
    def _add_standardization_parameters(self):
        """函数含义：为标准化算法声明输入输出参数；上游由 initAlgorithm 分发调用；下游生成 QGIS 参数表单；风险点是字段映射仍是基础版本。"""
        if self.algorithm_name == "standardize_buildings":
            self.addParameter(QgsProcessingParameterFeatureSource(self.BUILDINGS, "建筑图层", [QgsProcessing.TypeVectorPolygon]))
            self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, "标准化建筑", QgsProcessing.TypeVectorPolygon))
        elif self.algorithm_name == "standardize_roads":
            self.addParameter(QgsProcessingParameterFeatureSource(self.ROADS, "道路线图层", [QgsProcessing.TypeVectorLine]))
            self.addParameter(QgsProcessingParameterNumber(self.DEFAULT_SPEED, "默认步行速度（千米/时）", type=QgsProcessingParameterNumber.Double, defaultValue=5.0, minValue=0.1))
            self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, "标准化道路", QgsProcessing.TypeVectorLine))
        elif self.algorithm_name == "standardize_pois":
            self.addParameter(QgsProcessingParameterFeatureSource(self.FACILITIES, "POI 点图层", [QgsProcessing.TypeVectorPoint]))
            self.addParameter(QgsProcessingParameterField(self.SERVICE_TYPE_FIELD, "服务类型字段", type=QgsProcessingParameterField.Any, parentLayerParameterName=self.FACILITIES))
            self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, "标准化 POI", QgsProcessing.TypeVectorPoint))
        elif self.algorithm_name == "standardize_elevation_points":
            self.addParameter(QgsProcessingParameterFeatureSource(self.ELEVATION_POINTS, "高程点图层", [QgsProcessing.TypeVectorPoint]))
            self.addParameter(QgsProcessingParameterField(self.MEASURED_FIELD, "实测高程字段", type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.ELEVATION_POINTS))
            self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, "标准化高程点", QgsProcessing.TypeVectorPoint))
        elif self.algorithm_name == "write_standard_geopackage":
            self.addParameter(QgsProcessingParameterFeatureSource(self.BUILDINGS, "标准建筑图层", [QgsProcessing.TypeVectorAnyGeometry]))
            self.addParameter(QgsProcessingParameterFeatureSource(self.ROADS, "标准道路图层", [QgsProcessing.TypeVectorLine]))
            self.addParameter(QgsProcessingParameterFeatureSource(self.FACILITIES, "标准 POI 图层", [QgsProcessing.TypeVectorPoint]))
            self.addParameter(QgsProcessingParameterFeatureSource(self.ELEVATION_POINTS, "标准高程点图层", [QgsProcessing.TypeVectorPoint]))
            self.addParameter(QgsProcessingParameterFeatureSource(self.TRACKS, "标准轨迹图层", [QgsProcessing.TypeVectorLine]))
            self.addParameter(QgsProcessingParameterFileDestination(self.OUTPUT, "标准 GeoPackage", "GeoPackage (*.gpkg)", defaultValue="standard_data.gpkg"))
        elif self.algorithm_name == "standardize_tracks":
            self.addParameter(QgsProcessingParameterFeatureSource(self.TRACKS, "轨迹线图层", [QgsProcessing.TypeVectorLine]))
            self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, "标准化轨迹", QgsProcessing.TypeVectorLine))

    def _run_standardization(self, parameters, context, feedback):
        """函数含义：执行标准化算法分支；上游由 processAlgorithm 对标准化算法调用；下游返回报告目录或标准化图层；风险点是字段参数为空时必须显式失败。"""
        if self.algorithm_name == "validate_input_layers":
            output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
            report_path = validate_input_layer(parameters[self.INPUT], output_folder)
            feedback.pushInfo(f"已写入校验报告：{report_path}")
            return {self.OUTPUT_FOLDER: output_folder}
        if self.algorithm_name == "reproject_to_analysis_crs":
            result = reproject_to_analysis_crs(parameters[self.INPUT], self.parameterAsCrs(parameters, self.TARGET_CRS, context), unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)), context, feedback)
            return {self.OUTPUT: result["OUTPUT"]}
        if self.algorithm_name == "standardize_buildings":
            result = standardize_buildings(parameters[self.BUILDINGS], unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)), context, feedback)
            return {self.OUTPUT: result["OUTPUT"]}
        if self.algorithm_name == "standardize_roads":
            speed = self.parameterAsDouble(parameters, self.DEFAULT_SPEED, context)
            if speed <= 0:
                raise QgsProcessingException("默认步行速度必须大于 0。")
            result = standardize_roads(parameters[self.ROADS], speed, unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)), context, feedback)
            return {self.OUTPUT: result["OUTPUT"]}
        if self.algorithm_name == "standardize_pois":
            service_type_field = self.parameterAsString(parameters, self.SERVICE_TYPE_FIELD, context)
            if not service_type_field:
                raise QgsProcessingException("必须选择服务类型字段。")
            result = standardize_pois(parameters[self.FACILITIES], service_type_field, unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)), context, feedback)
            return {self.OUTPUT: result["OUTPUT"]}
        if self.algorithm_name == "standardize_elevation_points":
            measured_field = self.parameterAsString(parameters, self.MEASURED_FIELD, context)
            if not measured_field:
                raise QgsProcessingException("必须选择实测高程字段。")
            result = standardize_elevation_points(parameters[self.ELEVATION_POINTS], measured_field, unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)), context, feedback)
            return {self.OUTPUT: result["OUTPUT"]}
        if self.algorithm_name == "write_standard_geopackage":
            result = write_standard_geopackage(
                parameters[self.BUILDINGS],
                parameters[self.ROADS],
                parameters[self.FACILITIES],
                parameters[self.ELEVATION_POINTS],
                parameters[self.TRACKS],
                self.parameterAsFileOutput(parameters, self.OUTPUT, context),
                context,
                feedback,
            )
            return {self.OUTPUT: result["OUTPUT"]}
        result = standardize_tracks(parameters[self.TRACKS], unique_qgis_output_path(self.parameterAsOutputLayer(parameters, self.OUTPUT, context)), context, feedback)
        return {self.OUTPUT: result["OUTPUT"]}
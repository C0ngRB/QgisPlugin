from core.qgis_processing.runner import run_processing_algorithm


def extract_slope(dem_layer, z_factor, output, context, feedback):
    """函数含义：从 DEM 提取坡度栅格；上游由 extract_slope Processing 算法传入 DEM 和 Z 因子；下游调用 QGIS native:slope 输出 GeoTIFF；风险点是 DEM 水平单位和高程单位不一致时必须调整 Z 因子。"""
    return run_processing_algorithm(
        "native:slope",
        {"INPUT": dem_layer, "Z_FACTOR": z_factor, "OUTPUT": output},
        context,
        feedback,
    )


def extract_aspect(dem_layer, z_factor, output, context, feedback):
    """函数含义：从 DEM 提取坡向栅格；上游由 extract_aspect Processing 算法传入 DEM 和 Z 因子；下游调用 QGIS native:aspect 输出 GeoTIFF；风险点是平坦区域坡向值需要按 QGIS 算法输出解释。"""
    return run_processing_algorithm(
        "native:aspect",
        {"INPUT": dem_layer, "Z_FACTOR": z_factor, "OUTPUT": output},
        context,
        feedback,
    )


def extract_hillshade(dem_layer, z_factor, azimuth, vertical_angle, output, context, feedback):
    """函数含义：从 DEM 生成山体阴影栅格；上游由 extract_hillshade Processing 算法传入光照参数；下游调用 QGIS native:hillshade 输出 GeoTIFF；风险点是光照方位和高度角会明显改变视觉效果。"""
    return run_processing_algorithm(
        "native:hillshade",
        {
            "INPUT": dem_layer,
            "Z_FACTOR": z_factor,
            "AZIMUTH": azimuth,
            "V_ANGLE": vertical_angle,
            "OUTPUT": output,
        },
        context,
        feedback,
    )


def extract_contours(dem_layer, interval, output, context, feedback):
    """函数含义：从 DEM 提取等高线矢量；上游由 extract_contours Processing 算法传入 DEM 和等高距；下游调用 GDAL contour 输出线图层；风险点是等高距过小会生成过多要素。"""
    return run_processing_algorithm(
        "gdal:contour",
        {
            "INPUT": dem_layer,
            "BAND": 1,
            "INTERVAL": interval,
            "FIELD_NAME": "elevation_m",
            "CREATE_3D": False,
            "IGNORE_NODATA": False,
            "NODATA": None,
            "OFFSET": 0,
            "EXTRA": "",
            "OPTIONS": "",
            "OUTPUT": output,
        },
        context,
        feedback,
    )
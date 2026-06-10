"""模块含义：封装 QGIS Processing 调用边界；上游由 core 空间分析流程调用；下游集中调用 native、GDAL、SAGA 算法；风险点是本模块只能在 QGIS Python 环境中执行。"""

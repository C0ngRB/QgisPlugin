from core.qgis_processing.runner import run_processing_algorithm


def run_native_network_algorithm(algorithm_name, parameters, context, feedback):
    """函数含义：统一调用 QGIS native 网络分析算法；上游由可达性 core 流程调用；下游执行 native 网络分析；风险点是不得绕过本函数引入 networkx、PostGIS 或 pgRouting。"""
    return run_processing_algorithm(f"native:{algorithm_name}", parameters, context, feedback)

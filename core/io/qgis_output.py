from core.io.output_naming import unique_output_path


TEMPORARY_OUTPUT = "TEMPORARY_OUTPUT"


def unique_qgis_output_path(output_path):
    """函数含义：为 QGIS 输出路径追加不覆盖后缀；上游由插件 Algorithm 在调用 core 前处理输出参数；下游返回可传给 Processing 的路径；风险点是临时输出和带图层子路径的 provider 字符串不能按普通文件处理。"""
    if not output_path or output_path == TEMPORARY_OUTPUT or output_path.startswith("memory:"):
        return output_path
    if "|" in output_path:
        file_path, provider_suffix = output_path.split("|", 1)
        return f"{unique_output_path(file_path)}|{provider_suffix}"
    return str(unique_output_path(output_path))

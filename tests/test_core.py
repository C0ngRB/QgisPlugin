import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.config.defaults import load_defaults
from core.io.output_naming import unique_output_path
from core.io.qgis_output import unique_qgis_output_path
from core.registry.algorithms import ACCESSIBILITY_PROVIDER_ID, TERRAIN_HYDRO_PROVIDER_ID, provider_algorithms
from core.reporting.summary import write_run_summary


class CoreContractTests(unittest.TestCase):
    """类含义：验证 core 的无 QGIS 基础契约；上游由 unittest 执行器调用；下游保护注册表、默认值、命名和 summary 行为；风险点是不覆盖 QGIS Desktop 运行时。"""

    def test_registry_contains_two_provider_algorithm_sets(self):
        """函数含义：校验两个 Provider 都有算法清单；上游由测试执行器调用；下游防止 Provider 注册空工具箱；风险点是不校验算法真实空间计算。"""
        self.assertIn("run_accessibility_workflow", provider_algorithms(ACCESSIBILITY_PROVIDER_ID))
        self.assertIn("run_hydrology_workflow", provider_algorithms(TERRAIN_HYDRO_PROVIDER_ID))
        self.assertIn("run_standardization_workflow", provider_algorithms(TERRAIN_HYDRO_PROVIDER_ID))

    def test_registry_includes_accessibility_network_algorithms(self):
        """函数含义：校验可达性网络算法已进入注册表；上游由测试执行器调用；下游保护 Provider 和 UI 能发现新增算法；风险点是不验证 QGIS native 参数兼容。"""
        algorithms = provider_algorithms(ACCESSIBILITY_PROVIDER_ID)
        self.assertIn("calculate_service_area", algorithms)
        self.assertIn("calculate_shortest_path", algorithms)

    def test_defaults_load_service_thresholds(self):
        """函数含义：校验默认配置可读取；上游由测试执行器调用；下游防止 defaults.json 缺失或格式错误；风险点是不校验参数是否适合真实校园数据。"""
        defaults = load_defaults()
        self.assertIn("canteen", defaults["service_thresholds"])
        self.assertEqual(defaults["default_population_weight"], 1.0)

    def test_unique_output_path_appends_suffix(self):
        """函数含义：校验输出命名不覆盖既有文件；上游由测试执行器调用；下游保护 run_summary 和空间结果命名契约；风险点是不模拟并发写入。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "result.json"
            target.write_text("{}", encoding="utf-8")
            self.assertEqual(unique_output_path(target).name, "result_001.json")

    def test_unique_qgis_output_path_keeps_transient_outputs(self):
        """函数含义：校验 QGIS 临时输出不被改名；上游由测试执行器调用；下游保护 Processing 临时图层契约；风险点是不覆盖所有 provider URI。"""
        self.assertEqual(unique_qgis_output_path("TEMPORARY_OUTPUT"), "TEMPORARY_OUTPUT")
        self.assertEqual(unique_qgis_output_path("memory:"), "memory:")

    def test_unique_qgis_output_path_preserves_provider_suffix(self):
        """函数含义：校验带 provider 参数的 QGIS 输出路径只改文件名；上游由测试执行器调用；下游避免覆盖 GeoPackage 文件并保留 layername；风险点是不模拟 QGIS 写入。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "result.gpkg"
            target.write_text("", encoding="utf-8")
            output = unique_qgis_output_path(f"{target}|layername=test")
            self.assertTrue(output.endswith("result_001.gpkg|layername=test"))

    def test_write_run_summary_records_real_output_names(self):
        """函数含义：校验运行摘要记录输出和模式；上游由测试执行器调用；下游保证课程验收可追踪；风险点是不验证 QGIS 图层加载。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            summary_path = write_run_summary(temp_dir, "provider:algorithm", ["result.gpkg"], warnings=["warning"])
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["algorithm_id"], "provider:algorithm")
            self.assertEqual(summary["outputs"], ["result.gpkg"])
            self.assertEqual(summary["warnings"], ["warning"])


if __name__ == "__main__":
    unittest.main()
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.registry.algorithms import ACCESSIBILITY_PROVIDER_ID, TERRAIN_HYDRO_PROVIDER_ID
from scripts.build_plugins import build_all


class BuildContractTests(unittest.TestCase):
    """类含义：验证插件发布构建契约；上游由 unittest 执行器调用；下游保护 zip、core 复制和 manifest 输出；风险点是不启动 QGIS 安装插件。"""

    def test_build_outputs_two_plugin_zips_and_manifest(self):
        """函数含义：执行构建并校验发布产物；上游由测试执行器调用；下游确保两个插件 zip 可交付；风险点是只校验文件结构不校验 QGIS UI 行为。"""
        result = build_all()
        zip_paths = result["zip_paths"]
        self.assertTrue(zip_paths[ACCESSIBILITY_PROVIDER_ID].exists())
        self.assertTrue(zip_paths[TERRAIN_HYDRO_PROVIDER_ID].exists())
        self.assertTrue(result["manifest_path"].exists())

        manifest = json.loads(result["manifest_path"].read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["plugins"]), 2)

    def test_zip_contains_plugin_core_and_metadata(self):
        """函数含义：校验 zip 内部包含 QGIS 插件根目录和复制后的 core；上游由测试执行器调用；下游防止发布态缺少共享库；风险点是不校验 core 业务逻辑完整度。"""
        result = build_all()
        zip_path = result["zip_paths"][ACCESSIBILITY_PROVIDER_ID]
        with zipfile.ZipFile(zip_path) as zip_file:
            names = set(zip_file.namelist())
        self.assertIn(f"{ACCESSIBILITY_PROVIDER_ID}/metadata.txt", names)
        self.assertIn(f"{ACCESSIBILITY_PROVIDER_ID}/core/config/defaults.json", names)
        self.assertIn(f"{ACCESSIBILITY_PROVIDER_ID}/core/registry/algorithms.py", names)


if __name__ == "__main__":
    unittest.main()

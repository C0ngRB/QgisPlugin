# wuda_spatial_analysis_toolkit

武汉大学 GIS 实践课程 QGIS 空间分析自动化插件项目，按 ADR 交付两个可独立安装的 QGIS 插件和共享 core。

## 结构

```text
core/      # 共享核心库，源码态只维护一份
plugins/   # 两个薄 QGIS 插件壳
scripts/   # 构建脚本
tests/     # 无 QGIS 依赖的基础测试
docs/      # 用户指南和 QGIS 手工验收清单
build/     # 构建产物，脚本生成
dist/      # 发布产物，脚本生成
```

## 构建

```bash
python scripts/build_plugins.py
```

构建后生成：

- `dist/wuda_accessibility_analyzer.zip`
- `dist/wuda_terrain_hydro_analyzer.zip`
- `dist/release_manifest.json`
- `dist/build_report.txt`

## 当前能力

- `WudaAccessibilityAnalyzer`：标准化、GeoPackage 打包、道路成本、设施缓冲、最近设施、网络服务区、最短路径、设施适宜性和可达性 workflow。
- `WudaTerrainHydroAnalyzer`: standardization, GeoPackage packaging, terrain outputs, DEM elevation comparison, terrain workflow, real SAGA hydrology through provider or `saga_cmd.exe`, and demo summary only when no SAGA engine exists.
- Real hydrology uses SAGA only: QGIS `saga/sagang` provider first, then `saga_cmd.exe` from the same QGIS/OSGeo4W install; if neither exists, the plugin writes a demo summary and never substitutes GRASS or fake layers.

## 验证命令

```bash
python -m unittest discover -s tests
python scripts/build_plugins.py
```

QGIS Desktop 运行时验收见 `docs/qgis_manual_checklist.md`，也可以运行：`"C:\Program Files\QGIS 3.40.0\bin\python-qgis.bat" tests\qgis_runtime_check.py`。

# wuda_spatial_analysis_toolkit

本目录按 ADR 构建武汉大学 GIS 实践课程 QGIS 空间分析自动化插件项目。

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

## 当前阶段

已完成 ADR 要求的两插件工程骨架、共享 core、算法注册表、PyQt 向导入口、构建脚本、基础测试和文档。真实空间分析业务逻辑按 ADR 后续阶段继续补入 `core/`。

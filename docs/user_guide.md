# 用户指南

## 安装

1. 运行 `python scripts/build_plugins.py`。
2. 在 `dist/` 中获得两个 QGIS 插件压缩包。
3. 在 QGIS 中通过“插件 > 管理并安装插件 > 从 ZIP 安装”分别安装：
   - `wuda_accessibility_analyzer.zip`
   - `wuda_terrain_hydro_analyzer.zip`

## 使用边界

- 当前阶段完成插件框架、Provider 注册、算法清单、UI 入口、构建脚本和基础测试。
- 当前阶段不伪造空间分析结果。
- 真实空间分析逻辑必须继续放入 `core/`，插件壳只做参数读取和结果返回。

## 后续实现顺序

1. 补齐 `WudaAccessibilityAnalyzer` 的标准化和可达性 core 流程。
2. 补齐 `WudaTerrainHydroAnalyzer` 的地形和 SAGA 水文 core 流程。
3. 用 QGIS 手工验收清单验证插件安装、菜单、Provider、workflow 和 demo 模式。

## 已实现可视化算法

- wuda_accessibility_analyzer:generate_facility_buffers：输入设施图层和服务距离，输出真实缓冲区面图层。

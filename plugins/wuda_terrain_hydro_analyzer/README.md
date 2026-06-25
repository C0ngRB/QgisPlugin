# WudaTerrainHydroAnalyzer

武汉大学校园地形与水文分析 QGIS 插件。

## 当前能力

- 插件可安装，菜单可打开 PyQt 向导入口。
- Provider 注册标准化、地形和水文算法清单。
- 地形算法输出真实坡度、坡向、晕渲、等高线和 DEM 高程点对比结果。
- `run_terrain_workflow` 一键生成基础地形成果和 `run_summary.json`。
- Fine-grained hydrology algorithms use SAGA only: QGIS provider first, then `saga_cmd.exe`; if neither exists they fail clearly and never use GRASS or fake results.
- `run_hydrology_workflow` writes `mode=real` when provider or `saga_cmd.exe` is available; only when both are unavailable does it enter demo summary mode.

## 水文边界

真实水文输出需要 QGIS Processing 中存在 `saga` 或 `sagang` provider，并且 SAGA 算法 ID 与当前适配器匹配。当前仓库没有打包真实 demo/sample 空间数据；无 SAGA 且无 demo 数据时，只写 demo 摘要，不生成空间图层。

## 使用

1. 在 QGIS 中安装本插件 zip。
2. 启用 `WudaTerrainHydroAnalyzer`。
3. 点击菜单 `WUDA 地形水文分析`。
4. 从向导入口打开地形或水文 workflow。

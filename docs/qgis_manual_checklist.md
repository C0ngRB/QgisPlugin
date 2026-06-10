# QGIS 手工验收清单

## 安装

- [ ] QGIS 能从 `dist/wuda_accessibility_analyzer.zip` 安装插件。
- [ ] QGIS 能从 `dist/wuda_terrain_hydro_analyzer.zip` 安装插件。
- [ ] 插件管理器显示两个插件均已启用。

## 菜单与 UI

- [ ] 菜单出现 `WUDA 可达性分析`。
- [ ] 菜单出现 `WUDA 地形水文分析`。
- [ ] 两个 PyQt 面板均可打开。
- [ ] 默认模式只展示 workflow 入口。
- [ ] 高级模式展示细粒度算法入口。

## Processing

- [ ] Processing 工具箱出现 `WUDA 可达性分析` Provider。
- [ ] Processing 工具箱出现 `WUDA 地形水文分析` Provider。
- [ ] `run_standardization_workflow` 能打开参数窗口。
- [ ] `run_accessibility_workflow` 能打开参数窗口。
- [ ] `run_terrain_workflow` 能打开参数窗口。
- [ ] `run_hydrology_workflow` 能打开参数窗口。
- [ ] `check_saga_provider` 能写入 `run_summary.json`。

## 边界

- [ ] 未实现细粒度算法会明确报错，不生成假结果。
- [ ] SAGA 不可用时，水文流程说明应进入 demo/sample 模式。

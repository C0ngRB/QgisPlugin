# QGIS 手工验收清单

## 安装

- [ ] QGIS 能从 `dist/wuda_accessibility_analyzer.zip` 安装插件。
- [ ] QGIS 能从 `dist/wuda_terrain_hydro_analyzer.zip` 安装插件。
- [ ] 插件管理器显示两个插件均已启用。

## 菜单与 UI

- [ ] 菜单出现 `WUDA 可达性分析`。
- [ ] 菜单出现 `WUDA 地形水文分析`。
- [ ] 两个 PyQt 面板均可打开。
- [ ] 默认模式展示 workflow 入口。
- [ ] 高级模式展示细粒度算法入口。

## Processing 注册

- [ ] Processing 工具箱出现 `WUDA 可达性分析` Provider。
- [ ] Processing 工具箱出现 `WUDA 地形水文分析` Provider。
- [ ] `release_manifest.json` 中列出的算法均能在对应 Provider 中找到。

## 标准化验收

- [ ] `run_standardization_workflow` 能打开参数窗口。
- [ ] 输入建筑、道路、POI、高程点、轨迹后生成 `standard_data.gpkg`。
- [ ] GeoPackage 至少包含 `buildings`、`roads`、`pois`、`elevation_points`、`tracks` 五个图层。
- [ ] 输出目录生成 `run_summary.json`，且 `outputs` 记录真实 GeoPackage 路径。

## 可达性验收

- [ ] `run_accessibility_workflow` 能打开参数窗口。
- [ ] workflow 生成 `accessibility_buildings.gpkg`。
- [ ] workflow 生成 `facility_service_areas.gpkg`。
- [ ] workflow 生成 `facility_supply_demand.gpkg`。
- [ ] workflow 生成 `nearest_facility_links.gpkg`。
- [ ] 四个输出图层均可加载，且 `run_summary.json` 记录真实输出名。

## 地形验收

- [ ] `run_terrain_workflow` 能打开参数窗口。
- [ ] workflow 生成 `slope.tif`、`aspect.tif`、`hillshade.tif`。
- [ ] workflow 生成 `contours.gpkg`，字段包含 `elevation_m`。
- [ ] workflow 生成 `dem_elevation_comparison.gpkg`，字段包含 `measured_elev_m`、`dem_elev_m`、`elev_diff_m`、`abs_diff_m`。
- [ ] 输出目录生成 `run_summary.json`。

## 水文验收

- [ ] `check_saga_provider` writes `run_summary.json` and reflects availability of QGIS SAGA provider or `saga_cmd.exe`.
- [ ] QGIS Processing provider 列表有 `saga` 或 `sagang` 时，水文细粒度算法执行真实 SAGA 流程。
- [ ] If provider is absent but `saga_cmd.exe` exists, `fill_sinks` and related hydrology algorithms still generate real SAGA outputs.
- [ ] If both SAGA provider and `saga_cmd.exe` are unavailable, `run_hydrology_workflow` writes `mode=demo`, `is_demo_result=true`.
- [ ] 若插件包未包含真实 demo/sample 空间数据，水文 demo summary 的 `outputs` 应为空，并包含“未生成任何 demo 空间图层”警告。

## 边界

- [ ] 水文算法不调用 GRASS、WhiteboxTools 或欧氏距离替代 SAGA。
- [ ] 输出文件冲突时追加 `_001`、`_002` 后缀，不覆盖已有结果。
- [ ] 插件壳不直接实现空间分析，业务逻辑位于 `core/`。
## 自动化运行时验收

- [ ] 可运行 `"C:\Program Files\QGIS 3.40.0\bin\python-qgis.bat" tests\qgis_runtime_check.py`，并获得 JSON 验收报告。

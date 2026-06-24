# 用户指南

## 安装

1. 运行 `python scripts/build_plugins.py`。
2. 在 `dist/` 中获得两个 QGIS 插件压缩包。
3. 在 QGIS 中通过“插件 > 管理并安装插件 > 从 ZIP 安装”分别安装：
   - `wuda_accessibility_analyzer.zip`
   - `wuda_terrain_hydro_analyzer.zip`

## 推荐使用顺序

1. 运行 `run_standardization_workflow`，输入建筑、道路、POI、高程点、轨迹和关键字段，生成 `standard_data.gpkg`。
2. 运行 `run_accessibility_workflow`，生成设施适宜性、网络服务区、供需表和最近设施校核线。
3. 运行 `run_terrain_workflow`，生成坡度、坡向、晕渲、等高线和 DEM 高程点对比。
4. 若 QGIS 已安装并启用 SAGA provider，可运行水文细粒度算法或 `run_hydrology_workflow`；否则 workflow 只写 demo 摘要并说明原因。

## 已实现可视化算法

### 可达性插件

- `generate_facility_buffers`：设施服务缓冲区面图层。
- `calculate_road_length`：带 `length_m` 字段的道路图层。
- `build_network_cost`：带 `length_m/access_cost` 字段的道路图层。
- `calculate_nearest_facility`：源图层到最近设施校核线。
- `calculate_service_area`：网络服务区线。
- `calculate_shortest_path`：起点到目标点的最短路径线。
- `calculate_facility_suitability`：建筑 × 服务类型的适宜性长表。
- `run_accessibility_workflow`：一键输出 `accessibility_buildings`、`facility_service_areas`、`facility_supply_demand`、`nearest_facility_links`。

### 地形水文插件

- `extract_slope`：坡度 GeoTIFF。
- `extract_aspect`：坡向 GeoTIFF。
- `extract_hillshade`：晕渲 GeoTIFF。
- `extract_contours`：带 `elevation_m` 字段的等高线图层。
- `compare_dem_with_elevation_points`：DEM 采样值与实测高程误差点图层。
- `run_terrain_workflow`：一键输出基础地形成果。
- `fill_sinks`、`extract_flow_direction`、`extract_flow_accumulation`、`extract_stream_order`、`extract_stream_network`、`extract_watershed_basins`：真实水文算法入口，仅在 SAGA provider 可用时执行。
- `run_hydrology_workflow`：有 SAGA 时执行真实流程；无 SAGA 时写 demo 摘要，不生成伪图层。

## 水文边界

本项目 ADR 明确禁止使用 GRASS、WhiteboxTools 或欧氏距离结果冒充 SAGA 水文。当前插件会检测 `saga/sagang` provider；检测不到时，细粒度水文算法明确失败，workflow 写 `mode=demo`、`is_demo_result=true` 的 `run_summary.json`。
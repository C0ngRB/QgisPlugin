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
4. Run hydrology fine-grained algorithms or `run_hydrology_workflow` when QGIS `saga/sagang` provider or `saga_cmd.exe` is available; only when both are unavailable does workflow write a demo summary.

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
- `fill_sinks`, `extract_flow_direction`, `extract_flow_accumulation`, `extract_stream_order`, `extract_stream_network`, `extract_watershed_basins`: real hydrology entries executed by SAGA provider or `saga_cmd.exe`.
- `run_hydrology_workflow`: runs the real SAGA workflow when provider or `saga_cmd.exe` exists; otherwise writes a demo summary without fake layers.

## 水文边界

This ADR forbids GRASS, WhiteboxTools, or Euclidean substitutes for SAGA hydrology. The plugin checks QGIS `saga/sagang` provider and `saga_cmd.exe`; either one runs real SAGA, and only when both are absent does it write `mode=demo`, `is_demo_result=true`.

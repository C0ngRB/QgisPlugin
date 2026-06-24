# Demo 数据说明

本目录用于发布阶段携带真实预生成的水文 demo/sample 结果。当前仓库没有打包空间 demo 数据；无 SAGA provider 时插件只写 `mode=demo` 的 `run_summary.json`，并明确说明未生成 demo 空间图层。

如后续加入真实 demo 数据，文件名应与 ADR 保持一致：

- `demo_filled_dem.tif`
- `demo_flow_direction.tif`
- `demo_flow_accumulation.tif`
- `demo_stream_order.tif` 或同名 GeoPackage
- `demo_stream_network.gpkg`
- `demo_drainage_basins.gpkg`
# WudaAccessibilityAnalyzer

武汉大学校园可达性与设施适宜性分析 QGIS 插件。

## 当前能力

- 插件可安装，菜单可打开 PyQt 向导入口。
- Provider 注册标准化与可达性算法清单。
- 标准化 workflow 生成 `standard_data.gpkg` 和 `run_summary.json`。
- 可达性 workflow 输出 `accessibility_buildings`、`facility_service_areas`、`facility_supply_demand`、`nearest_facility_links`。
- 细粒度算法支持设施缓冲、道路长度、网络成本、最近设施、网络服务区、最短路径和设施适宜性评价。

## 使用边界

业务逻辑通过共享 `core/` 进入，插件壳只做参数读取和结果返回。首版设施适宜性为服务区叠置近似 E2SFCA，不是完整 OD 矩阵版 E2SFCA。

## 使用

1. 在 QGIS 中安装本插件 zip。
2. 启用 `WudaAccessibilityAnalyzer`。
3. 点击菜单 `WUDA 可达性分析`。
4. 从向导入口打开 workflow 或高级细粒度算法窗口。
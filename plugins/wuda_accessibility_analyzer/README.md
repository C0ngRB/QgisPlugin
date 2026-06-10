# WudaAccessibilityAnalyzer

武汉大学校园可达性与设施适宜性分析 QGIS 插件。

## 当前阶段

- 插件可安装。
- 菜单可打开 PyQt 向导入口。
- Provider 注册标准化与可达性算法清单。
- 业务逻辑通过共享 `core/` 进入，插件壳不直接实现空间分析。

## 使用

1. 在 QGIS 中安装本插件 zip。
2. 启用 `WudaAccessibilityAnalyzer`。
3. 点击菜单 `WUDA 可达性分析`。
4. 从向导入口打开 workflow 或高级细粒度算法窗口。

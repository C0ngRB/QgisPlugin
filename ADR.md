# wuda_spatial_analysis_toolkit ADR

日期：2026-06-08
状态：已决策

## ADR 使用说明

本文件是 `wuda_spatial_analysis_toolkit` 的架构事实来源。Codex 或后续 session 必须先读本文件，再读 `handoff.md`。若 HANDOFF 与 ADR 冲突，以 ADR 为准，先修正 HANDOFF，不得直接推翻已决策内容。

本项目目标是开发一套服务武汉大学 GIS 实践课程的 QGIS 空间分析自动化插件：以武汉大学校园为默认场景，算法尽量通用；最终交付两个可独立安装的 QGIS 插件压缩包、共享核心库源码、构建脚本、测试、用户文档和验收清单。

---

# ADR-000: 决策粒度、工程纪律与 Codex 执行规则

日期：2026-06-08
状态：已决策

## 背景

本项目从课程实践需求出发，存在 QGIS 插件架构、空间分析模型、数据标准化、构建交付、测试验收等多类决策。如果不区分决策层级，Codex 很容易跳过架构约束直接写代码，后续会出现插件边界混乱、核心逻辑重复、输出不可追踪等问题。

## 备选方案

A. 所有细节都写入 ADR

好处：
- 所有事项都有记录。
- 后续 session 不容易遗漏上下文。
- 便于严格追责。

代价：
- ADR 会膨胀为实现笔记。
- 大量 L3 细节会拖慢决策。
- Codex 执行时容易被无关约束干扰。

B. 只记录 L1/L2，L3 交给实现

好处：
- ADR 保持架构事实来源，不变成代码说明书。
- 用户只需要决定影响面较大的事项。
- Codex 有足够实现空间。

代价：
- L3 细节需要靠代码注释和测试固化。
- 后续审查必须区分“架构违背”和“实现选择”。
- 如果 L2 漏定，Codex 仍可能自由发挥。

C. 不写 ADR，只保留聊天记录

好处：
- 初期最快。
- 不需要维护文档。
- 对短脚本项目足够。

代价：
- Codex 无法稳定接手。
- 决策冲突难发现。
- 课程成果交付不可审计。

## 决策

选择 B：只把 L1/L2 及少量必须固化的执行约束写入 ADR；L3 实现细节交给 Codex，但必须受本 ADR、HANDOFF、代码注释、单元测试和 QGIS 手工验收清单约束。

决策粒度规则：

- L1：整体架构决策。包括模块边界、插件主线、执行引擎、外部依赖、安全边界、与外部模块关系。必须先给用户至少 3 个选项，由用户确认后写入 ADR。
- L2：局部战术决策。包括算法输入输出、错误分级、字段模型、构建策略、测试策略。影响面较大的写入 ADR。
- L3：具体实现决策。包括类名、函数拆分、局部变量、测试 fixture、UI 控件布局等。Codex 自行决定，不升级为 ADR。

编码纪律：

- 所有可复用业务逻辑必须放入 `core/`。
- QGIS 插件目录只保留插件壳、Provider、Algorithm 类和 UI 导航。
- 工作流算法只做编排，不重复实现业务逻辑。
- UI 只负责打开 Processing 算法窗口，不直接执行空间分析。
- 构建产物 `build/`、`dist/` 不得手工维护源码。
- 函数注释必须说明函数作用、上游调用方、下游依赖、危险边界。

## 影响

Codex 应按照 ADR 决策实现，不得擅自改为单插件、不得绕过标准化、不得改用 GRASS、Docker、PostGIS、networkx 等未决策依赖。若发现 ADR 不足以继续实现，应暂停并向用户提出新的 L1/L2 决策问题。

## 下一步方向

后续若项目进入长期维护，可单独新增 ADR，把 L3 中反复出现的局部规则上升为 L2 规范。

---

# ADR-001: 项目总体定位、研究区与首版功能范围

日期：2026-06-08
状态：已决策

## 背景

指导书要求 QGIS 插件应结合前期数据处理、符号化、空间分析痛点，完成有实用价值或补充 QGIS 功能的插件。项目需在“数据采集质检、空间分析自动化、制图自动化、小系统原型”之间确定主线，同时要满足课程中“不少于 2 个有实用价值插件”的交付要求。

## 备选方案

A. 数据采集与质检插件套件

好处：
- 贴合建筑、POI、轨迹高程等班级采集任务。
- 工程风险低，容易交付。
- 可服务后续数据库建设。

代价：
- 空间分析深度不足。
- 插件视觉展示效果一般。
- 与地形、水文、路网分析方向结合较弱。

B. 空间分析自动化插件套件

好处：
- 直接覆盖公共设施、地形、水文、路网等指导书方向。
- 报告中有算法、指标和模型可写。
- 插件成果与空间分析专题图可形成闭环。

代价：
- 输入数据质量和 QGIS 环境依赖更高。
- 算法范围容易膨胀。
- 水文和网络分析需要较严格边界。

C. 制图与符号化自动化插件套件

好处：
- 输出成果稳定，适合专题图整饰。
- 技术风险较低。
- 可提高全班制图效率。

代价：
- 空间分析技术含量不足。
- 容易被认为只是样式工具。
- 与完整空间分析模型结合较弱。

D. 小系统原型优先，插件作为附属

好处：
- 工程完整性强。
- 后续可扩展 WebGIS 或数据库系统。
- 能覆盖数据载入、显示、查询、简单分析。

代价：
- 范围最大，短期风险高。
- 会分散插件开发主线。
- 环境和交付复杂度明显上升。

## 决策

选择 B：空间分析自动化插件套件。

具体定位：

- 以武汉大学校园为默认场景，算法尽量通用。
- 首版采取完整分析型功能范围：可达性/路网/设施适宜性 + 地形 + 水文。
- 插件设计要能支撑课程报告、专题图和插件演示三类成果。
- 实现顺序先做 `WudaAccessibilityAnalyzer`，再做 `WudaTerrainHydroAnalyzer`。

已决策编号对应：

- L1-001：选择空间分析自动化插件套件。
- L1-005：选择武大校园主线，算法尽量通用。
- L1-006：选择完整分析型。
- L2-021：选择按插件分别实现。
- L2-022：选择先实现 `WudaAccessibilityAnalyzer`，再实现 `WudaTerrainHydroAnalyzer`。

## 影响

项目不得退化为纯数据采集工具或纯制图工具。插件必须围绕空间分析能力组织，且两个插件都应有独立价值。武大场景只作为默认场景，不得在 `core/` 中硬编码“武汉大学”边界或具体图层名。

## 下一步方向

小系统原型、WebGIS、班级数据库直连、三维展示可作为后续增强，不进入首版 Codex 任务。

---

# ADR-002: 插件模块边界、核心库分发与 QGIS 交互形态

日期：2026-06-08
状态：已决策

## 背景

课程要求不少于 2 个有实用价值的 QGIS 插件。项目同时需要避免两个插件重复写 CRS、输出命名、Processing 调用、日志和错误处理等公共逻辑。因此必须决定插件边界、共享核心库如何发布，以及用户通过什么入口使用算法。

## 备选方案

A. 两个完全独立插件，各写各的逻辑

好处：
- 最符合“两插件”的表面要求。
- 单个插件坏了不影响另一个。
- 初期理解简单。

代价：
- 公共逻辑重复。
- 错误处理、输出、日志风格容易不一致。
- 后续维护成本高。

B. 单插件多工具箱

好处：
- 工程结构最简单。
- 公共逻辑天然统一。
- 用户体验集中。

代价：
- 与“不少于两个插件”的课程表述不完全一致。
- 一个插件失败会影响全部功能。
- 后续拆分成本高。

C. 共享核心库 + 两个薄插件

好处：
- 既满足两个插件交付，也避免公共逻辑重复。
- core 可被测试和复用。
- 架构边界清楚，适合 Codex 分工。

代价：
- QGIS 插件加载共享 core 需要处理。
- 构建脚本复杂度上升。
- 需要严格防止业务逻辑进入插件壳。

D. core 做成可安装 Python 包

好处：
- 工程最正规。
- core 可独立版本化。
- 长期维护价值高。

代价：
- QGIS Python 环境安装包风险高。
- 课程验收安装步骤复杂。
- 不适合插件 zip 独立交付。

## 决策

选择 C，并采用发布阶段复制 core 的方式。

具体约束：

- 源码态只维护一份根目录 `core/`。
- 发布态由 `scripts/build_plugins.py` 把 `core/` 复制进两个插件包内部。
- 交付两个独立 QGIS 插件 zip：`wuda_accessibility_analyzer.zip` 与 `wuda_terrain_hydro_analyzer.zip`。
- 插件采用混合交互形态：Processing 算法是正式执行契约，PyQt 面板只是向导入口。
- PyQt 面板默认显示工作流入口，高级模式显示细粒度算法入口。
- PyQt 面板只打开 QGIS 原生 Processing 算法对话框，不直接执行 `processing.run()`。

已决策编号对应：

- L1-002：核心分析库 + 两个薄插件。
- L1-003：源码阶段单 core，发布阶段构建脚本复制 core 到插件包。
- L1-004：Processing 算法为核心契约，PyQt 面板做向导入口。
- L2-014：双模式 PyQt 面板。
- L2-015：面板打开 Processing 算法窗口，不直接执行。

## 影响

Codex 必须把业务逻辑写在 `core/`；插件目录中 Algorithm 类只做参数读取、调用 core、返回结果。PyQt UI 不得进行空间分析、字段标准化、CRS 转换、输出命名或日志写入。

## 下一步方向

后续若课程外继续维护，可把 `core/` 抽成标准 Python 包，但首版不做 pip 安装、不做 Docker 运行依赖。

---

# ADR-003: 运行依赖、Processing 调用封装与外部算法策略

日期：2026-06-08
状态：已决策

## 背景

空间分析插件需要调用 QGIS native、GDAL、SAGA 等处理能力。水文分析若要贴合指导书，通常需要 SAGA；但 GRASS、Docker、PostGIS 等依赖会增加课程交付风险。因此必须明确哪些依赖允许使用、哪些禁止进入运行时，以及 Processing 调用如何封装。

## 备选方案

A. 只使用 QGIS native + GDAL

好处：
- 环境最稳。
- 插件安装简单。
- 课程验收风险最低。

代价：
- 高级水文链条不足。
- 与指导书 SAGA 水文流程不完全对齐。
- 部分模型只能缩水。

B. 基础功能使用 QGIS native/GDAL，高级水文只强依赖 SAGA

好处：
- 基础分析稳定。
- 水文流程可对齐指导书。
- 只依赖一个外部水文引擎，范围可控。

代价：
- SAGA 不可用时真实水文不能运行。
- 需要 demo/sample 模式。
- 需要明确 SAGA provider 检测和错误提示。

C. 同时支持 SAGA 和 GRASS

好处：
- 兼容性看似更好。
- 可选择算法更多。
- 后续扩展空间大。

代价：
- 算法 ID、参数、输出都要维护两套。
- 环境风险更高。
- Codex 实现范围扩大。

D. Docker 封装全部依赖

好处：
- 理论上环境可复现。
- 可固定 QGIS/SAGA 版本。
- 适合后端批处理。

代价：
- QGIS Desktop 插件无法用 Docker 作为常规运行依赖。
- 机房 Windows 环境不一定支持 Docker。
- 容器路径、GUI、权限都会复杂化。

## 决策

选择 B 的收缩版：基础功能依赖 QGIS native/GDAL；高级水文只强依赖 SAGA；不兼容 GRASS；Docker 只允许作为可选开发环境，不作为插件运行依赖。

具体约束：

- 所有 Processing 调用必须通过 `core/qgis_processing/` 下封装模块进行。
- 网络分析调用必须走 `core/qgis_processing/network_runner.py`。
- SAGA 水文调用必须先检测 SAGA provider 是否可用。
- SAGA 不可用时进入 demo/sample 模式，不执行真实水文。
- 若 SAGA 算法不存在或参数不兼容，返回明确 ERROR，不静默改用 GRASS 或欧氏距离。
- 网络分析不得引入 `networkx`、PostGIS、pgRouting。
- 水文分析不得引入 GRASS 或 WhiteboxTools。

已决策编号对应：

- L1-007：基础功能用 QGIS native/GDAL，高级水文只强依赖 SAGA，不兼容 GRASS。
- L2-001：SAGA 不可用时启用内置演示模式。
- L2-002：演示模式只内置预生成结果图层。
- L2-026：路网分析使用 QGIS native 网络分析算法。
- L2-037：QGIS native 网络分析调用走统一适配器。
- L2-040：SAGA 水文真实流程按指导书对齐流程执行。
- L2-041：水文 demo/sample 结果与真实流程输出同名对应。

## 影响

Codex 不得通过 pip 添加外部网络分析或水文分析库。真实水文结果强依赖 SAGA；无 SAGA 时只能加载 demo/sample 结果，且必须显式标记为非实时计算。

## 下一步方向

后续如确需支持 GRASS 或 Docker，应新增 ADR，不得在首版私自增加。

---

# ADR-004: 标准化数据模型、CRS、元数据与质检策略

日期：2026-06-08
状态：已决策

## 背景

空间分析算法不能直接依赖原始建筑、道路、POI、DEM、轨迹数据的任意字段。项目需要先把原始数据转换为统一标准库，再执行分析。标准库还需要记录字段映射、质量检查、处理日志和 CRS 信息，保证结果可追踪。

## 备选方案

A. 分析算法直接读取原始图层

好处：
- 工作流短。
- 初期实现快。
- 用户不用先标准化。

代价：
- 字段名和 CRS 不稳定。
- 每个算法都要重复校验。
- 后续结果不可追踪。

B. 固定字段模板，用户提前整理数据

好处：
- 算法简单。
- 字段读取稳定。
- 适合统一采集规范。

代价：
- 数据稍不一致就失败。
- 泛化能力弱。
- 无法记录原始字段映射过程。

C. 先运行数据标准化算法，生成元数据驱动 GeoPackage

好处：
- 后续分析输入稳定。
- 字段映射、质量检查、日志可追踪。
- 可支撑班级数据长期维护。

代价：
- 首版复杂度提高。
- 需要定义标准业务图层和元数据表。
- 用户流程多一步。

D. 数据库/PostGIS 标准化

好处：
- 多人协作能力强。
- 数据治理更完整。
- 长期工程价值高。

代价：
- 需要数据库环境。
- 与插件 zip 独立交付冲突。
- 课程首版过重。

## 决策

选择 C：先运行数据标准化算法，生成元数据驱动 `standard_data.gpkg`，后续分析只读取标准库。

标准业务图层：

- `buildings`
- `roads`
- `cleaned_roads`
- `pois`
- `elevation_points`
- `tracks`
- `dem_index`
- `analysis_units`

元数据表：

- `schema_metadata`
- `source_layers`
- `field_mapping`
- `validation_report`
- `processing_log`

标准字段深度选择“均衡分析字段”。核心字段：

```text
buildings:
  id, source_id, name, building_type,
  floors, height_m, ground_elev_m, roof_elev_m,
  population_weight, geometry_status, representative_point_source

roads:
  id, source_id, name, road_type,
  speed_kmh, direction, length_m,
  slope_cost, access_cost, walkable, geometry_status

pois:
  id, source_id, name, poi_type,
  service_type, service_level, capacity,
  weight, geometry_status

elevation_points:
  id, source_id, point_type,
  measured_elev_m, dem_elev_m, elev_diff_m,
  source_method

tracks:
  id, source_id, track_name,
  length_m, elev_min_m, elev_max_m,
  elev_gain_m, source_method

dem_index:
  id, dem_path, crs_authid,
  resolution_m, nodata_value, vertical_unit, note

analysis_units:
  id, unit_type, name, weight, note
```

CRS 策略：

- 标准化阶段强制用户指定米制投影 `analysis_crs`。
- 所有矢量标准图层转换到 `analysis_crs`。
- 原始图层缺失 CRS、CRS 不可解析或无法转换时，标准化失败。
- 距离、面积、服务区、路径成本均按 `analysis_crs` 的米制单位处理。

质检分级：

- `ERROR`：中止标准化。
- `WARNING`：记录后继续。
- `INFO`：记录过程。

默认值策略：

- 默认值集中在 `core/config/defaults.json`。
- 不得在算法函数中硬编码默认值。
- 默认值使用必须写入 `validation_report`、`processing_log` 和 `run_summary.json`。

道路拓扑：

- 标准化阶段生成 `cleaned_roads`，原始 `roads` 不覆盖。
- 受控拓扑修复包括几何修复、空几何删除、walkable 过滤、长度和成本字段计算、小容差端点吸附、交叉打断、连通性辅助处理。
- 拓扑修复全部调用 QGIS native Processing 工具，`core` 不自写复杂拓扑修复算法。
- `topology_report` 不作为 workflow 默认输出图层，统计写入元数据和 summary。

建筑代表点：

- 建筑面参与分析时使用 `point_on_surface` 生成代表点。
- 首版不采集入口点，不做道路吸附。
- 标准化结果记录 `representative_point_source = "point_on_surface"`。

服务类型：

- `pois.service_type` 采用固定枚举：`canteen`, `express`, `toilet`, `teaching_service`, `study_space`, `medical`, `sports`, `scenic`, `other`。
- 未知 service_type 归入 `other`，记录 WARNING。

已决策编号对应：

- L2-005：先标准化数据，再运行分析。
- L2-006：元数据驱动 GeoPackage。
- L2-007：均衡元数据。
- L2-008：标准化阶段强制指定分析 CRS。
- L2-009：ERROR 中止，WARNING 继续，INFO 记录。
- L2-010：标准业务图层均衡分析字段。
- L2-011：默认值由 `core/config/defaults.json` 驱动。
- L2-031：service_type 固定枚举。
- L2-032：未知 service_type 归入 other。
- L2-033：建筑代表点使用 point_on_surface。
- L2-034：受控拓扑修复。
- L2-035：拓扑修复全部使用 QGIS native Processing 工具。

## 影响

后续所有分析算法只能读标准库，不得直接读用户原始字段。Codex 必须优先实现标准化流程，否则可达性、地形、水文算法都不能进入稳定实现。

## 下一步方向

后续可增加中文 POI 类型到固定枚举的映射表，减少 `other` 类比例。该增强需另开 ADR。

---

# ADR-005: Processing 算法粒度、注册表、UI 和工作流编排

日期：2026-06-08
状态：已决策

## 背景

插件需要同时支持 QGIS Processing 工具箱、PyQt 向导入口、工作流算法和细粒度算法。若算法 ID 分散硬编码，UI、Provider、README、测试会互相脱节。

## 备选方案

A. 每个插件只暴露一两个大 workflow 算法

好处：
- 用户操作简单。
- 工具箱清爽。
- 初期实现快。

代价：
- 算法内部黑盒化。
- 调试困难。
- 不利于模型构建器复用。

B. 只暴露细粒度算法

好处：
- 最像专业工具箱。
- 每个算法职责清楚。
- 适合高级用户组合。

代价：
- 普通用户使用门槛高。
- 演示流程长。
- 需要手工串联很多步骤。

C. 细粒度算法 + 工作流封装

好处：
- 既能分步调试，也能一键编排。
- 与 Processing 和 PyQt 双入口兼容。
- 适合课程展示和后续扩展。

代价：
- 算法数量多。
- 工作流和细粒度算法必须防止重复逻辑。
- 注册和文档维护成本更高。

D. 只做 PyQt 窗口，不注册 Processing 算法

好处：
- 自定义界面自由。
- 演示效果直观。
- 初学者容易点按钮。

代价：
- 不支持模型构建器和批处理。
- 测试和复用困难。
- 不符合空间分析工具标准契约。

## 决策

选择 C：Processing 采用细粒度工具箱 + workflow 封装；工作流只做编排，不重复实现业务逻辑。

首版 Processing 算法清单：

```text
common / standardization
- validate_input_layers
- reproject_to_analysis_crs
- standardize_buildings
- standardize_roads
- standardize_pois
- standardize_elevation_points
- standardize_tracks
- write_standard_geopackage

accessibility
- calculate_road_length
- build_network_cost
- generate_facility_buffers
- calculate_nearest_facility
- calculate_service_area
- calculate_shortest_path
- calculate_facility_suitability

terrain_hydro
- extract_slope
- extract_aspect
- extract_hillshade
- extract_contours
- compare_dem_with_elevation_points
- check_saga_provider
- fill_sinks
- extract_flow_direction
- extract_flow_accumulation
- extract_stream_order
- extract_stream_network
- extract_watershed_basins
- load_hydrology_demo_results

workflow
- run_standardization_workflow
- run_accessibility_workflow
- run_terrain_workflow
- run_hydrology_workflow
```

算法命名与注册：

- Provider ID：`wuda_accessibility_analyzer`、`wuda_terrain_hydro_analyzer`。
- 算法 ID 格式：`provider_id:algorithm_name`。
- 算法 `name` 使用英文 snake_case。
- 显示名使用中文。
- 算法注册表采用 Python 常量，位于 `core/registry/algorithms.py`。
- 注册表不得 import QGIS、processing、PyQt。
- PyQt 面板、Provider 注册、测试清单、构建脚本都必须读取该注册表。

PyQt 面板：

- 默认展示四个 workflow 入口。
- 高级模式展示细粒度算法列表。
- 所有按钮只打开 QGIS Processing 原生算法窗口。
- UI 不直接执行 `processing.run()`。

已决策编号对应：

- L2-012：Processing 算法采用细粒度工具箱。
- L2-013：完整细粒度算法清单 + workflow 封装。
- L2-014：双模式 PyQt 面板。
- L2-015：PyQt 面板只打开 Processing 算法窗口。
- L2-018：插件前缀 ID + 集中算法注册表。
- L2-019：算法注册表采用 Python 常量注册表。

## 影响

Codex 不得在 Provider、UI、README 或测试中散落硬编码算法 ID。新增算法必须先更新 `core/registry/algorithms.py`，再补算法类和文档。

## 下一步方向

后续可从 Python 注册表生成 README 算法表和 release manifest 的算法摘要，但首版不要求自动生成 README。

---

# ADR-006: 输出、构建、测试、源码结构与最终交付

日期：2026-06-08
状态：已决策

## 背景

课程成果需要可安装插件包、说明文档和可复现结果。项目采用源码态单 core、发布态复制 core 到两个插件，因此必须规定源码结构、输出格式、覆盖策略、构建产物、测试和最终 Codex 交付标准。

## 备选方案

A. 只维护源码，不自动构建和测试

好处：
- 最快开工。
- 文档负担小。
- 适合个人临时脚本。

代价：
- 交付不稳定。
- 插件 zip 容易打包错。
- Codex 无法验证修改影响。

B. 源码 + 构建脚本 + 基础测试

好处：
- 构建可重复。
- 能校验核心文件。
- 适合课程项目。

代价：
- 文档仍可能不足。
- QGIS 手工验收需要另行维护。
- release 信息不完整。

C. 源码 + 构建 + 测试 + 文档 + 验收清单

好处：
- 完整交付。
- 便于 Codex 和后续 session 接手。
- 课程提交风险低。

代价：
- 工作量增加。
- 需要阶段化推进。
- 文档和测试必须随代码维护。

D. 先最小可运行，再后补文档和构建

好处：
- 最快看到插件运行。
- 便于早期演示。
- 适合时间极紧。

代价：
- 后补文档经常遗漏。
- 工程质量不可控。
- 与本项目复杂架构不匹配。

## 决策

选择 C 的最终标准，并允许按阶段交付。即 L2-042 选择 D：分阶段实现，但最终必须满足完整交付标准。

源码结构：

```text
repo/
  core/
    config/
    registry/
    standardization/
    accessibility/
    terrain/
    hydrology/
    io/
    reporting/
    qgis_processing/
  plugins/
    wuda_accessibility_analyzer/
      metadata.txt
      __init__.py
      plugin.py
      provider.py
      algorithms/
      ui/
      resources/
      README.md
      LICENSE
    wuda_terrain_hydro_analyzer/
      metadata.txt
      __init__.py
      plugin.py
      provider.py
      algorithms/
      ui/
      resources/
      demo/
      README.md
      LICENSE
  scripts/
    build_plugins.py
  tests/
    test_core/
    test_build/
  docs/
    qgis_manual_checklist.md
    user_guide.md
  data/
    demo_results/
  build/
  dist/
```

输出契约：

- 矢量结果默认输出到 GeoPackage。
- 栅格结果默认输出到 GeoTIFF。
- 每次算法运行额外生成 `run_summary.json`。
- 默认不覆盖已有文件或图层；冲突时自动追加 `_001`, `_002` 等后缀。
- `run_summary.json` 必须记录真实输出名。

构建契约：

- `scripts/build_plugins.py` 复制 `core/` 到两个插件包内部。
- 必须复制 `core/config/defaults.json`。
- 必须复制 terrain_hydro 插件 demo/sample 数据。
- 校验 `metadata.txt`、`__init__.py`、`LICENSE`、`README.md`。
- 生成：

```text
dist/
  wuda_accessibility_analyzer.zip
  wuda_terrain_hydro_analyzer.zip
  release_manifest.json
  build_report.txt
```

测试策略：

- core 单元测试覆盖 defaults 读取、字段映射、错误分级、输出后缀命名、summary 写入、manifest 写入。
- 构建校验覆盖 zip、metadata、core 复制、defaults、demo 数据、manifest。
- QGIS 手工验收覆盖插件安装、菜单出现、Provider 注册、算法窗口打开、workflow 运行、SAGA 不可用 demo 模式提示。
- 首版不强制 QGIS 自动化集成测试。

最终 Codex 交付阶段：

1. 阶段 1：`WudaAccessibilityAnalyzer` 可运行。
2. 阶段 2：`WudaTerrainHydroAnalyzer` 可运行。
3. 阶段 3：构建、测试、文档、验收清单补齐。

已决策编号对应：

- L2-003：GeoPackage/GeoTIFF 输出 + run_summary.json。
- L2-004：默认自动追加后缀，不覆盖已有结果。
- L2-016：构建脚本 + 校验清单 + release manifest。
- L2-017：core 单元测试 + 构建校验 + QGIS 手工验收清单。
- L2-020：标准分层仓库结构。
- L2-042：分阶段交付，但最终满足完整交付标准。

## 影响

Codex 不得只交付“能跑的代码”而跳过构建、测试和文档。`build/` 与 `dist/` 是构建产物，不得手工修改其中源码。

## 下一步方向

后续可增加 QGIS 自动化集成测试，但首版不要求。

---

# ADR-007: WudaAccessibilityAnalyzer 可达性与设施适宜性模型

日期：2026-06-08
状态：已决策

## 背景

可达性插件是第一阶段实现重点。它要围绕建筑、道路、POI 计算校园公共设施可达性和设施布局适宜性。用户选择了两步移动搜寻法/供需匹配模型，并要求按设施类型配置阈值和距离衰减，同时路网分析只使用 QGIS native 算法，不自建图算法。

## 备选方案

A. 简单归一化加权模型

好处：
- 实现快。
- 输入要求低。
- 报告公式易解释。

代价：
- 供需关系表达弱。
- 学术深度一般。
- 对容量和需求利用不足。

B. 网络可达性 + 加权综合评价

好处：
- 能利用路网距离、时间、覆盖、服务等级。
- 可解释性较好。
- 适合校园设施评价。

代价：
- 权重主观。
- 仍不是供需匹配模型。
- 对服务公平性表达有限。

C. 类型化 E2SFCA 供需匹配模型

好处：
- 能表达设施供给、建筑需求和服务机会。
- 方法深度更高。
- 适合公共设施布局合理性分析。

代价：
- 依赖 capacity 与 population_weight。
- 参数更多，默认值会影响结果。
- 需要明确近似策略和输出解释。

D. 完整 OD 成本矩阵版 E2SFCA

好处：
- 方法更严格。
- 可获得精确建筑—设施网络成本。
- 后续研究价值高。

代价：
- 需要自建成本矩阵或大量路径计算。
- 与“不自建网络图”的决策冲突。
- 首版性能和实现风险高。

## 决策

选择 C，并采用服务区叠置近似 E2SFCA + 最近设施校核。

模型规则：

- `calculate_facility_suitability` 采用两步移动搜寻法思想。
- 服务阈值和距离衰减权重按 `pois.service_type` 从 `defaults.json` 读取。
- capacity 缺失时使用保守默认值，必须记录。
- population_weight 缺失时默认 1.0，必须记录。
- 主流程用 QGIS native 网络服务区与建筑代表点叠置，不构建完整建筑—设施 OD 矩阵。
- 额外计算最近设施路径或成本作为校核字段。
- 输出必须说明：首版为“服务区叠置近似 E2SFCA”，不是完整 OD 矩阵版 E2SFCA。

输出图层：

```text
wuda_accessibility_results.gpkg
  accessibility_buildings
  facility_service_areas
  facility_supply_demand
  nearest_facility_links
```

`accessibility_buildings` 采用长表结构：一栋建筑 × 一个 service_type 一条记录。

核心字段：

```text
accessibility_buildings:
  building_id
  service_type
  accessibility_index
  supply_demand_ratio_sum
  reachable_facility_count
  nearest_facility_id
  nearest_facility_cost
  suitability_class
  demand_source

facility_service_areas:
  facility_id
  service_type
  band_index
  time_min
  decay_weight
  capacity
  capacity_source

facility_supply_demand:
  facility_id
  service_type
  capacity
  total_weighted_demand
  supply_demand_ratio
  reachable_building_count
  capacity_source

nearest_facility_links:
  building_id
  facility_id
  service_type
  cost_value
  cost_unit
```

适宜性等级：

- 基于 `accessibility_index` 做分位数分级。
- 默认 5 级：极低、较低、中等、较高、极高。
- 分级是相对等级，不代表绝对服务水平。

Workflow 输出：

- `run_accessibility_workflow` 默认只保留四类结果图层和 `run_summary.json`。
- 不默认保留 `cleaned_roads`、`building_representative_points`、`service_area_overlay_points` 等过程图层。
- 如需过程检查，用户运行细粒度算法。

已决策编号对应：

- L2-023：两步移动搜寻法/供需匹配模型。
- L2-024：按 service_type 配置服务阈值与距离衰减。
- L2-025：capacity 与 population_weight 缺失使用保守默认值。
- L2-026：路网分析使用 QGIS native 网络分析算法。
- L2-027：服务区叠置近似 E2SFCA + 最近设施校核。
- L2-028：输出结果图层 + 关键中间图层。
- L2-029：适宜性等级采用分位数分级。
- L2-030：建筑评价输出采用长表结构。
- L2-036：workflow 只保留最终结果。
- L2-037：网络分析调用走 network_runner 适配器。

## 影响

可达性插件结果可用于专题图和报告，但必须说明默认 capacity 和 population_weight 会影响供需匹配结果；首版不是完整 OD 矩阵版 E2SFCA。

## 下一步方向

后续可新增严格 OD 成本矩阵版 E2SFCA 或中文 POI 类型映射表，但不进入首版。

---

# ADR-008: WudaTerrainHydroAnalyzer 地形与水文分析契约

日期：2026-06-08
状态：已决策

## 背景

地形水文插件需要处理 DEM、轨迹/高程点、坡度、坡向、晕渲、等高线以及 SAGA 水文流程。用户已选择高级水文强依赖 SAGA，并在 SAGA 不可用时加载 demo/sample 结果。因此需要明确 DEM 标准化、基础地形输出、真实水文流程和 demo 输出。

## 备选方案

A. 只做基础地形分析

好处：
- 环境风险低。
- 实现快。
- 输出稳定。

代价：
- 水文功能不足。
- 与完整分析型决策不匹配。
- 指导书水文方向覆盖不够。

B. 基础地形 + 指导书 SAGA 水文流程

好处：
- 覆盖坡度、坡向、晕渲、等高线和水文。
- 与指导书 Fill Sinks、Strahler Order、Channel Network and Drainage Basins 对齐。
- 输出适合专题图和报告。

代价：
- 依赖 SAGA provider。
- DEM 质量会影响水文结果。
- 需要 demo 模式兜底。

C. 完整水文增强流程

好处：
- 可做多阈值比较和质量评价。
- 专业性更强。
- 后续研究价值高。

代价：
- 工程量过大。
- 参数解释复杂。
- 首版风险高。

D. demo 为主，真实水文暂缓

好处：
- 演示稳定。
- 不受 SAGA 环境限制。
- 体积和开发风险可控。

代价：
- 真实分析能力不足。
- 不能声称完成水文计算。
- 与用户选择的完整分析型冲突。

## 决策

选择 B：基础地形 + 指导书对齐的 SAGA 水文真实流程；SAGA 不可用时加载与真实流程同名的 demo/sample 结果。

DEM 策略：

- 标准化阶段生成 `standard_dem.tif`。
- `standard_dem.tif` 转换到 `analysis_crs`，尽量保持原始 DEM 近似地面分辨率。
- 水文分析前生成 `hydrology_dem.tif`。
- `standard_dem.tif` 用于坡度、坡向、晕渲、等高线、高程点对比。
- `hydrology_dem.tif` 用于 SAGA 水文流程。
- `dem_index` 记录原始 DEM、standard_dem、hydrology_dem 的路径、CRS、分辨率、NoData、用途说明。

基础地形输出：

```text
standard_dem.tif
slope.tif
aspect.tif
hillshade.tif
contours.gpkg
dem_elevation_comparison.gpkg
terrain_summary.json
```

字段：

```text
dem_elevation_comparison:
  point_id
  measured_elev_m
  dem_elev_m
  elev_diff_m
  abs_diff_m
  source_method
```

默认规则：

- slope 单位为 degree。
- aspect 单位为 degree。
- contours.gpkg 必须包含 `elevation_m`。
- 没有 elevation_points 时，高程对比跳过并记录 WARNING。

真实 SAGA 水文流程：

```text
1. Fill Sinks
2. Strahler Order
3. Channel Network and Drainage Basins
```

真实输出：

```text
filled_dem.tif
flow_direction.tif
flow_accumulation.tif
stream_order.gpkg 或 stream_order.tif
stream_network.gpkg
drainage_basins.gpkg
```

Demo/sample 输出：

```text
demo_filled_dem.tif
demo_flow_direction.tif
demo_flow_accumulation.tif
demo_stream_order.tif 或 demo_stream_order.gpkg
demo_stream_network.gpkg
demo_drainage_basins.gpkg
```

Demo 约束：

- 只在 SAGA 不可用或真实流程不可执行时加载。
- 图层名必须带 `demo_` 或 `sample_` 前缀。
- `run_summary.json` 必须写 `mode = "demo"`、`is_demo_result = true` 和原因。
- demo 结果不得覆盖真实分析结果。

已决策编号对应：

- L2-038：双轨 DEM 策略。
- L2-039：基础地形 + 高程校核输出。
- L2-040：SAGA 水文真实流程按指导书流程执行。
- L2-041：水文 demo/sample 结果与真实流程输出同名对应。

## 影响

地形水文插件可以在无 SAGA 环境中演示结果结构，但真实水文计算必须依赖 SAGA。报告中必须说明自动水文结果基于 DEM 提取，不等同于实测水系。

## 下一步方向

后续可新增多阈值河网敏感性分析、流域面积统计和 hydrology_quality_report，但不进入首版 Codex 任务。

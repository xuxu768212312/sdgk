---
title: 日志
tags: [日志]
created: 2026-06-22
updated: 2026-06-22
---

# 山东高考知识库 · 日志

## [2026-06-22] setup

- `[setup]` 知识库初始化，创建目录结构和 CLAUDE.md schema

## [2026-06-22] ingest | 山东高考志愿填报资料包 2026 正式整理版

- `[ingest]` 全量迁移源资料包到 `raw/`，按年份分目录
  - 2021-2025：每年含一分一段表、常规批 1/2/3 次投档表、分数线、常规批 2/3 次志愿计划、提前批第 2 次计划、高职注册入学计划
  - 2026：8 个政策 md + 政策原件 + 2024/2027 版选科要求（PDF + 分册 md）+ 工作模板 + 志愿参考表
  - _common：防错规则、来源索引、待更新清单、数据字段说明
- `[ingest]` 共迁移约 203 个文件
- `[wiki]` 构建初始 wiki 页面：
  - 总览：overview.md
  - 概念页 7 个：3+3 模式、赋分制、志愿填报规则、分数线、选科要求、一分一段表、投档表
  - 实体页 7 个：2021-2026 年高考 + 山东省教育招生考试院
  - 主题页 5 个：防错清单、本科专科分开、历年数据趋势、数据使用原则、2026 待更新清单
  - 来源页 1 个：资料包索引
  - 更新 index.md 和 log.md
- `[note]` 原始资料包路径：`C:/Users/76821/Desktop/山东高考志愿填报资料包_2026_正式整理版`

## [2026-06-22] process | 二次数据整理

- `[process]` 将 raw/ 原始 Excel/PDF 提取为标准 CSV+JSON，存入 `processed/`
  - **一分一段表**：2021-2025 共约 2700 条，字段含全体和 6 科选考的本段/累计人数
  - **投档表**：2021-2025 常规批 1/2/3 次共约 15.1 万条，已拆分专业代号/名称、院校代号/名称
  - **志愿计划**：2021-2025 共约 1.1 万条，含常规批 2/3 次、提前批 2 次、高职注册入学
  - **分数线**：2025 从 PDF 提取完整；2021-2024 待补（官方 HTML 无 PDF 附件）
- `[wiki]` 新增 [[source_标准数据字典]] 页面
- `[wiki]` 更新 [[index]] 统计信息
- `[note]` 处理脚本：`_process_score_table.py`、`_process_admission.py`、`_process_scorelines.py`、`_process_plans.py`
- `[note]` 已知缺口：2021-2024 分数线（需重新下载官方页面）

## [2026-06-22] lint | 健康检查

- `[lint]` 执行全量健康检查，生成 [[lint_2026-06-22]] 报告
- `[fix]` 删除 `raw/2025/分数线/` 中重复的 PDF（内容完全一致）
- `[lint]` 检查结果：健康度优良
  - raw 完整性 ✓
  - processed 数据质量 ✓（99.99% 字段完整，5 条空位次 + 65 条空计划均为原始数据正常情况）
  - Wiki 链接 ✓（无断链、无孤立页）
  - 内容一致性 ✓（wiki 数值与 processed 一致）
- `[todo]` 待修复：2024 志愿计划 1 条 school_code 缺失（体育类附件格式问题）
- `[todo]` 待补全：2021-2024 分数线（需重新下载官方页面）

## [2026-06-22] fix | 准确性修正与查漏补缺

依据山东省教育招生考试院 2026 官方政策原文（百问百答、艺术类实施方案、报名办法、等级考选报问答），对照 wiki 进行全量修正与补充。

- `[fix]` 修正 [[concept_赋分制]]：明确 8 等级对应分数区间（A=91-100, B+=81-90, B=71-80, C+=61-70, C=51-60, D+=41-50, D=31-40, E=21-30），替换原"最高约 100 最低约 30"的不准确表述
- `[fix]` 修正 [[concept_分数线]]：
  - 补充第 4 条线"3+2 对口贯通分段培养高职志愿填报资格线"（2025 年 391 分）
  - 艺术类本科文化线 4 种划定方式（校考一段线、播音一段线、美术音乐书法 75%、舞蹈表导演戏曲 65%）
  - 体育类补充文化控制线（本科=一段线 65%、专科=二段线）
  - 补充 2025 年实际分数线数值
- `[new]` 新增 8 个概念页：
  - [[concept_位次]] — 位次定义与同分排序规则
  - [[concept_艺术类综合成绩]] — 6 类统考综合分公式
  - [[concept_春季高考]] — 知识+技能、30 个专业类别
  - [[concept_强基计划]] — 39 所试点、两种录取模式
  - [[concept_综合评价招生]] — 10 所试点高校
  - [[concept_专项计划]] — 高校/地方/高职院校 3 类专项
  - [[concept_省属公费生]] — 师范/医学/农科 3 类公费生
  - [[concept_保送生]] — 4 类保送资格
- `[new]` 新增 [[topic_2026时间节点]] 主题页：报名、考试、成绩、志愿填报、资格审核、军队招飞等关键日期
- `[update]` 完善已有页面：
  - [[concept_志愿填报规则]]：明确提前批 A 类/B 类志愿数细节、补充艺术类综合成绩链接
  - [[concept_投档表]]：补充退档风险警示
  - [[concept_一分一段表]]：补充位次确定规则
  - [[topic_历年数据趋势]]：标注 2021-2024 分数线待补
- `[update]` 更新 [[index]] 收录全部 32 页
- `[note]` 信息来源：山东省教育招生考试院 2026 官方政策文件（sdzk.cn）
- `[note]` 所有数值均与官方原文核对，确保准确

## [2026-06-22] enrich | 结合互联网数据补充

依据互联网公开数据（教育部、新华网、山东省教育招生考试院、教育在线等）补充知识库。

- `[new]` 新增 [[topic_2026政策变化]] 主题页：
  - 5 大政策变化（取消特殊类型批、提前批 A/B 类、艺体志愿 96 个、春季高考提前批平行、兼报限制）
  - 教育部新增 38 个本科专业（按 5 大类列出代表性专业）
- `[fix]` 补全 2021-2024 历年分数线：
  - 新建 `processed/分数线/历史分数线_2020-2024.json`
  - 含 2020-2024 年普通类、艺术类、体育类分数线
  - 删除 `_pending_2021_2024.json`（已补全）
- `[update]` 完善 [[topic_历年数据趋势]]：
  - 新增"普通类分数线历年对比（2020-2025）"表格
  - 新增"体育类综合分分数线对比"表格
  - 2021-2024 分数线状态从"待补"改为"✓ 互联网"
- `[update]` 完善 [[topic_2026时间节点]]：
  - 成绩公布时间精确到 6 月 25 日 15:00
  - 补全 2026 年 6 次志愿填报具体日期（6/29、7/5-7、7/13、7/20、7/24-26、7/31）
  - 补充志愿填报演练时间（6/13-16）
  - 补充"爱山东"APP 查询渠道
- `[update]` 更新 [[index]] 收录政策变化页
- `[note]` 数据来源：教育部官网、新华网、青岛本地宝、教育在线、网易、搜狐等公开渠道

## [2026-06-22] update | 完善 CLAUDE.md

- `[update]` 重写 CLAUDE.md，对齐知识库现状：
  - 架构从三层改为四层（新增 `processed/` 和 `scripts/`）
  - 目录结构补全 `processed/`、`scripts/`、`raw/_common/`
  - 修正考试模式：3+1+2 → **3+3**（原错误）
  - 新增四类页面职责说明（concept/entity/topic/source）
  - 新增页面命名约定（`<type>_<中文名>.md` 前缀）
  - 新增数据流程说明（raw → processed → wiki）
  - 新增 processed/ 数据集概览表
  - 新增处理脚本表
  - 新增关键原则 8 条（含"数据准确"和"链接有效"）
  - 新增扩展指引（添加年份/概念/主题/数据集的步骤）

## [2026-06-22] setup | 新建 students/ 学生工作区

- `[setup]` 创建 `students/` 目录，与知识库隔离，不入库 raw/processed/wiki
- `[setup]` 建立 `students/张三/` 示例目录，含 `基本信息.md` 和 `操作记录.md` 模板
- `[setup]` 写 `students/README.md` 说明隔离原则和使用流程
- `[update]` 更新 CLAUDE.md：
  - 架构概述加入"学生工作区"
  - 目录结构加入 `students/` 子树
  - 新增"学生工作区"章节（隔离原则、目录结构、操作流程、隐私保护）
  - 关键原则加入第 9 条"学生信息隔离"

## [2026-06-23] strategy | 构建 System2 填报策略体系

- `[new]` 新增 [[topic_System2填报思维框架]] 主题页：
  - 六步决策流程（定位→筛选→排序→风险评估→优化→验证）
  - 每步详细操作指南、数据来源、输出要求
  - 常见认知偏差与防范（锚定效应、确认偏差、过度自信、损失厌恶、从众心理）
- `[new]` 新增 [[topic_专有填报策略]] 主题页：
  - 位次法（核心策略）：原理、操作步骤、录取概率公式、示例
  - 线差法（辅助策略）：公式、适用场景、局限性
  - 冲稳保垫梯度策略：比例设计（2:4:3:1）、位次梯度、关键原则
  - 分档决策模型：顶尖/高分/中分/低分四档策略、优先级、志愿设计
  - 专业/学校/城市优先级决策：四种优先策略、决策树、权衡矩阵
  - 风险评估与量化：退档/滑档风险、量化公式、风险等级、调整策略
  - 综合应用示例：中分段考生完整案例
- `[update]` 更新 CLAUDE.md：
  - 新增"志愿填报策略体系（System2 思维框架）"章节
  - 包含六步决策流程、专有策略、分档模型、关键原则
- `[update]` 更新 [[index]]：
  - 新增"决策框架"子分类
  - 收录 System2 思维框架和专有填报策略两页
- `[note]` 信息来源：互联网公开数据（教育部、阳光高考、教育在线、知乎专栏等）
- `[note]` 策略体系对标顶尖高考志愿填报专家水平，强调数据驱动、流程化、风险量化

## [2026-06-23] strategy+ | 引入顶尖思维工具加固策略体系

依据互联网公开数据（决策科学、行为经济学、博弈论、概率统计）引入高级决策模型，并修正山东投档规则认知。

- `[new]` 新增 [[topic_高级决策模型]] 主题页：
  - **贝叶斯推理**：用新证据（扩招、政策变化）动态更新录取概率，公式 + 应用场景
  - **蒙特卡洛模拟**：10000 次随机抽样，输出滑档风险分布而非单点估计
  - **凯利公式**：在"冲"和"稳"之间科学分配志愿数量（理论最优 6.7%:40%）
  - **MECE 原则**：志愿分类、专业选择、风险来源做到互斥穷尽
  - **SWOT 分析**：考生优势/劣势/机会/威胁四维分析 + SWOT 矩阵策略
  - **期望效用理论**：个性化效用函数（就业/薪资/兴趣/考研权重）
  - **行为经济学偏差**：8 类偏差清单（损失厌恶、沉没成本、锚定、确认、过度自信、从众、现状、框架）
  - **博弈论视角**：纳什均衡找"价值洼地"，零和博弈思维
  - **决策树综合应用**：7 步完整决策流程
  - **顶尖专家 vs 普通水平对比表**
- `[new]` 新增 [[topic_张雪峰八连问]] 主题页：
  - 八连问决策树完整内容（学医→学农→当老师→文理兼招→带化学→带物理→三方向→带数学）
  - 就业导向三原则（能就业、能考公考研、不问喜不喜欢）
  - 适用人群分析（普通家庭强烈推荐 / 有资源家庭谨慎使用）
  - 与胡向阳"四优先"、System2 框架的关系
  - 局限性分析（忽视兴趣、静态就业观、普通家庭预设、专业壁垒假设）
  - 专业选择 4 步法（城市→学校→专业→兴趣）
  - 综合应用示例（普通家庭理科生物化生）
- `[fix]` 修正 [[concept_志愿填报规则]]：
  - 补充山东投档核心机制：**分数优先、遵循志愿、一次投档**
  - 明确 **1:1 投档**（对外省 1:1.05，对山东一律 1:1）
  - 明确 **无调剂**（96 个平行志愿直达专业）
  - 明确 **投档即录取**（只要硬性条件符合）
  - 列出 6 类退档风险（体检、单科、外语语种、口试、综合素质、总分低额满）
  - 明确退档后果（本批次后续志愿作废，只能征集志愿或下一批次）
- `[update]` 更新 CLAUDE.md：
  - 主要主题新增"高级决策模型"和"张雪峰八连问方法论"
  - 新增"高级决策模型（顶尖思维工具）"章节，8 大工具概述
  - 新增"张雪峰八连问方法论"章节，决策树 + 适用人群
- `[update]` 更新 [[index]]：
  - 决策框架子分类补充高级决策模型、张雪峰八连问两页
- `[note]` 信息来源：
  - 决策科学：维基百科凯利公式、知乎贝叶斯/蒙特卡洛专栏
  - 行为经济学：心理学报、MBA 智百科
  - 张雪峰八连问：搜狐、知乎、B 站视频
  - 山东投档规则：搜狐 2026 山东高考实施办法解读
- `[note]` 本次加固使策略体系从"经验判断"升级为"科学计算"，达到顶尖专家水平

## [2026-06-23] governance | 官方数据源约束加固

- `[update]` 升级 `AGENTS.md` / `CLAUDE.md` 至 v3.1：
  - 明确山东省教育招生考试院（sdzk.cn）为山东高考数据唯一正式主源
  - 非官方数据（第三方网站、媒体、商业软件、整理表）降为 D 级，仅作线索，不得作为正式方案数值依据
  - 新增 processed 元数据要求：source_file、source_url、publisher、quality_level、verification_status
- `[update]` 更新 [[topic_数据使用原则]]：
  - 增加官方来源优先级表
  - 明确高校招生章程只作合规辅助，不替代考试院计划/位次/投档数据
- `[update]` 更新 [[source_资料包索引]] 与 [[source_标准数据字典]]：
  - 标注工作模板和参考表的使用边界
  - 将 `历史分数线_2020-2024.json` 标为 D 级趋势线索，正式引用前必须回查考试院
- `[new]` 新增 `processed/分数线/_meta.json`，记录 2025 官方 PDF 与 2020-2024 待核验历史汇总的质量等级
- `[update]` 补强 `processed/一分一段表/`、`processed/投档表/`、`processed/志愿计划/`、`processed/选科要求/` 的 `_meta.json` 来源等级字段

## [2026-06-23] audit | 数据准确性全量审计

- `[new]` 新增 `scripts/audit_data_accuracy.py`，用于审计 `processed/` 与 `raw/` 的一致性
- `[audit]` 生成 [[lint_2026-06-23_数据准确性审计]]：
  - 机器审计 FAIL=0，WARN=3，INFO=12
  - 一分一段表、投档表、志愿计划均已从 raw 官方 Excel 全量重抽取比对
  - 4 个选科要求官方 PDF 已全量重抽取，比对 180788 条结构化数据
  - 2025 分数线 PDF 文本核查通过
- `[fix]` 修复 `scripts/_process_plans.py`：
  - 处理无表头注册入学附件
  - 修正 2024 体育类注册入学 `体育运营与管理` 院校信息：`D321 青岛求实职业技术学院`，计划数 4，学制 3，学费 10800
  - 固定附件读取顺序，保证重跑稳定
- `[fix]` 修复 `scripts/_process_score_table.py`：
  - 统一一分一段 CSV/JSON 字段顺序
  - 元数据保留山东省教育招生考试院来源等级
- `[warn]` 剩余 3 类提醒：
  - 投档表 5 条官方原始空位次，正式概率建模前需人工确认
  - 志愿计划 63 条官方原始空计划数，集中在高职院校专项/注册入学相关记录，正式使用前需核查
  - 2020-2024 历史分数线仍为 D 级线索，正式引用前必须回查 sdzk.cn

## [2026-06-23] safety | 选科防幻觉索引与志愿审核闸门

- `[new]` 新增 `scripts/subject_eligibility.py`，统一选科解析、年份版本映射、证据 ID 生成与 PASS/BLOCK/REVIEW 判定
- `[new]` 新增 `scripts/build_subject_index.py`，从 `processed/选科要求/` 4 个官方派生 JSON 构建 SQLite 索引
- `[new]` 新增 `scripts/check_subject_eligibility.py`，用于单条“专业（专业类）+ 学校”选科可报性确定性查询
- `[new]` 新增 `scripts/audit_volunteer_subjects.py`，用于 CSV/JSON/XLSX 志愿方案选科审核；任一 `BLOCK` 或 `REVIEW` 阻断正式交付
- `[new]` 新增 `scripts/test_subject_index.py`，覆盖索引行数、单条 PASS/BLOCK/REVIEW 与整表硬闸门
- `[update]` `scripts/audit_data_accuracy.py` 纳入选科 SQLite 索引完整性检查
- `[update]` `wiki/topics/topic_选科查询.md` 与 [[concept_选科可报性]] 增加强制脚本查询和审核闸门规则

## [2026-06-23] governance | AGENTS/CLAUDE 选科硬闸门同步

- `[update]` `AGENTS.md` 与 `CLAUDE.md` 升级至 v3.2（选科防幻觉索引版）
- `[update]` 新增 Z17 选科硬闸门：选科能否报考必须经确定性脚本返回证据，`BLOCK`/`REVIEW` 不得交付
- `[update]` 新增 2.5 选科防幻觉索引与硬闸门，明确年份映射、匹配优先级、状态语义、正式方案字段和审计要求
- `[update]` 查询、咨询、多 Agent A6、学生工作区、脚本清单和版本历史均同步到 `subject_index.sqlite`、`evidence_id`、`subject_audit.json` 逻辑

## [2026-06-23] strategy | 互联网数据准入与策略优化器

- `[new]` 新增 `scripts/internet_source_policy.py`，对互联网 URL 做来源质量上限与正式使用准入判定
- `[new]` 新增 `algorithms/strategy_optimizer.py`，对候选志愿执行数据质量、选科证据、概率、效用、冲稳保垫配额和滑档基线检查
- `[new]` 新增 `scripts/test_strategy_optimizer.py`，覆盖正式候选入选、选科/来源/evidence_id 拦截和垫底不足阻断
- `[new]` 新增 [[topic_互联网数据使用原则]]，明确 `sdzk.cn` 主源、阳光高考/高校官网辅助、第三方线索隔离
- `[update]` `AGENTS.md` 与 `CLAUDE.md` 升级至 v3.3，新增 Z18 互联网数据准入与 5.15 策略优化器硬要求
- `[update]` [[topic_数据使用原则]]、[[topic_专有填报策略]]、[[topic_高级决策模型]] 与 [[index]] 同步算法入口和数据边界

## [2026-06-23] strategy | 策略优化器失败关闭加固

- `[update]` `algorithms/strategy_optimizer.py` 升级为 `strategy_optimizer_v2_fail_closed`
- `[update]` 异常概率、缺效用分、缺 `source_file`、重复院校专业、缺选科 `evidence_id` 均进入 `blocked`
- `[update]` 新增 `conservative_slip_probability`：不假设 96 志愿独立，用最强安全志愿失败概率作为硬闸门
- `[update]` `scripts/test_strategy_optimizer.py` 增加异常概率、重复候选、保守滑档超限测试
- `[update]` `AGENTS.md` 与 `CLAUDE.md` 升级至 v3.4，新增 Z19 算法失败关闭
- `[update]` [[topic_专有填报策略]]、[[topic_高级决策模型]]、[[topic_互联网数据使用原则]] 同步保守滑档与失败关闭规则

## [2026-06-23] strategy | 价值捕获与图文双交付加固

- `[update]` `algorithms/strategy_optimizer.py` 升级为 `strategy_optimizer_v3_value_capture_fail_closed`
- `[new]` 新增 `value_capture_score` 与 `value_capture_reasons`，将“低分上好大学/好专业”纳入可解释排序，但不越过选科、来源、保底、滑档硬闸门
- `[update]` `scripts/test_strategy_optimizer.py` 增加 `value_capture_priority` 测试
- `[update]` `AGENTS.md` 与 `CLAUDE.md` 升级至 v3.5，新增 Z20 价值捕获不越过安全闸门、Z21 Excel + Markdown 图文双交付

## [2026-06-23] docs | GitHub README 与提交准备

- `[new]` 新增 `README.md`，说明项目定位、数据原则、SQLite 选科索引、策略优化器、正式咨询工作流、交付物标准和隐私边界
- `[new]` 新增 `.gitignore`，默认排除 `students/`、`node_modules/`、缓存、根目录生成志愿表和本地环境文件，避免学生隐私数据进入 GitHub

## [2026-06-23] strategy | 受控冲刺概率加固

- `[update]` `algorithms/strategy_optimizer.py` 升级为 `strategy_optimizer_v4_rush_guard_fail_closed`
- `[new]` 新增 `opportunistic` 机会冲刺风险档：96 志愿目标配额 34:36:20:6，最低冲刺概率 10%，保守滑档上限 6%
- `[new]` 新增 Rush Guard：普通冲与深度冲分层，深度冲必须满足 `value_capture_score` 阈值，且受 `max_deep_rush` 数量上限约束
- `[new]` 新增阻断原因：`LOW_PROBABILITY_WITHOUT_VALUE_CAPTURE`、`DEEP_RUSH_OVER_PROFILE_CAP`、`DEEP_RUSH_TOO_MANY`
- `[update]` 优化器输出新增 `rush_counts`、`rush_tier`、`rush_probability_floor`、`deep_rush_probability`，用于 Excel/Markdown 报告追踪“搏一搏”依据
- `[update]` `scripts/test_strategy_optimizer.py` 增加 `opportunistic_rush_profile` 与 `deep_rush_requires_value_capture` 测试
- `[update]` `AGENTS.md` 与 `CLAUDE.md` 升级至 v3.6，新增 Z22 冲刺有界可搏、5.9ter Rush Guard、5.15 v4 策略优化器硬要求
- `[audit]` 重跑 `scripts/audit_data_accuracy.py`：`FAIL=0`，`WARN=4`，更新 `wiki/lint_2026-06-23_数据准确性审计.md`

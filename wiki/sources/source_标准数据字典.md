---
title: 标准数据字典
tags: [数据字典, processed, AI可读]
created: 2026-06-22
updated: 2026-06-24
sources: ["processed/"]
---

# 标准数据字典

本页索引 `processed/` 目录下的标准化数据集。所有数据均为 **CSV + JSON 双格式**，AI 可直接读取。

## 数据集概览

| 数据集 | 位置 | 年份 | 数据量 | 状态 |
|---|---|---|---|---|
| 一分一段表 | `processed/一分一段表/` | 2021-2025 | 约 2700 条 | ✓ 完整 |
| 投档表（常规批 1/2/3 次） | `processed/投档表/` | 2021-2025 | 约 15.1 万条 | ✓ 完整 |
| 分数线 | `processed/分数线/` | 2020-2025 | 6 年 | 2025 为考试院 PDF 提取；2020-2024 为待官方回查的历史汇总 |
| 志愿计划 | `processed/志愿计划/` | 2021-2025 | 约 1.1 万条 | ✓ 完整 |
| 选科要求 | `processed/选科要求/` | 2024/2027 版 | 约 18.1 万条 | ✓ 完整 |
| 院校地区 | `processed/院校地区/` | 2024/2027 版派生 | 2534 所院校 | ✓ 省份完整；城市不确定返回 REVIEW |

## 数据集详情

### 一分一段表

**位置**：`processed/一分一段表/<year>.csv|json` + `all_years.json`

**字段**：year, score, total_count, total_cumulative, {subject}_count, {subject}_cumulative

**6 科**：physics, chemistry, biology, politics, history, geography

**用途**：分数 ↔ 位次双向转换

详见 `processed/README.md`。

### 投档表

**位置**：`processed/投档表/<year>_round<n>.csv|json` + `all_years_all_rounds.json`

**字段**：year, round, major_code, major_name, school_code, school_name, plan_count, min_rank

**round 含义**：
- 1 = 第 1 次志愿（本科计划）
- 2 = 第 2 次志愿（剩余本科+专科）
- 3 = 第 3 次志愿（剩余计划）

**代号拆分**：
- major_code：开头 1-3 位字母数字
- school_code：字母+3-4 位数字（如 A001, Y030）

### 分数线

**位置**：`processed/分数线/2025.json`、`processed/分数线/历史分数线_2020-2024.json`

**2025 完整数据**：普通类（特殊类型 521、一段 441、二段 150、3+2 资格 391）、艺术类、体育类

**2020-2024 历史汇总**：`历史分数线_2020-2024.json` 当前标注为互联网公开数据整理，质量等级 D，仅用于趋势线索；正式方案引用前必须回查山东省教育招生考试院对应年度页面或原始公告，并升级元数据质量等级。

### 志愿计划

**位置**：`processed/志愿计划/<year>.csv|json` + `all_years_all_batches.json`

**字段**：year, batch, category, school_code, school_name, major_code, major_name, subject_requirement, level, study_years, plan_count, annual_fee

**batch 取值**：
- 常规批第2次（剩余本科计划）
- 常规批第3次（剩余计划含专科）
- 提前批第2次（第1次未完成的提前批）
- 高职注册入学

**category 取值**：普通类、艺术类、体育类、春季高考

### 院校地区

**位置**：`processed/院校地区/school_region_index.sqlite`

**来源**：由 `processed/选科要求/*.json` 的 `school_name`、`school_code`、`province` 字段派生。

**用途**：
- 省份偏好：用 `province` 精确判断，如“山东的学校”不再依赖学校名是否包含“山东”。
- 城市偏好：用 `city`、`city_aliases` 和 reviewed override 判断；多校区或不确定返回 `REVIEW`。
- 正式候选池：地区硬约束只允许 `MATCH`，`REVIEW` 进入人工复核清单。

**查询入口**：

```bash
python scripts/check_school_region.py --regions 山东,苏州 --school-name 青岛大学 --json
```

## 使用示例

### Python 查询

```python
import json

# 1. 分数 → 位次
data = json.load(open("processed/一分一段表/2025.json", encoding='utf-8'))
score_to_rank = {r['score']: r['total_cumulative'] for r in data}
print(f"441 分位次：{score_to_rank[441]}")

# 2. 学校专业 → 投档位次
data = json.load(open("processed/投档表/2025_round1.json", encoding='utf-8'))
pku = [r for r in data if r['school_code'] == 'A001']
for r in pku:
    print(f"{r['major_name']}：位次 {r['min_rank']}")

# 3. 剩余本科计划
data = json.load(open("processed/志愿计划/2025.json", encoding='utf-8'))
r2 = [r for r in data if r['batch'] == '常规批第2次']
print(f"2025 常规批第2次剩余本科计划：{len(r2)} 条")
```

### AI 直接读取

LLM 可直接读 JSON 文件，无需额外解析。对于大文件（如投档表 all_years_all_rounds.json 约 78MB），建议按年份/批次单独读取。

## 数据质量

### 来源等级要求

- 正式志愿方案只使用 S/A/B 级数据：山东省教育招生考试院官方原文/附件或由其生成的 processed 数据。
- 高校招生章程、教育部阳光高考等官方渠道只作合规辅助。
- 第三方网站、媒体、商业软件、非官方整理表为 D 级，只能作线索，不能作为正式方案数值依据。

### 完整性

- 一分一段表：5 年全部完整，字段统一
- 投档表：5 年 × 3 次全部完整，已处理 4 列/5 列差异、表头措辞差异、2021 第3次附件顺序颠倒
- 志愿计划：5 年 × 4 类批次全部完整
- 分数线：2025 为考试院 PDF 提取；2020-2024 已有历史汇总但需考试院回查后才能作正式决策依据
- 选科要求：2024 版与 2027 版本/专科均已结构化

### 已知问题

1. **2020-2024 分数线质量等级待升级**：当前历史汇总来自互联网公开资料，需回查考试院页面/公告后升级为 B 级或以上
2. **major_name 含备注**：志愿计划的专业名称包含校区、中外合作、单科要求等备注信息，未进一步拆分
3. **体育类投档表未纳入**：投档表数据集仅含普通类，体育类需单独处理
4. **processed 元数据需补强**：后续 `_meta.json` 应统一加入 source_url、publisher、quality_level、verification_status 字段

## 相关页面

- [[source_资料包索引]] — 原始资料来源
- [[concept_一分一段表]] — 一分一段表概念
- [[concept_投档表]] — 投档表概念
- [[concept_分数线]] — 分数线体系
- [[topic_数据使用原则]] — 数据使用边界

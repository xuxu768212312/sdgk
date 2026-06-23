---
title: 选科查询方法与示例
tags: [选科, 查询, 示例, 防幻觉]
created: 2026-06-23
updated: 2026-06-23
sources: ["processed/选科要求/", "raw/2026/政策文件原件/"]
---

# 选科查询方法与示例

本页提供选科查询的 **具体操作方法**，所有方法均基于 `processed/选科要求/` 标准数据，避免凭印象判断。

## 强制防幻觉流程

正式回答“某考生能否报某专业”或交付 96 志愿方案前，必须先跑确定性脚本，不能直接凭上下文或人工筛选结论判断。

### 单条查询

```bash
python scripts/check_subject_eligibility.py \
  --year 2026 \
  --level 本科 \
  --subjects 物理,化学,生物 \
  --school-code 10001 \
  --major-code 080101 \
  --json
```

输出必须读取以下字段：

| 字段 | 含义 |
|---|---|
| `status` | `PASS` / `BLOCK` / `REVIEW` |
| `eligible` | 是否可报；`REVIEW` 时为 `null` |
| `reason_code` | 判定原因 |
| `match_type` | 命中方式，优先代码精确命中 |
| `evidence_id` | 选科证据 ID |
| `source_file` | 证据来源 processed 文件 |

### 96 志愿审核闸门

```bash
python scripts/audit_volunteer_subjects.py \
  --input students/某考生/志愿方案/96志愿.xlsx \
  --year 2026 \
  --level 本科 \
  --subjects 物理,化学,生物 \
  --out students/某考生/志愿方案/选科审核报告.json
```

闸门规则：

- 所有志愿必须是 `PASS` 才能交付。
- 任一志愿为 `BLOCK` 或 `REVIEW`，正式方案不得交付。
- `REVIEW` 不能口头解释为“应该可以报”，必须人工回查官方原文或当年招生计划。
- 最终志愿表必须保留 `subject_check_status`、`evidence_id`、`source_file`。

## 数据准备

### 数据集

| 文件 | 版本 | 层次 | 条数 |
|---|---|---|---|
| `processed/选科要求/2024版本科.json` | 2024（适用 2025-2026） | 本科 | 50915 |
| `processed/选科要求/2024版专科.json` | 2024（适用 2025-2026） | 专科 | 39950 |
| `processed/选科要求/2027版本科.json` | 2027（2027 起） | 本科 | 52558 |
| `processed/选科要求/2027版专科.json` | 2027（2027 起） | 专科 | 37365 |
| `processed/选科要求/all_requirements.json` | 全部合并 | 全部 | 180788 |

**2026 届使用 2024 版**，不要混用 2027 版。

### 字段说明

```yaml
edition: 2024 / 2027
level: 本科 / 专科
school_code: 院校代码（5 位数字，如 10001）
school_name: 院校名称（如 北京大学）
major_code: 专业代码（如 0015）
major_name: 专业名称（含括号说明）
subject_requirement_raw: 原始文本（如 "物理,化学(2门科目考生均须选考方可报考)"）
subject_requirement_type: none / one / two / three / any
subjects_list: 科目中文名列表，用 | 分隔（如 "物理|化学"）
province: 院校所在省份
```

**5 种类型说明**：

| type | 含义 | 示例 |
|---|---|---|
| `none` | 不提科目要求 | 任何组合可报 |
| `one` | 1 门必须选考 | `思想政治` |
| `two` | 2 门均须选考 | `物理\|化学` |
| `three` | 3 门均须选考 | `物理\|化学\|生物` |
| `any` | 多门任选 1 门（"或"关系） | `物理\|化学\|生物` |

## 查询场景

### 场景 1：查某选科组合能报的专业总数

**问题**：张三选了物理+化学+生物，能报多少个本科专业？

```python
import json

data = json.load(open("processed/选科要求/2024版本科.json", encoding='utf-8'))
my_subjects = {'物理', '化学', '生物'}

def can_apply(rec):
    req_type = rec['subject_requirement_type']
    if req_type == 'none':
        return True
    required = set(rec['subjects_list'].split('|')) if rec['subjects_list'] else set()
    if not required:
        return True
    if req_type in ('one', 'two', 'three'):
        # "且"关系：必须全部含
        return required.issubset(my_subjects)
    if req_type == 'any':
        # "或"关系：含其中任一门即可
        return bool(required & my_subjects)
    return False

applicable = [r for r in data if can_apply(r)]
print(f"张三可报本科专业: {len(applicable)} / {len(data)}")
print(f"覆盖率: {len(applicable)/len(data)*100:.1f}%")
```

### 场景 2：查某组合能报哪些学校

```python
schools = set(r['school_name'] for r in applicable)
print(f"可报学校数: {len(schools)}")
# 前 20 所
for s in sorted(schools)[:20]:
    print(f"  {s}")
```

### 场景 3：查某学校所有可报专业

```python
target_school = '山东大学'
sd_majors = [r for r in data if r['school_name'] == target_school and can_apply(r)]
print(f"{target_school}: 可报 {len(sd_majors)} 个专业")
for r in sd_majors[:10]:
    print(f"  {r['major_code']} {r['major_name'][:50]}")
```

### 场景 4：查某专业能否报

```python
# 张三能否报临床医学
target = '临床医学'
clinical = [r for r in data if target in r['major_name']]
for r in clinical[:10]:
    can = can_apply(r)
    print(f"{r['school_name']} {r['major_name'][:40]}: {'✓' if can else '✗'} 要求={r['subjects_list'] or '不限'}")
```

### 场景 5：查某专业在哪些学校开设

```python
target = '计算机科学与技术'
cs = [r for r in data if r['major_name'] == target]
print(f"开设计算机科学与技术的学校: {len(cs)} 所")
for r in cs[:10]:
    can = can_apply(r)
    print(f"  {r['school_name']} ({r['province']}): {'✓' if can else '✗'} 要求={r['subjects_list'] or '不限'}")
```

### 场景 6：比较不同选科组合的覆盖率

```python
import itertools

subjects = ['物理', '化学', '生物', '政治', '历史', '地理']
combos = list(itertools.combinations(subjects, 3))

results = []
for combo in combos:
    my_subjects = set(combo)
    count = sum(1 for r in data if can_apply(r))
    rate = count / len(data) * 100
    results.append((combo, count, rate))

# 按覆盖率排序
results.sort(key=lambda x: -x[2])
print("选科组合覆盖率排名（2024 版本科）:")
for i, (combo, count, rate) in enumerate(results, 1):
    print(f"  {i:2d}. {'+'.join(combo):12s} {rate:5.1f}%  ({count} 个专业)")
```

### 场景 7：查选科要求最严的专业

```python
# 要求 3 门科目的专业
three_req = [r for r in data if r['subject_requirement_type'] == 'three']
print(f"要求 3 门科目均须选考的专业: {len(three_req)}")
for r in three_req[:10]:
    print(f"  {r['school_name']} {r['major_name'][:40]} 要求={r['subjects_list']}")
```

### 场景 8：按省份查询

```python
# 查山东省内所有本科院校
sd_schools = [r for r in data if r['province'] == '山东']
print(f"山东省内本科院校专业: {len(sd_schools)}")
sd_school_names = set(r['school_name'] for r in sd_schools)
print(f"山东省内本科院校数: {len(sd_school_names)}")
for s in sorted(sd_school_names):
    print(f"  {s}")
```

## 常见误区（防幻觉）

### 误区 1：凭印象判断专业能否报

❌ **错误**："物化生能报所有专业"

✓ **正确**：查数据。某些专业（如小语种、艺术类）即使物化生组合也可能有特殊要求。

### 误区 2：跨版本混用

❌ **错误**：用 2027 版选科要求判断 2026 届

✓ **正确**：2026 届用 2024 版，2027 届起用 2027 版。

### 误区 3：专业名相同则要求相同

❌ **错误**："临床医学专业都要求物化生"

✓ **正确**：不同学校同一专业名要求可能不同。必须按 school_code + major_code 精确查询。

### 误区 4：大类招生包含所有子专业

❌ **错误**：报了"工商管理类"就能分流到任何子专业

✓ **正确**：大类招生的子专业分流可能有额外要求，需查招生章程。

### 误区 5：选科要求就是最终门槛

❌ **错误**：选科符合就能录取

✓ **正确**：选科只是初筛，还需体检、单科成绩、外语语种、口试、面试等多重核查。

## 数据更新

### 2026 届流程

1. 使用 2024 版选科要求初筛
2. 等 2026 年《填报志愿指南》发布后，核对当年招生计划的选科要求
3. 最终以官方计划为准

### 2027 届及以后

使用 2027 版选科要求。2027 版部分专业要求有调整（如更多专业要求物化）。

## 相关页面

- [[concept_选科要求]] — 5 种类型说明
- [[concept_3+3模式]] — 选科机制
- [[source_标准数据字典]] — 数据字段
- [[topic_防错清单]] — 选科是第一道筛选

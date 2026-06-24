# processed/ 数据字典

本目录存放从 `raw/` 原始 Excel/PDF 提取的标准化数据，格式为 **CSV + JSON 双格式**，AI 可直接读取。正式志愿方案只能使用山东省教育招生考试院（`sdzk.cn`）官方原文/附件或由其生成的数据；非官方补充数据仅作线索。

## 官方来源要求

| 等级 | 来源 | 用途 |
|---|---|---|
| S/A | 山东省教育招生考试院官方原文/附件 + 脚本生成 | 正式决策依据 |
| B | 山东省教育招生考试院页面截图/HTML/图片 + 人工或 OCR 核对 | 临时决策依据，需标注 |
| C | 高校招生章程、教育部阳光高考等官方渠道 | 合规辅助 |
| D | 第三方网站、媒体、商业软件、非官方整理表 | 仅作线索，禁止作为正式方案数值依据 |

新增或更新数据集时，`_meta.json` 应记录 `source_file`、`source_url`、`publisher`、`quality_level`、`verification_status`。

## 目录

```
processed/
├── 一分一段表/       # 2021-2025 分数↔位次转换
├── 投档表/           # 2021-2025 常规批 1/2/3 次投档数据
├── 分数线/           # 各类别分数线（2020-2025）
├── 志愿计划/         # 常规批 2/3 次、提前批 2 次、高职注册入学计划
├── 选科要求/         # 2024 版+2027 版，本/专科，约 18 万条
├── 院校地区/         # 从选科要求 province 派生的院校地区索引
└── README.md         # 本文件
```

## 数据集详情

### 1. 一分一段表

**位置**：`processed/一分一段表/`

**文件**：
- `<year>.csv` / `<year>.json` — 单年份数据
- `all_years.json` — 全部年份合并
- `_meta.json` — 元数据

**字段**：

| 字段 | 类型 | 说明 |
|---|---|---|
| year | int | 年份 |
| score | int | 分数（从高到低） |
| total_count | int | 全体本段人数（该分数考生数） |
| total_cumulative | int | 全体累计人数（该分数及以上） |
| physics_count | int? | 选考物理本段人数 |
| physics_cumulative | int? | 选考物理累计人数 |
| chemistry_count | int? | 选考化学本段人数 |
| chemistry_cumulative | int? | 选考化学累计人数 |
| biology_count | int? | 选考生物本段人数 |
| biology_cumulative | int? | 选考生物累计人数 |
| politics_count | int? | 选考思想政治本段人数 |
| politics_cumulative | int? | 选考思想政治累计人数 |
| history_count | int? | 选考历史本段人数 |
| history_cumulative | int? | 选考历史累计人数 |
| geography_count | int? | 选考地理本段人数 |
| geography_cumulative | int? | 选考地理累计人数 |

**说明**：
- `None` 表示该分数段当年无此科考生
- 分数范围 150-700（逐年最高分不同）
- 累计人数 = 该分数及以上的总人数

**数据量**：5 年 × 约 540 行 = 约 2700 条

### 2. 投档表（普通类常规批）

**位置**：`processed/投档表/`

**文件**：
- `<year>_round<n>.csv` / `.json` — 单年份单次数据
- `all_years_all_rounds.json` — 全部合并
- `official_null_min_rank_exceptions.json` — 官方原表空最低投档位次例外清单，不得自动补数
- `_meta.json` — 元数据

**字段**：

| 字段 | 类型 | 说明 |
|---|---|---|
| year | int | 年份 |
| round | int | 志愿次数（1/2/3） |
| major_code | string | 专业代号（从原"专业代号及名称"拆分） |
| major_name | string | 专业名称 |
| school_code | string | 院校代号（如 A001） |
| school_name | string | 院校名称 |
| plan_count | int? | 投档计划数 |
| min_rank | int? | 最低投档位次 |

**说明**：
- round=1：第 1 次志愿（本科计划）
- round=2：第 2 次志愿（剩余本科+专科计划）
- round=3：第 3 次志愿（剩余计划）
- 仅含普通类，不含体育类
- major_code 拆分规则：开头的 1-3 位字母数字
- school_code 拆分规则：开头字母+3-4 位数字（如 A001, Y030）

**数据量**：5 年 × 3 次 = 约 15.1 万条

### 3. 分数线

**位置**：`processed/分数线/`

**文件**：
- `2025.json` — 2025 年完整分数线（从 PDF 提取）
- `历史分数线_2020-2024.json` — 2020-2024 历史汇总，来自山东省教育招生考试院官方页面图片公告转录（B 级）

**2025 数据结构**：

```json
{
  "year": 2025,
  "普通类": {
    "特殊类型招生控制线": 521,
    "一段线": 441,
    "二段线": 150,
    "3+2对口贯通分段培养高职志愿填报资格线": 391
  },
  "艺术类": {
    "本科文化控制线": {
      "舞蹈类、美术与设计类、播音与主持类": 441,
      "表（导）演类、音乐类、书法类": 330,
      "戏曲类": 286
    },
    "专科文化控制线": 150
  },
  "体育类": {
    "综合分一段线": 566,
    "综合分二段线": 428,
    "本科文化控制线": 286,
    "专科文化控制线": 150
  }
}
```

**2020-2024 使用限制**：`历史分数线_2020-2024.json` 当前质量等级为 B，保留官方页面、官方图片和 SHA256 证据，可作为历史趋势与正式方案辅助依据；正式填报仍以当年山东省教育招生考试院最新公告为准。

### 4. 志愿计划

**位置**：`processed/志愿计划/`

**文件**：
- `<year>.csv` / `<year>.json` — 单年份全部批次
- `all_years_all_batches.json` — 全部合并
- `official_null_plan_count_exceptions.json` — 官方原表空计划数例外清单，不得自动补数
- `_meta.json` — 元数据

**字段**：

| 字段 | 类型 | 说明 |
|---|---|---|
| year | int | 年份 |
| batch | string | 批次（常规批第2次/常规批第3次/提前批第2次/高职注册入学） |
| category | string | 类别（普通类/艺术类/体育类/春季高考） |
| school_code | string | 院校代号 |
| school_name | string | 院校名称 |
| major_code | string | 专业代号（从"专业代号 名称"拆分） |
| major_name | string | 专业名称（含备注） |
| subject_requirement | string | 选考科目要求（如"物理和化学"、"不限"） |
| level | string | 层次（本科/专科，仅提前批有） |
| study_years | string | 学制（年） |
| plan_count | int? | 计划数 |
| annual_fee | string | 年收费（元） |

**说明**：
- 常规批第2次志愿计划 = 剩余本科计划（第1次未完成）
- 常规批第3次志愿计划 = 剩余计划（含专科）
- 院校行和专业行通过"院校代号"列是否为空区分
- major_name 包含完整备注（校区、中外合作、单科要求等）

**数据量**：5 年 × 4 类批次 = 约 1.1 万条

### 5. 选科要求

**位置**：`processed/选科要求/`

**文件**：
- `2024版本科.csv|json` — 2024 版本科（适用 2025-2026），50915 条
- `2024版专科.csv|json` — 2024 版专科（适用 2025-2026），39950 条
- `2027版本科.csv|json` — 2027 版本科（2027 起），52558 条
- `2027版专科.csv|json` — 2027 版专科（2027 起），37365 条
- `all_requirements.json` — 全部合并，180788 条
- `_meta.json` — 元数据

**字段**：

| 字段 | 类型 | 说明 |
|---|---|---|
| edition | string | 2024 / 2027 |
| level | string | 本科 / 专科 |
| school_code | string | 院校代码（5 位数字，如 10001） |
| school_name | string | 院校名称 |
| major_code | string | 专业代码 |
| major_name | string | 专业（类）名称 |
| subject_requirement_raw | string | 原始文本（如"物理,化学(2门科目考生均须选考方可报考)"） |
| subject_requirement_type | string | none / one / two / three / any |
| subjects_list | string | 科目列表，用 `\|` 分隔（如"物理\|化学"） |
| province | string | 院校所在省份 |

**5 种类型**：

| type | 含义 | 考生需选考 |
|---|---|---|
| `none` | 不提科目要求 | 任选 3 科 |
| `one` | 1 门必须选考 | 必须含该科 |
| `two` | 2 门均须选考 | 必须同时含这两科 |
| `three` | 3 门均须选考 | 必须同时含这三科 |
| `any` | 多门任选 1 门 | 含其中任一门即可 |

**2024 版本科类型分布**：

| 类型 | 数量 | 占比 |
|---|---|---|
| two | 23685 | 46.5% |
| none | 21754 | 42.7% |
| one | 5016 | 9.9% |
| three | 460 | 0.9% |

**说明**：
- 2026 届使用 2024 版，2027 届起使用 2027 版
- 选科要求只做初筛，不能替代招生章程核查
- 最终以当年招生计划为准

### 6. 院校地区

**位置**：`processed/院校地区/`

**文件**：
- `school_region_index.sqlite` — 院校地区 SQLite 索引，2534 所唯一院校
- `school_region_index_meta.json` — 元数据

**字段**：

| 字段 | 类型 | 说明 |
|---|---|---|
| evidence_id | string | 地区证据 ID |
| school_name | string | 院校名称 |
| subject_school_codes | string | 选科索引中的 5 位院校代码，多个用 `\|` 分隔 |
| province | string | 院校所在省份，来自 `processed/选科要求/*.json` 的 `province` 字段 |
| province_source | string | 省份来源说明 |
| city | string | 城市；仅在可确定时填写 |
| city_status | string | PASS / REVIEW / UNKNOWN |
| city_match_type | string | override_reviewed / alias_in_school_name / review_multi_city / unknown |
| city_aliases | string | 城市别名或需复核城市，用 `\|` 分隔 |
| source_files | string | 派生来源文件 |
| quality_level | string | 省份字段质量等级 |

**使用规则**：
- 查询“山东的学校”必须使用 `province=山东`，不得用学校名包含“山东”判断。
- 查询“苏州/青岛”等城市时，`MATCH` 才可直接进入硬约束候选池；`REVIEW` 必须人工核查校区或招生计划原文。
- 例：青岛大学、济南大学、烟台大学均通过 `province=山东` 命中山东；西交利物浦大学通过 reviewed override 命中苏州；山东大学按“青岛”查询返回 `REVIEW`。

**数据量**：4 个 PDF 合计 180788 条

## 使用建议

### AI 查询示例

```python
import json

# 查 2025 年 441 分（一段线）的位次
data = json.load(open("processed/一分一段表/2025.json", encoding='utf-8'))
for r in data:
    if r['score'] == 441:
        print(f"2025 年 441 分累计位次：{r['total_cumulative']}")
        break

# 查北京大学 2025 年各专业投档位次
data = json.load(open("processed/投档表/2025_round1.json", encoding='utf-8'))
pku = [r for r in data if r['school_code'] == 'A001']
for r in pku:
    print(f"{r['major_code']} {r['major_name']}：位次 {r['min_rank']}")

# 查 2025 年常规批第2次剩余本科计划
data = json.load(open("processed/志愿计划/2025.json", encoding='utf-8'))
r2 = [r for r in data if r['batch'] == '常规批第2次']
print(f"2025 常规批第2次剩余本科计划：{len(r2)} 条")
```

### 注意事项

1. **跨年比较用位次**，不用分数（[[concept_赋分制]] 原因）
2. **投档表按 round 区分**：不同 round 对应不同计划范围，不能混用
3. **志愿计划按 batch 区分**：第2/3次计划是剩余计划，与第1次不同
4. **官方空值不补数**：`official_null_min_rank_exceptions.json` 与 `official_null_plan_count_exceptions.json` 仅记录官方原表空白，不得自动填补或进入概率/计划数计算

## 数据生成脚本

- `_process_score_table.py` — 一分一段表
- `_process_admission.py` — 投档表
- `_process_scorelines.py` — 分数线
- `_process_plans.py` — 志愿计划
- `_process_subject_requirements.py` — 选科要求

脚本可重复运行，输出幂等。

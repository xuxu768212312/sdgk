# 山东高考知识库

面向山东新高考志愿填报的本地知识库、审计闸门和可视化方案生成工具。项目以山东省教育招生考试院官方数据为正式主源，围绕一分一段表、投档表、招生计划、选科要求、院校地区、学生偏好和风险档，形成“先查库、后计算、再审计、可阻断”的完整链路。

维护者邮箱：`768212312@qq.com`

## 核心能力

- **Python 包化入口**：正式命令统一为 `python -m sdgk ...`，核心代码位于 `src/sdgk/`。
- **SQLite 主索引**：`processed/master/master_index.sqlite` 汇总院校库、院校代码别名、专业库、专业代码别名、招生单元、投档历史、计划历史和证据。
- **选科硬闸门**：`subject_index.sqlite` 输出 `PASS/BLOCK/REVIEW + evidence_id + source_file`，任何 `BLOCK/REVIEW` 不得交付正式方案。
- **地区硬闸门**：省份按 `province` 字段匹配，城市不确定或多校区返回 `REVIEW`，禁止用院校名 contains 判断“山东学校”。
- **策略优化器**：`strategy_optimizer_v4_rush_guard_fail_closed` 支持低分高价值捕获和受控冲刺，但保底、滑档和证据不足时失败关闭。
- **FastAPI + Vue3**：本地 API 与独立前端工作台，前端只展示 API 返回结果，不自行计算选科、地区或概率。

## 项目结构

```text
山东高考知识库/
├── src/sdgk/                       # Python 正式包
│   ├── indexes/                    # subject/region/master SQLite 索引
│   ├── strategy/                   # 概率与策略优化
│   ├── audits/                     # 数据、选科、最终方案审计
│   ├── plans/                      # 候选池、Excel、Markdown、方案链
│   └── api/                        # FastAPI 本地 API
├── frontend/                       # Vue3 + TypeScript + Element Plus
├── processed/
│   ├── 选科要求/subject_index.sqlite
│   ├── 院校地区/school_region_index.sqlite
│   └── master/master_index.sqlite
├── tests/                          # pytest 回归测试
├── raw/                            # 官方原始资料，只读
├── wiki/                           # 结构化知识与日志
└── students/                       # 学生隐私工作区，不提交 GitHub
```

## 安装

```bash
python -m pip install -e '.[dev]'
cd frontend
pnpm install
cd ..
```

如果本机没有 `pnpm`，可使用 Codex bundled pnpm；普通 Node 环境下也可用等价的包管理器安装前端依赖。

## 常用命令

构建三类索引：

```bash
python -m sdgk build subject-index --rebuild
python -m sdgk build region-index --rebuild
python -m sdgk build master-index --rebuild
```

查询选科和地区：

```bash
python -m sdgk check subject \
  --year 2026 \
  --level 本科 \
  --subjects 历史,生物,思想政治 \
  --school-code 10001 \
  --major-code 0060 \
  --json

python -m sdgk check region \
  --regions 山东,苏州 \
  --school-name 青岛大学 \
  --json
```

查询院校库和专业库：

```bash
python -m sdgk master summary
python -m sdgk master search-schools 青岛大学 --limit 5
python -m sdgk master search-majors 法学 --limit 10
python -m sdgk master search-programs 青岛大学 --major-name 法学 --limit 20
python -m sdgk master major-code-aliases --code 01 --limit 20
```

互联网来源准入：

```bash
python -m sdgk source check --url https://www.sdzk.cn/
```

生成完整方案链：

```bash
python -m sdgk plan generate \
  --student students/王二哈/基本信息.json \
  --out-dir students/王二哈/志愿方案/2026模拟_v1 \
  --risk-profile opportunistic
```

输出目录：

```text
students/<姓名>/志愿方案/<方案名>/
├── 志愿表.xlsx
├── 详细报告.md
├── candidate_pool.json
├── strategy_result.json
├── subject_audit.json
├── region_audit.json
├── final_audit.json
├── plan_meta.json
└── report_assets/
```

启动后端和前端：

```bash
python -m sdgk api serve --host 127.0.0.1 --port 8716
cd frontend
pnpm run dev
```

访问：`http://127.0.0.1:5173`

## 前端页面

- `数据看板`：审计状态、索引规模、主索引计数。
- `学生画像`：学生画像录入。
- `证据查询`：单条闸门、招生单元、院校库、专业库和代码复核。
- `候选池`：候选池、通过/阻断/待复核、证据字段。
- `方案生成`：一键生成方案链。
- `方案复核`：冲稳保垫、滑档概率、证据编号、闸门失败项。
- `报告下载`：志愿表、详细报告、审计文件。

## 正式方案硬条件

正式 96 志愿方案必须同时满足：

- 96 条全部 `subject_check_status=PASS`
- 地区硬偏好全部 `MATCH`
- 无未解决 `REVIEW`
- 无 `BLOCK`
- `strategy_result.hard_gate_passed=true`
- `final_audit.hard_gate_passed=true`
- `conservative_slip_probability` 不超过风险档阈值
- 每条志愿都有 `program_id`、`evidence_id`、`source_file`

任一条件不满足，只能输出模拟方案、问题清单和人工复核清单。

## 测试与审计

```bash
python -m pytest
python -m sdgk audit data --full-subject-reextract
cd frontend && pnpm run build
```

本轮校验结果：

```text
subject_index rows = 180788
region_index schools = 2534
master programs = 36825
school code aliases = 4775
major code aliases = 25472
pytest = 30 passed
data audit = FAIL 0, WARN 1（未执行选科 PDF 全量重抽取）
frontend build = passed
```

## 数据原则

1. 山东省教育招生考试院（`sdzk.cn`）是山东高考正式主源。
2. 跨年比较只用位次，不用分数硬比。
3. 本科、专科、提前批、常规批分开建池和审计。
4. 第三方数据只能作线索，不进入正式数值依据。
5. LLM 不得直接凭上下文判断选科、地区、概率或能否正式交付。
6. 2026 当年计划未发布或未入库前，方案必须标记为模拟。

## 隐私与提交

`students/` 默认被 `.gitignore` 排除，具体考生信息、成绩、偏好、方案不提交 GitHub。提交前检查：

```bash
git status --short
git check-ignore -v students/
```

## 免责声明

本项目用于辅助山东高考志愿填报的数据整理、风险评估和方案审计，不替代山东省教育招生考试院官方信息、招生高校章程、考生本人确认和人工复核。正式填报前必须以当年官方计划、考生实际位次、选科要求、体检限制、单科限制和家庭偏好为准。

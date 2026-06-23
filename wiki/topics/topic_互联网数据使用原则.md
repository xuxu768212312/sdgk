---
title: 互联网数据使用原则
tags: [互联网数据, 官方来源, 数据准入, 策略优化]
created: 2026-06-23
updated: 2026-06-23
sources: ["https://www.sdzk.cn/", "https://www.sdzk.cn/NewsListM.aspx?BCID=2&CID=20", "https://www.sdzk.cn/Business.aspx?BID=4", "https://gaokao.chsi.com.cn/", "raw/_common/来源索引/官方来源索引.md"]
---

# 互联网数据使用原则

互联网数据用于发现最新官方信息和补充合规材料，但不能绕过本地数据治理。正式志愿方案必须经过来源准入、官方回查、raw/processed 追溯、选科硬闸门和策略优化器检查。

## 来源准入

使用任何 URL 前先运行：

```bash
python scripts/internet_source_policy.py --url <URL>
```

| 来源 | 质量上限 | 用途 |
|---|---|---|
| 山东省教育招生考试院 `sdzk.cn` / `wsbm.sdzk.cn` | S | 山东高考政策、计划、分数线、一分一段、投档、缺额、填报入口状态的唯一主源 |
| 教育部、阳光高考、山东省教育厅 | C | 政策背景、招生章程、合规辅助 |
| 高校官网/本科招生网 | C | 体检、单科、外语、校区、学费、培养模式、转专业等章程事项 |
| 媒体、论坛、公众号、商业软件、非官方表格 | D | 只能作线索，必须回查官方来源 |

## 入库规则

- S 级互联网资料必须保存官方原文或附件到 `raw/` 后，再由脚本生成 `processed/`。
- C 级官方辅助资料只能进入合规核查，不替代山东考试院计划、位次、投档数据。
- D 级线索不得写入 `processed/`，不得进入正式策略算法。
- 2026 当年计划、缺额、志愿填报时间、分数线、一分一段、投档情况必须以操作当日最新 `sdzk.cn` 信息为准。

## 算法入口

策略优化器只接受已经过准入和硬闸门的候选志愿：

```bash
python algorithms/strategy_optimizer.py \
  --input students/某考生/志愿方案/candidates.json \
  --risk-profile standard \
  --slots 96 \
  --out students/某考生/志愿方案/strategy_optimized.json
```

候选志愿必须满足：

- `source_quality` 为 S/A/B
- `subject_check_status` 为 `PASS`
- 存在 `evidence_id`
- 存在 `source_file`
- 存在录取概率和效用分
- 不存在重复的院校专业候选
- 保守滑档概率不超过风险偏好阈值

若输出 `hard_gate_passed=false`，不得交付为正式方案。

## 相关页面

- [[topic_数据使用原则]]
- [[topic_专有填报策略]]
- [[topic_高级决策模型]]
- [[topic_选科查询]]

from __future__ import annotations

from pathlib import Path
from typing import Any

from sdgk.core.paths import ensure_students_path


def gradient_bar(counts: dict[str, Any]) -> str:
    labels = ["冲", "稳", "保", "垫"]
    total = sum(int(counts.get(label, 0)) for label in labels) or 1
    parts = []
    for label in labels:
        count = int(counts.get(label, 0))
        blocks = max(1 if count else 0, round(count / total * 32))
        parts.append(f"{label} {'█' * blocks} {count}")
    return "\n".join(parts)


def write_markdown_report(
    *,
    out_path: Path,
    profile: dict[str, Any],
    candidate_pool: dict[str, Any],
    strategy_result: dict[str, Any],
    final_audit: dict[str, Any],
) -> Path:
    safe_path = ensure_students_path(out_path)
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    selected = strategy_result.get("selected", [])
    counts = strategy_result.get("gradient_counts", {})
    name = profile.get("name") or profile.get("姓名") or "考生"
    status = "通过" if final_audit.get("hard_gate_passed") else "未通过"
    simulation_text = "是" if candidate_pool.get("simulation") else "否"
    rows = []
    for row in selected[:96]:
        rows.append(
            "| {order} | {bucket} | {p} | {school} | {major} | {subject} | {region} | `{eid}` |".format(
                order=row.get("strategy_order", ""),
                bucket=row.get("gradient_bucket", ""),
                p=row.get("probability", ""),
                school=row.get("school_name", ""),
                major=str(row.get("major_name", ""))[:36],
                subject=row.get("subject_check_status", ""),
                region=row.get("region_check_status", ""),
                eid=str(row.get("evidence_id", ""))[:12],
            )
        )
    review_items = final_audit.get("violations", []) + strategy_result.get("violations", [])
    content = f"""# {name} 志愿方案详细报告

> 本报告由本地 `sdgk` 应用生成。山东省教育招生考试院为唯一正式主源；2026 当年计划未发布或未复核前，本报告按模拟方案处理。

## 一、学生画像

| 项目 | 内容 |
|---|---|
| 年份 | {profile.get("year") or profile.get("年份") or ""} |
| 批次 | {profile.get("level") or profile.get("批次") or "本科"} |
| 分数 | {profile.get("score") or profile.get("分数") or ""} |
| 位次 | {candidate_pool.get("rank_info", {}).get("rank") or "待补充"} |
| 选科 | {"、".join(candidate_pool.get("subjects", []))} |
| 地区偏好 | {"、".join(candidate_pool.get("preferences", {}).get("regions", []))} |
| 专业偏好 | {"、".join(candidate_pool.get("preferences", {}).get("majors", []))} |
| 是否模拟 | {simulation_text} |

## 二、硬闸门结论

**最终状态：{status}**

- 选科闸门：正式方案要求 96 条全部 `PASS`。
- 地区闸门：硬地区偏好要求全部 `MATCH`；软偏好允许 `NO_MATCH` 降权，但 `REVIEW` 必须人工复核。
- 证据闸门：每条必须含 `program_id`、`evidence_id`、`source_file`。
- 策略闸门：`strategy_result.hard_gate_passed=true` 且保守滑档概率不超过风险档。

## 三、冲稳保垫结构

```text
{gradient_bar(counts)}
```

| 指标 | 数值 |
|---|---|
| 保守滑档概率 | {strategy_result.get("conservative_slip_probability")} |
| 独立模型滑档概率 | {strategy_result.get("independent_model_slip_probability")} |
| 候选数 | {candidate_pool.get("counts", {}).get("candidates")} |
| 人工复核数 | {candidate_pool.get("counts", {}).get("review")} |
| 阻断数 | {candidate_pool.get("counts", {}).get("blocked")} |

## 四、志愿表预览

| 序号 | 梯度 | 概率 | 院校 | 专业 | 选科 | 地区 | 证据 |
|---:|---|---:|---|---|---|---|---|
{chr(10).join(rows) if rows else "| - | - | - | - | - | - | - | - |"}

## 五、低分高价值机会

本轮排序只在硬闸门之后进行价值捕获；价值项包括院校层次、专业匹配、地区匹配、位次机会、计划稳定性。任何 `BLOCK` 或 `REVIEW` 不会因为“性价比高”被放入正式方案。

## 六、REVIEW/BLOCK 清单

{chr(10).join(f"- {item}" for item in review_items) if review_items else "- 暂无策略级违规项。"}

## 七、数据来源说明

- 选科：`processed/选科要求/subject_index.sqlite`
- 地区：`processed/院校地区/school_region_index.sqlite`
- 主索引：`processed/master/master_index.sqlite`
- 投档/计划：`processed/投档表/`、`processed/志愿计划/`

正式填报前必须使用山东省教育招生考试院最新发布的当年招生计划、缺额计划、投档规则再次复核。
"""
    safe_path.write_text(content, encoding="utf-8")
    return safe_path

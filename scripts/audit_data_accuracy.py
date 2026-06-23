#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit processed data against raw official source files.

The audit is intentionally strict:
- raw/ is read-only
- processed CSV/JSON pairs must match
- combined JSON files must equal the sum of annual files
- core Excel-derived datasets are re-extracted from raw and compared
- 2025 scoreline PDF text must contain the published values
- optional full subject-requirement PDF re-extraction can be enabled
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional, Union

import pdfplumber
import xlrd

from subject_eligibility import DEFAULT_DB_PATH, DEFAULT_META_PATH, connect_index, make_evidence_id, parse_subject_requirement


ROOT = Path(__file__).resolve().parents[1]
YEARS = [2021, 2022, 2023, 2024, 2025]
SUBJECTS = ["physics", "chemistry", "biology", "politics", "history", "geography"]
CN_SUBJECTS = {"物理", "化学", "生物", "思想政治", "历史", "地理"}


class Audit:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []
        self.stats: dict[str, Any] = {}

    def add(self, severity: str, code: str, message: str, path: str = "", detail: Any = None) -> None:
        self.items.append(
            {
                "severity": severity,
                "code": code,
                "message": message,
                "path": path,
                "detail": detail,
            }
        )

    def fail(self, code: str, message: str, path: str = "", detail: Any = None) -> None:
        self.add("FAIL", code, message, path, detail)

    def warn(self, code: str, message: str, path: str = "", detail: Any = None) -> None:
        self.add("WARN", code, message, path, detail)

    def info(self, code: str, message: str, path: str = "", detail: Any = None) -> None:
        self.add("INFO", code, message, path, detail)

    def counts(self) -> Counter:
        return Counter(item["severity"] for item in self.items)


def rel(path: Union[Path, str]) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def as_csv_value(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        if math.isnan(v):
            return ""
        if v.is_integer():
            return str(int(v))
    return str(v)


def normalized_json_rows(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, str]]:
    return [{field: as_csv_value(row.get(field)) for field in fields} for row in rows]


def to_int(v: Any) -> Optional[int]:
    if v == "" or v is None:
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None


def split_major(v: Any) -> tuple[str, str]:
    if not v:
        return "", ""
    s = str(v).strip()
    m = re.match(r"^([A-Za-z0-9]{1,3})(.*)$", s)
    if m:
        return m.group(1), m.group(2).strip()
    return "", s


def split_school(v: Any) -> tuple[str, str]:
    if not v:
        return "", ""
    s = str(v).strip()
    m = re.match(r"^([A-Z]\d{3,4})(.*)$", s)
    if m:
        return m.group(1), m.group(2).strip()
    return "", s


def split_major_name(v: Any) -> tuple[str, str]:
    if not v:
        return "", ""
    s = str(v).strip()
    m = re.match(r"^([0-9A-Za-z]{1,3})\s+(.*)$", s)
    if m:
        return m.group(1), m.group(2).strip()
    return "", s


def find_header_row_admission(sh: xlrd.sheet.Sheet) -> int:
    for r in range(min(5, sh.nrows)):
        row = [str(sh.cell_value(r, c)).strip() for c in range(sh.ncols)]
        joined = "|".join(row)
        if "专业" in joined and "院校" in joined:
            return r
    return 1


def find_col_indices_admission(sh: xlrd.sheet.Sheet, header_row: int) -> dict[str, int]:
    headers = [str(sh.cell_value(header_row, c)).strip() for c in range(sh.ncols)]
    cols = {"major": -1, "school": -1, "plan": -1, "rank": -1}
    for i, h in enumerate(headers):
        if "专业" in h and cols["major"] < 0:
            cols["major"] = i
        elif "院校" in h and cols["school"] < 0:
            cols["school"] = i
        elif "计划" in h and cols["plan"] < 0:
            cols["plan"] = i
        elif ("位次" in h or "最低位" in h) and cols["rank"] < 0:
            cols["rank"] = i
    return cols


def process_admission_file(filepath: Path, year: int, round_num: int) -> list[dict[str, Any]]:
    wb = xlrd.open_workbook(str(filepath))
    sh = wb.sheet_by_index(0)
    header_row = find_header_row_admission(sh)
    cols = find_col_indices_admission(sh, header_row)
    rows = []
    for r in range(header_row + 1, sh.nrows):
        major_raw = sh.cell_value(r, cols["major"])
        school_raw = sh.cell_value(r, cols["school"])
        if not major_raw or not school_raw:
            continue
        major_code, major_name = split_major(major_raw)
        school_code, school_name = split_school(school_raw)
        rows.append(
            {
                "year": year,
                "round": round_num,
                "major_code": major_code,
                "major_name": major_name,
                "school_code": school_code,
                "school_name": school_name,
                "plan_count": to_int(sh.cell_value(r, cols["plan"])),
                "min_rank": to_int(sh.cell_value(r, cols["rank"])),
            }
        )
    return rows


def extract_score_year(year: int) -> list[dict[str, Any]]:
    src = ROOT / f"raw/{year}/一分一段表.xls"
    wb = xlrd.open_workbook(str(src))
    sh = wb.sheet_by_index(0)
    rows = []
    for r in range(3, sh.nrows):
        score = sh.cell_value(r, 0)
        if score == "" or score is None:
            continue
        try:
            score = int(score)
        except (ValueError, TypeError):
            continue
        rec: dict[str, Any] = {"year": year, "score": score}
        rec["total_count"] = to_int(sh.cell_value(r, 1))
        rec["total_cumulative"] = to_int(sh.cell_value(r, 2))
        for i, subj in enumerate(SUBJECTS):
            base = 3 + i * 2
            rec[f"{subj}_count"] = to_int(sh.cell_value(r, base))
            rec[f"{subj}_cumulative"] = to_int(sh.cell_value(r, base + 1))
        rows.append(rec)
    return rows


def find_header_row_plan(sh: xlrd.sheet.Sheet) -> int:
    for r in range(min(5, sh.nrows)):
        row = [str(sh.cell_value(r, c)).strip() for c in range(sh.ncols)]
        if "院校代号" in row:
            return r
    return None


def process_plan_file(filepath: Path, year: int, batch: str, category: str) -> list[dict[str, Any]]:
    wb = xlrd.open_workbook(str(filepath))
    sh = wb.sheet_by_index(0)
    header_row = find_header_row_plan(sh)
    col_school_code = 0
    col_name = 1
    col_subject = 2
    col_level = -1
    col_years = -1
    col_plan = -1
    col_fee = -1
    if header_row is None:
        data_start_row = 2
        col_years = 3
        col_plan = 4
        col_fee = 5
    else:
        data_start_row = header_row + 1
        headers = [str(sh.cell_value(header_row, c)).strip() for c in range(sh.ncols)]
        for i, h in enumerate(headers):
            if "层次" in h:
                col_level = i
            elif "学制" in h:
                col_years = i
            elif "计划" in h:
                col_plan = i
            elif "收费" in h:
                col_fee = i

    rows = []
    current_school_code = ""
    current_school_name = ""
    for r in range(data_start_row, sh.nrows):
        school_code = str(sh.cell_value(r, col_school_code)).strip()
        name = str(sh.cell_value(r, col_name)).strip()
        if not name:
            continue
        if school_code:
            current_school_code = school_code
            current_school_name = name
            continue
        major_code, major_name = split_major_name(name)
        rows.append(
            {
                "year": year,
                "batch": batch,
                "category": category,
                "school_code": current_school_code,
                "school_name": current_school_name,
                "major_code": major_code,
                "major_name": major_name,
                "subject_requirement": str(sh.cell_value(r, col_subject)).strip() if col_subject >= 0 else "",
                "level": str(sh.cell_value(r, col_level)).strip() if col_level >= 0 else "",
                "study_years": str(sh.cell_value(r, col_years)).strip() if col_years >= 0 else "",
                "plan_count": to_int(sh.cell_value(r, col_plan)) if col_plan >= 0 else None,
                "annual_fee": str(sh.cell_value(r, col_fee)).strip() if col_fee >= 0 else "",
            }
        )
    return rows


SUBJECT_PDFS = [
    {
        "edition": "2024",
        "level": "本科",
        "pdf": ROOT / "raw/2026/政策文件原件/2024通用版普通高校拟在山东招生专业类选考科目要求（本科，适用2025-2026）.pdf",
        "json": ROOT / "processed/选科要求/2024版本科.json",
    },
    {
        "edition": "2024",
        "level": "专科",
        "pdf": ROOT / "raw/2026/政策文件原件/2024通用版普通高校拟在山东招生专业类选考科目要求（专科，适用2025-2026）.pdf",
        "json": ROOT / "processed/选科要求/2024版专科.json",
    },
    {
        "edition": "2027",
        "level": "本科",
        "pdf": ROOT / "raw/2026/政策文件原件/2027通用版普通高校拟在山东招生专业类选考科目要求（本科，2027及以后）.pdf",
        "json": ROOT / "processed/选科要求/2027版本科.json",
    },
    {
        "edition": "2027",
        "level": "专科",
        "pdf": ROOT / "raw/2026/政策文件原件/2027通用版普通高校拟在山东招生专业类选考科目要求（专科，2027及以后）.pdf",
        "json": ROOT / "processed/选科要求/2027版专科.json",
    },
]


def extract_subject_pdf(cfg: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with pdfplumber.open(str(cfg["pdf"])) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for tbl in tables:
                if len(tbl) < 2:
                    continue
                for row in tbl[1:]:
                    if len(row) < 6:
                        continue
                    school_code = (row[0] or "").replace("\n", "").strip()
                    school_name = (row[1] or "").replace("\n", "").strip()
                    major_code = (row[2] or "").replace("\n", "").strip()
                    major_name = (row[3] or "").replace("\n", "").strip()
                    subject_raw = (row[4] or "").replace("\n", "").strip()
                    province = (row[5] or "").replace("\n", "").strip()
                    if not school_code or not school_name:
                        continue
                    if not re.match(r"^\d{5}$", school_code):
                        continue
                    req_type, subjects = parse_subject_requirement(subject_raw)
                    rows.append(
                        {
                            "edition": cfg["edition"],
                            "level": cfg["level"],
                            "school_code": school_code,
                            "school_name": school_name,
                            "major_code": major_code,
                            "major_name": major_name,
                            "subject_requirement_raw": subject_raw,
                            "subject_requirement_type": req_type,
                            "subjects_list": "|".join(subjects),
                            "province": province,
                        }
                    )
    return rows


def first_mismatch(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    for i, (left, right) in enumerate(zip(a, b)):
        if left != right:
            return {"index": i, "expected": left, "actual": right}
    if len(a) != len(b):
        return {"expected_len": len(a), "actual_len": len(b)}
    return None


def audit_csv_json_pairs(audit: Audit) -> None:
    for csv_path in sorted((ROOT / "processed").glob("**/*.csv")):
        json_path = csv_path.with_suffix(".json")
        if not json_path.exists():
            audit.fail("CSV_WITHOUT_JSON", "CSV 缺少同名 JSON", rel(csv_path))
            continue
        fields, csv_rows = read_csv_rows(csv_path)
        json_rows = load_json(json_path)
        if not isinstance(json_rows, list):
            audit.fail("JSON_NOT_LIST", "同名 JSON 不是数组", rel(json_path))
            continue
        json_fields = list(json_rows[0].keys()) if json_rows else fields
        if fields != json_fields and set(fields) == set(json_fields):
            audit.warn(
                "FIELD_ORDER_MISMATCH",
                "CSV 与 JSON 字段集合一致但顺序不同",
                rel(csv_path),
                {"csv": fields, "json": json_fields},
            )
        elif fields != json_fields:
            audit.fail(
                "FIELD_MISMATCH",
                "CSV 与 JSON 字段顺序或字段集合不一致",
                rel(csv_path),
                {"csv": fields, "json": json_fields},
            )
        norm_json = normalized_json_rows(json_rows, fields)
        if len(csv_rows) != len(json_rows):
            audit.fail(
                "ROW_COUNT_MISMATCH",
                "CSV 与 JSON 行数不一致",
                rel(csv_path),
                {"csv": len(csv_rows), "json": len(json_rows)},
            )
        elif csv_rows != norm_json:
            mismatch = first_mismatch(csv_rows, norm_json)
            audit.fail("CSV_JSON_VALUE_MISMATCH", "CSV 与 JSON 同名数据值不一致", rel(csv_path), mismatch)
    audit.info("CSV_JSON_PAIRS", "CSV/JSON 同名文件一致性检查完成")


def audit_combined_files(audit: Audit) -> None:
    score_all = load_json(ROOT / "processed/一分一段表/all_years.json")
    score_sum = sum(len(load_json(ROOT / f"processed/一分一段表/{y}.json")) for y in YEARS)
    if sum(len(v) for v in score_all.values()) != score_sum:
        audit.fail("SCORE_COMBINED_COUNT", "一分一段 all_years.json 与年度文件总量不一致")

    admission_all = load_json(ROOT / "processed/投档表/all_years_all_rounds.json")
    admission_sum = sum(len(load_json(ROOT / f"processed/投档表/{y}_round{r}.json")) for y in YEARS for r in [1, 2, 3])
    if len(admission_all) != admission_sum:
        audit.fail("ADMISSION_COMBINED_COUNT", "投档表 all_years_all_rounds.json 与分文件总量不一致")

    plan_all = load_json(ROOT / "processed/志愿计划/all_years_all_batches.json")
    plan_sum = sum(len(load_json(ROOT / f"processed/志愿计划/{y}.json")) for y in YEARS)
    if len(plan_all) != plan_sum:
        audit.fail("PLAN_COMBINED_COUNT", "志愿计划 all_years_all_batches.json 与年度文件总量不一致")

    req_all = load_json(ROOT / "processed/选科要求/all_requirements.json")
    req_sum = sum(
        len(load_json(ROOT / f"processed/选科要求/{name}.json"))
        for name in ["2024版本科", "2024版专科", "2027版本科", "2027版专科"]
    )
    if len(req_all) != req_sum:
        audit.fail("REQ_COMBINED_COUNT", "选科要求 all_requirements.json 与分文件总量不一致")

    audit.stats["combined_counts"] = {
        "score": score_sum,
        "admission": admission_sum,
        "plans": plan_sum,
        "subject_requirements": req_sum,
    }
    audit.info("COMBINED_FILES", "合并 JSON 数量一致性检查完成", detail=audit.stats["combined_counts"])


def audit_score_tables(audit: Audit) -> None:
    expected_fields = ["year", "score", "total_count", "total_cumulative"] + [
        f"{s}_{kind}" for s in SUBJECTS for kind in ["count", "cumulative"]
    ]
    for year in YEARS:
        path = ROOT / f"processed/一分一段表/{year}.json"
        rows = load_json(path)
        if rows != extract_score_year(year):
            audit.fail("SCORE_RAW_MISMATCH", "一分一段 processed 与 raw 重抽取不一致", rel(path), first_mismatch(extract_score_year(year), rows))
        scores = [row["score"] for row in rows]
        if scores != sorted(scores, reverse=True):
            audit.fail("SCORE_ORDER", "一分一段分数不是降序", rel(path))
        if len(scores) != len(set(scores)):
            audit.fail("SCORE_DUPLICATE", "一分一段存在重复分数", rel(path))
        for field in expected_fields:
            if any(field not in row for row in rows):
                audit.fail("SCORE_FIELD_MISSING", f"一分一段缺少字段 {field}", rel(path))
        prev_total = None
        for row in rows:
            total_count = row["total_count"]
            total_cum = row["total_cumulative"]
            if total_count is None or total_count < 0:
                audit.fail("SCORE_TOTAL_COUNT", "一分一段 total_count 非法", rel(path), row)
            if total_cum is None or total_cum < 0:
                audit.fail("SCORE_TOTAL_CUM", "一分一段 total_cumulative 非法", rel(path), row)
            if prev_total is not None:
                if total_cum < prev_total:
                    audit.fail("SCORE_TOTAL_MONOTONIC", "一分一段累计人数非单调递增", rel(path), row)
                if total_cum - prev_total != total_count:
                    audit.fail("SCORE_TOTAL_DIFF", "一分一段累计差值不等于本段人数", rel(path), row)
            prev_total = total_cum
            for subj in SUBJECTS:
                count = row.get(f"{subj}_count")
                cumulative = row.get(f"{subj}_cumulative")
                if count is not None and count < 0:
                    audit.fail("SUBJECT_COUNT_NEGATIVE", "选考科目本段人数为负", rel(path), row)
                if cumulative is not None and cumulative < 0:
                    audit.fail("SUBJECT_CUM_NEGATIVE", "选考科目累计人数为负", rel(path), row)
    audit.info("SCORE_TABLES", "一分一段表 raw 重抽取与单调性检查完成")


def audit_admission(audit: Audit) -> None:
    null_ranks = []
    null_plans = []
    duplicate_counter = Counter()
    for year in YEARS:
        raw_by_round: dict[int, list[dict[str, Any]]] = {}
        f1 = ROOT / f"raw/{year}/常规批第1次投档表.xls"
        raw_by_round[1] = process_admission_file(f1, year, 1)
        for round_num in [2, 3]:
            directory = ROOT / f"raw/{year}/常规批第{round_num}次投档表"
            files = sorted(directory.glob("*.xls"))
            chosen = next((p for p in files if "普通类" in p.name), files[0] if files else None)
            raw_by_round[round_num] = process_admission_file(chosen, year, round_num) if chosen else []
        for round_num, raw_rows in raw_by_round.items():
            path = ROOT / f"processed/投档表/{year}_round{round_num}.json"
            rows = load_json(path)
            if rows != raw_rows:
                audit.fail("ADMISSION_RAW_MISMATCH", "投档表 processed 与 raw 重抽取不一致", rel(path), first_mismatch(raw_rows, rows))
            for row in rows:
                if row["year"] != year or row["round"] != round_num:
                    audit.fail("ADMISSION_YEAR_ROUND", "投档表 year/round 字段与文件名不一致", rel(path), row)
                if not re.match(r"^[A-Z]\d{3,4}$", row["school_code"]):
                    audit.fail("SCHOOL_CODE_PATTERN", "投档表院校代码格式异常", rel(path), row)
                if not row["school_name"] or not row["major_name"]:
                    audit.fail("ADMISSION_NAME_EMPTY", "投档表院校或专业名称为空", rel(path), row)
                if row["plan_count"] is None:
                    null_plans.append(row)
                elif row["plan_count"] <= 0:
                    audit.fail("ADMISSION_PLAN_NONPOSITIVE", "投档计划数非正", rel(path), row)
                if row["min_rank"] is None:
                    null_ranks.append(row)
                elif not (1 <= row["min_rank"] <= 1_000_000):
                    audit.fail("ADMISSION_RANK_RANGE", "最低投档位次超出合理范围", rel(path), row)
                duplicate_counter[(year, round_num, row["school_code"], row["major_code"], row["major_name"])] += 1
    duplicates = [k for k, c in duplicate_counter.items() if c > 1]
    if duplicates:
        audit.warn("ADMISSION_DUPLICATES", "投档表存在重复 school_code+major_code+major_name 键", detail={"count": len(duplicates), "sample": duplicates[:10]})
    audit.stats["admission_null_ranks"] = len(null_ranks)
    audit.stats["admission_null_plans"] = len(null_plans)
    if null_ranks:
        audit.warn("ADMISSION_NULL_RANKS", "投档表存在原始空位次，需要人工确认特殊类型", detail={"count": len(null_ranks), "sample": null_ranks[:10]})
    if null_plans:
        audit.warn("ADMISSION_NULL_PLANS", "投档表存在空计划数，需要确认是否为原始空值", detail={"count": len(null_plans), "sample": null_plans[:10]})
    audit.info("ADMISSION", "投档表 raw 重抽取与字段合法性检查完成")


def audit_plans(audit: Audit) -> None:
    allowed_batches = {"常规批第2次", "常规批第3次", "提前批第2次", "高职注册入学"}
    allowed_categories = {"普通类", "艺术类", "体育类", "春季高考"}
    missing_school_codes = []
    null_plans = []
    for year in YEARS:
        expected = []
        for batch, dirname in [
            ("常规批第2次", "常规批第2次志愿计划"),
            ("常规批第3次", "常规批第3次志愿计划"),
            ("提前批第2次", "提前批第2次志愿计划"),
        ]:
            files = sorted((ROOT / f"raw/{year}/{dirname}").glob("*.xls"))
            if files:
                chosen = next((p for p in files if "普通类" in p.name), files[0])
                expected.extend(process_plan_file(chosen, year, batch, "普通类"))
        for f in sorted((ROOT / f"raw/{year}/高职注册入学计划").glob("*.xls")):
            for key, category in {"普通类": "普通类", "艺术类": "艺术类", "体育类": "体育类", "春季高考": "春季高考"}.items():
                if key in f.name:
                    expected.extend(process_plan_file(f, year, "高职注册入学", category))
                    break
        path = ROOT / f"processed/志愿计划/{year}.json"
        rows = load_json(path)
        if rows != expected:
            audit.fail("PLAN_RAW_MISMATCH", "志愿计划 processed 与 raw 重抽取不一致", rel(path), first_mismatch(expected, rows))
        for row in rows:
            if row["year"] != year:
                audit.fail("PLAN_YEAR", "志愿计划 year 与文件名不一致", rel(path), row)
            if row["batch"] not in allowed_batches:
                audit.fail("PLAN_BATCH", "志愿计划 batch 非法", rel(path), row)
            if row["category"] not in allowed_categories:
                audit.fail("PLAN_CATEGORY", "志愿计划 category 非法", rel(path), row)
            if not row["school_code"]:
                missing_school_codes.append(row)
            if not row["school_name"] or not row["major_name"]:
                audit.fail("PLAN_NAME_EMPTY", "志愿计划院校或专业名称为空", rel(path), row)
            if row["plan_count"] is None:
                null_plans.append(row)
            elif row["plan_count"] <= 0:
                audit.fail("PLAN_COUNT_NONPOSITIVE", "志愿计划计划数非正", rel(path), row)
    audit.stats["plan_missing_school_codes"] = len(missing_school_codes)
    audit.stats["plan_null_plan_count"] = len(null_plans)
    if missing_school_codes:
        audit.warn("PLAN_MISSING_SCHOOL_CODE", "志愿计划存在空院校代码，需人工核查原始表结构", detail={"count": len(missing_school_codes), "sample": missing_school_codes[:10]})
    if null_plans:
        audit.warn("PLAN_NULL_PLAN_COUNT", "志愿计划存在空计划数，需确认是否为原始专项/格式空值", detail={"count": len(null_plans), "sample": null_plans[:10]})
    audit.info("PLANS", "志愿计划 raw 重抽取与字段合法性检查完成")


def audit_subject_requirements(audit: Audit, full_reextract: bool) -> None:
    allowed_types = {"none", "one", "two", "three", "any"}
    files = ["2024版本科", "2024版专科", "2027版本科", "2027版专科"]
    total = 0
    type_counts = Counter()
    for name in files:
        path = ROOT / f"processed/选科要求/{name}.json"
        rows = load_json(path)
        total += len(rows)
        for row in rows:
            if not re.match(r"^\d{5}$", row["school_code"]):
                audit.fail("REQ_SCHOOL_CODE", "选科要求院校代码不是 5 位数字", rel(path), row)
            if row["subject_requirement_type"] not in allowed_types:
                audit.fail("REQ_TYPE", "选科要求类型非法", rel(path), row)
            subjects = [x for x in row["subjects_list"].split("|") if x]
            if any(s not in CN_SUBJECTS for s in subjects):
                audit.fail("REQ_SUBJECT_NAME", "选科要求科目名称非法", rel(path), row)
            expected_type, expected_subjects = parse_subject_requirement(row["subject_requirement_raw"])
            if row["subject_requirement_type"] != expected_type or subjects != expected_subjects:
                audit.fail("REQ_PARSE_MISMATCH", "选科要求原始文本解析结果与结构化字段不一致", rel(path), row)
            type_counts[row["subject_requirement_type"]] += 1
    all_req = load_json(ROOT / "processed/选科要求/all_requirements.json")
    if len(all_req) != total:
        audit.fail("REQ_ALL_COUNT", "选科要求 all_requirements 数量不等于分文件总和")
    audit.stats["subject_requirement_type_counts"] = dict(type_counts)

    if full_reextract:
        start = time.time()
        for cfg in SUBJECT_PDFS:
            expected = extract_subject_pdf(cfg)
            actual = load_json(cfg["json"])
            if expected != actual:
                audit.fail("REQ_RAW_PDF_MISMATCH", "选科要求 processed 与 PDF 重抽取不一致", rel(cfg["json"]), first_mismatch(expected, actual))
            audit.info("REQ_PDF_REEXTRACT_FILE", f"选科要求 PDF 重抽取完成：{cfg['edition']} {cfg['level']}", rel(cfg["pdf"]), {"rows": len(expected)})
        audit.stats["subject_pdf_reextract_seconds"] = round(time.time() - start, 1)
    else:
        audit.warn("REQ_PDF_REEXTRACT_SKIPPED", "未启用选科要求 PDF 全量重抽取；仅做结构化字段自洽检查")
    audit.info("SUBJECT_REQUIREMENTS", "选科要求检查完成")


def audit_subject_index(audit: Audit) -> None:
    files = ["2024版本科", "2024版专科", "2027版本科", "2027版专科"]
    expected_total = sum(len(load_json(ROOT / f"processed/选科要求/{name}.json")) for name in files)

    if not DEFAULT_DB_PATH.exists():
        audit.fail("SUBJECT_INDEX_MISSING", "选科 SQLite 索引不存在", rel(DEFAULT_DB_PATH))
        return
    if not DEFAULT_META_PATH.exists():
        audit.fail("SUBJECT_INDEX_META_MISSING", "选科 SQLite 索引元数据不存在", rel(DEFAULT_META_PATH))
        return

    try:
        meta = load_json(DEFAULT_META_PATH)
        with connect_index(DEFAULT_DB_PATH) as conn:
            actual_total = conn.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
            sample = conn.execute("SELECT * FROM requirements ORDER BY row_id LIMIT 1").fetchone()
    except Exception as exc:
        audit.fail("SUBJECT_INDEX_READ_ERROR", "选科 SQLite 索引读取失败", rel(DEFAULT_DB_PATH), str(exc))
        return

    if actual_total != expected_total:
        audit.fail(
            "SUBJECT_INDEX_COUNT",
            "选科 SQLite 索引行数与源 JSON 总量不一致",
            rel(DEFAULT_DB_PATH),
            {"expected": expected_total, "actual": actual_total},
        )
    if meta.get("row_count") != expected_total:
        audit.fail(
            "SUBJECT_INDEX_META_COUNT",
            "选科 SQLite 索引元数据行数与源 JSON 总量不一致",
            rel(DEFAULT_META_PATH),
            {"expected": expected_total, "actual": meta.get("row_count")},
        )
    if sample is None:
        audit.fail("SUBJECT_INDEX_EMPTY", "选科 SQLite 索引为空", rel(DEFAULT_DB_PATH))
        return

    sample_dict = {key: sample[key] for key in sample.keys()}
    expected_evidence_id = make_evidence_id(sample_dict)
    if sample_dict.get("evidence_id") != expected_evidence_id:
        audit.fail(
            "SUBJECT_INDEX_EVIDENCE_ID",
            "选科 SQLite 索引 evidence_id 与约定公式不一致",
            rel(DEFAULT_DB_PATH),
            {"expected": expected_evidence_id, "actual": sample_dict.get("evidence_id")},
        )

    audit.stats["subject_index_rows"] = actual_total
    audit.info("SUBJECT_INDEX", "选科 SQLite 索引完整性检查完成", rel(DEFAULT_DB_PATH), {"rows": actual_total})


def audit_scorelines(audit: Audit) -> None:
    data_2025 = load_json(ROOT / "processed/分数线/2025.json")
    expected = {
        ("普通类", "特殊类型招生控制线"): 521,
        ("普通类", "一段线"): 441,
        ("普通类", "二段线"): 150,
        ("普通类", "3+2对口贯通分段培养高职志愿填报资格线"): 391,
        ("体育类", "综合分一段线"): 566,
        ("体育类", "综合分二段线"): 428,
    }
    for (section, key), value in expected.items():
        if data_2025[section][key] != value:
            audit.fail("SCORELINE_2025_VALUE", "2025 分数线结构化数值与预期不一致", "processed/分数线/2025.json", {(section, key): data_2025[section][key]})
    pdf_path = ROOT / "raw/2025/分数线/附件1_夏季高考各类别分数线.pdf"
    with pdfplumber.open(str(pdf_path)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    for value in [521, 441, 150, 391, 566, 428, 286, 330]:
        if str(value) not in text:
            audit.fail("SCORELINE_PDF_TEXT", f"2025 分数线 PDF 文本中未找到数值 {value}", rel(pdf_path))
    hist = load_json(ROOT / "processed/分数线/历史分数线_2020-2024.json")
    if hist.get("quality_level") != "D":
        audit.fail("HIST_SCORELINE_QUALITY", "历史分数线 2020-2024 未标注 D 级线索", "processed/分数线/历史分数线_2020-2024.json")
    audit.warn("HIST_SCORELINE_NOT_OFFICIAL", "2020-2024 历史分数线为 D 级线索，正式方案前必须回查 sdzk.cn")
    audit.info("SCORELINES", "分数线检查完成")


def audit_metadata_and_sources(audit: Audit) -> None:
    metas = [
        ROOT / "processed/一分一段表/_meta.json",
        ROOT / "processed/投档表/_meta.json",
        ROOT / "processed/志愿计划/_meta.json",
        ROOT / "processed/选科要求/_meta.json",
        ROOT / "processed/分数线/_meta.json",
    ]
    for path in metas:
        meta = load_json(path)
        text = json.dumps(meta, ensure_ascii=False)
        if "quality_level" not in text:
            audit.fail("META_QUALITY_LEVEL", "_meta.json 缺少 quality_level", rel(path))
        if "verification_status" not in text:
            audit.fail("META_VERIFICATION", "_meta.json 缺少 verification_status", rel(path))
        if "山东省教育招生考试院" not in text and "sdzk.cn" not in text:
            audit.fail("META_OFFICIAL_SOURCE", "_meta.json 未记录山东省教育招生考试院或 sdzk.cn", rel(path))

    for cfg in SUBJECT_PDFS:
        if not cfg["pdf"].exists():
            audit.fail("SOURCE_FILE_MISSING", "选科要求原始 PDF 缺失", rel(cfg["pdf"]))
    for year in YEARS:
        required = [
            ROOT / f"raw/{year}/一分一段表.xls",
            ROOT / f"raw/{year}/常规批第1次投档表.xls",
            ROOT / f"raw/{year}/常规批第2次投档表",
            ROOT / f"raw/{year}/常规批第3次投档表",
            ROOT / f"raw/{year}/常规批第2次志愿计划",
            ROOT / f"raw/{year}/常规批第3次志愿计划",
            ROOT / f"raw/{year}/提前批第2次志愿计划",
            ROOT / f"raw/{year}/高职注册入学计划",
        ]
        for path in required:
            if not path.exists():
                audit.fail("RAW_SOURCE_MISSING", "raw 官方源文件/目录缺失", rel(path))
    audit.info("METADATA", "来源元数据与 raw 文件存在性检查完成")


def render_report(audit: Audit, full_subject_reextract: bool) -> str:
    counts = audit.counts()
    status = "通过" if counts["FAIL"] == 0 else "未通过"
    now = "2026-06-23"
    lines = [
        "---",
        "title: 数据准确性审计 2026-06-23",
        "tags: [lint, 数据审计, 官方来源, 高考]",
        "created: 2026-06-23",
        "updated: 2026-06-23",
        "sources: [\"processed/\", \"raw/\", \"scripts/audit_data_accuracy.py\"]",
        "---",
        "",
        "# 数据准确性审计 · 2026-06-23",
        "",
        "## 结论",
        "",
        f"**机器审计状态：{status}**",
        "",
        f"- FAIL：{counts['FAIL']}",
        f"- WARN：{counts['WARN']}",
        f"- INFO：{counts['INFO']}",
        f"- 选科要求 PDF 全量重抽取：{'已执行' if full_subject_reextract else '未执行'}",
        "",
        "## 审计范围",
        "",
        "- `processed/` CSV/JSON 同名文件一致性",
        "- 合并 JSON 与分文件总量一致性",
        "- 一分一段表：从 `raw/<year>/一分一段表.xls` 全量重抽取比对",
        "- 投档表：从 `raw/<year>/常规批第N次投档表` 全量重抽取比对",
        "- 志愿计划：从 `raw/<year>/*志愿计划` 全量重抽取比对",
        "- 选科要求：结构化字段自洽检查；如启用则从 4 个官方 PDF 全量重抽取比对",
        "- 分数线：2025 官方 PDF 文本核查；2020-2024 历史汇总质量等级核查",
        "- `_meta.json` 来源等级与核验状态字段",
        "",
        "## 统计",
        "",
        "```json",
        json.dumps(audit.stats, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 问题明细",
        "",
    ]
    for severity in ["FAIL", "WARN", "INFO"]:
        subset = [item for item in audit.items if item["severity"] == severity]
        lines.append(f"### {severity}（{len(subset)}）")
        lines.append("")
        if not subset:
            lines.append("- 无")
            lines.append("")
            continue
        for item in subset:
            detail = ""
            if item["detail"] is not None:
                detail = "；detail=" + json.dumps(item["detail"], ensure_ascii=False)[:1200]
            path = f" `{item['path']}`" if item["path"] else ""
            lines.append(f"- **{item['code']}**{path}：{item['message']}{detail}")
        lines.append("")
    lines.extend(
        [
            "## 使用限制",
            "",
            "- 只要存在 FAIL，不得把相关数据用于正式志愿方案。",
            "- WARN 不是自动错误，但必须在正式填报前人工复核。",
            "- 2020-2024 历史分数线当前为 D 级线索，不能作为正式填报依据。",
            "- 正式填报前仍需以山东省教育招生考试院最新发布为准。"
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-subject-reextract", action="store_true", help="Re-extract four subject requirement PDFs and compare with processed JSON.")
    parser.add_argument("--report", default="wiki/lint_2026-06-23_数据准确性审计.md")
    args = parser.parse_args()

    audit = Audit()
    audit_csv_json_pairs(audit)
    audit_combined_files(audit)
    audit_score_tables(audit)
    audit_admission(audit)
    audit_plans(audit)
    audit_subject_requirements(audit, args.full_subject_reextract)
    audit_subject_index(audit)
    audit_scorelines(audit)
    audit_metadata_and_sources(audit)

    report = render_report(audit, args.full_subject_reextract)
    report_path = ROOT / args.report
    report_path.write_text(report, encoding="utf-8")
    counts = audit.counts()
    print(json.dumps({"FAIL": counts["FAIL"], "WARN": counts["WARN"], "INFO": counts["INFO"], "report": rel(report_path)}, ensure_ascii=False, indent=2))
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())

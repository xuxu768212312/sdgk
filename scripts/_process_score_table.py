#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 2021-2025 一分一段表转为标准 CSV + JSON
列：year, score, total_count, total_cumulative,
     physics_count, physics_cumulative,
     chemistry_count, chemistry_cumulative,
     biology_count, biology_cumulative,
     politics_count, politics_cumulative,
     history_count, history_cumulative,
     geography_count, geography_cumulative
"""
import xlrd, csv, json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SUBJECTS = ['physics', 'chemistry', 'biology', 'politics', 'history', 'geography']
FIELDS = ['score', 'total_count', 'total_cumulative'] + \
         [field for s in SUBJECTS for field in (f'{s}_count', f'{s}_cumulative')]

def to_int(v):
    if v == '' or v is None:
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None

def process_year(year):
    src = f"raw/{year}/一分一段表.xls"
    wb = xlrd.open_workbook(src)
    sh = wb.sheet_by_index(0)
    rows = []
    for r in range(3, sh.nrows):
        score = sh.cell_value(r, 0)
        if score == '' or score is None:
            continue
        try:
            score = int(score)
        except (ValueError, TypeError):
            continue
        rec = {'year': year, 'score': score}
        # 全体: cols 1,2
        rec['total_count'] = to_int(sh.cell_value(r, 1))
        rec['total_cumulative'] = to_int(sh.cell_value(r, 2))
        # 6 科: 每科 2 列
        for i, subj in enumerate(SUBJECTS):
            base = 3 + i * 2
            rec[f'{subj}_count'] = to_int(sh.cell_value(r, base))
            rec[f'{subj}_cumulative'] = to_int(sh.cell_value(r, base + 1))
        rows.append(rec)
    return rows

all_data = {}
for year in [2021, 2022, 2023, 2024, 2025]:
    rows = process_year(year)
    all_data[year] = rows
    # CSV
    csv_path = f"processed/一分一段表/{year}.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['year'] + FIELDS)
        w.writeheader()
        w.writerows(rows)
    # JSON
    json_path = f"processed/一分一段表/{year}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"{year}: {len(rows)} 行 -> {csv_path}, {json_path}")

# 合并 JSON
with open("processed/一分一段表/all_years.json", 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)
print(f"\n合并: processed/一分一段表/all_years.json")

# 元数据
meta = {
    'dataset': '一分一段表',
    'publisher': '山东省教育招生考试院',
    'official_domain': 'sdzk.cn',
    'source_registry': [
        'raw/_common/来源索引/官方来源索引.md',
        'raw/_common/来源索引/补充官方数据来源索引.md',
    ],
    'source_file_pattern': 'raw/<year>/一分一段表.xls',
    'quality_level': 'A',
    'verification_status': 'official_excel_extracted',
    'extract_script': 'scripts/_process_score_table.py',
    'years': [2021, 2022, 2023, 2024, 2025],
    'fields': FIELDS,
    'description': '山东夏季高考文化成绩一分一段表，含全体和6科选考的本段/累计人数',
    'note': '分数从高到低；累计人数为该分数及以上的总人数；选考列中 None 表示当年该分数段无此科考生'
}
with open("processed/一分一段表/_meta.json", 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print("元数据: processed/一分一段表/_meta.json")

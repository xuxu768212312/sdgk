#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 2021-2025 普通类常规批第 1/2/3 次投档表转为标准 CSV + JSON
统一字段：year, round, major_code, major_name, school_code, school_name, plan_count, min_rank
"""
import xlrd, csv, json, os, glob, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def to_int(v):
    if v == '' or v is None:
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None

def split_major(v):
    """拆分专业代号和名称，如 '17文科试验班类(不限选考科目类专业)'"""
    if not v or v == '':
        return '', ''
    s = str(v).strip()
    # 代号通常是开头的数字/字母（1-2 个字符）
    m = re.match(r'^([A-Za-z0-9]{1,3})(.*)$', s)
    if m:
        return m.group(1), m.group(2).strip()
    return '', s

def split_school(v):
    """拆分院校代号和名称，如 'A001北京大学'"""
    if not v or v == '':
        return '', ''
    s = str(v).strip()
    # 院校代号通常是开头的字母+数字（如 A001, Y030）
    m = re.match(r'^([A-Z]\d{3,4})(.*)$', s)
    if m:
        return m.group(1), m.group(2).strip()
    return '', s

def find_header_row(sh):
    """找到表头行（含'专业'和'院校'的行）"""
    for r in range(min(5, sh.nrows)):
        row = [str(sh.cell_value(r, c)).strip() for c in range(sh.ncols)]
        joined = '|'.join(row)
        if '专业' in joined and '院校' in joined:
            return r
    return 1

def find_col_indices(sh, header_row):
    """找到各列的索引，处理首列可能为空的情况"""
    headers = [str(sh.cell_value(header_row, c)).strip() for c in range(sh.ncols)]
    cols = {'major': -1, 'school': -1, 'plan': -1, 'rank': -1}
    for i, h in enumerate(headers):
        if '专业' in h and cols['major'] < 0:
            cols['major'] = i
        elif '院校' in h and cols['school'] < 0:
            cols['school'] = i
        elif '计划' in h and cols['plan'] < 0:
            cols['plan'] = i
        elif ('位次' in h or '最低位' in h) and cols['rank'] < 0:
            cols['rank'] = i
    return cols

def process_file(filepath, year, round_num):
    wb = xlrd.open_workbook(filepath)
    sh = wb.sheet_by_index(0)
    header_row = find_header_row(sh)
    cols = find_col_indices(sh, header_row)
    rows = []
    for r in range(header_row + 1, sh.nrows):
        major_raw = sh.cell_value(r, cols['major'])
        school_raw = sh.cell_value(r, cols['school'])
        if not major_raw or not school_raw:
            continue
        major_code, major_name = split_major(major_raw)
        school_code, school_name = split_school(school_raw)
        rec = {
            'year': year,
            'round': round_num,
            'major_code': major_code,
            'major_name': major_name,
            'school_code': school_code,
            'school_name': school_name,
            'plan_count': to_int(sh.cell_value(r, cols['plan'])),
            'min_rank': to_int(sh.cell_value(r, cols['rank'])),
        }
        rows.append(rec)
    return rows

# 处理各年份
all_data = {}
for year in [2021, 2022, 2023, 2024, 2025]:
    all_data[year] = {}
    # 第 1 次
    f1 = f"raw/{year}/常规批第1次投档表.xls"
    rows1 = process_file(f1, year, 1)
    all_data[year][1] = rows1
    # 第 2 次：找附件里含"普通类"的 xls
    d2 = f"raw/{year}/常规批第2次投档表"
    files2 = glob.glob(f"{d2}/*.xls")
    # 优先普通类
    f2 = None
    for f in files2:
        if '普通类' in os.path.basename(f):
            f2 = f
            break
    if not f2 and files2:
        f2 = files2[0]
    rows2 = process_file(f2, year, 2) if f2 else []
    all_data[year][2] = rows2
    # 第 3 次：找附件里含"普通类"的 xls
    d3 = f"raw/{year}/常规批第3次投档表"
    files3 = glob.glob(f"{d3}/*.xls")
    f3 = None
    for f in files3:
        if '普通类' in os.path.basename(f):
            f3 = f
            break
    if not f3 and files3:
        f3 = files3[0]
    rows3 = process_file(f3, year, 3) if f3 else []
    all_data[year][3] = rows3

    # 写文件
    for rnd, rows in [(1, rows1), (2, rows2), (3, rows3)]:
        csv_path = f"processed/投档表/{year}_round{rnd}.csv"
        json_path = f"processed/投档表/{year}_round{rnd}.json"
        with open(csv_path, 'w', newline='', encoding='utf-8') as cf:
            w = csv.DictWriter(cf, fieldnames=['year', 'round', 'major_code', 'major_name',
                                               'school_code', 'school_name', 'plan_count', 'min_rank'])
            w.writeheader()
            w.writerows(rows)
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(rows, jf, ensure_ascii=False, indent=2)
    print(f"{year}: R1={len(rows1)} R2={len(rows2)} R3={len(rows3)}")

# 合并 JSON
flat = []
for y, rounds in all_data.items():
    for r, rows in rounds.items():
        flat.extend(rows)
with open("processed/投档表/all_years_all_rounds.json", 'w', encoding='utf-8') as f:
    json.dump(flat, f, ensure_ascii=False, indent=2)

meta = {
    'dataset': '普通类常规批投档表',
    'years': [2021, 2022, 2023, 2024, 2025],
    'rounds': [1, 2, 3],
    'fields': ['year', 'round', 'major_code', 'major_name', 'school_code', 'school_name', 'plan_count', 'min_rank'],
    'description': '山东夏季高考普通类常规批第 1/2/3 次志愿投档情况',
    'notes': [
        'round=1 对应第 1 次志愿（本科计划）',
        'round=2 对应第 2 次志愿（剩余本科+专科计划）',
        'round=3 对应第 3 次志愿（剩余计划）',
        'major_code/school_code 已从原始合并字段拆分',
        '体育类投档表未纳入此数据集，仅普通类',
    ]
}
with open("processed/投档表/_meta.json", 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"\n合并: processed/投档表/all_years_all_rounds.json (共 {len(flat)} 条)")
print("元数据: processed/投档表/_meta.json")

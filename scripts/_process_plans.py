#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整理志愿计划类数据
- 常规批第2次志愿计划（剩余本科计划）
- 常规批第3次志愿计划
- 提前批第2次志愿计划（普通类）
- 高职注册入学计划（普通类/艺术类/体育类/春季高考）

统一字段：year, batch, category, school_code, school_name,
         major_code, major_name, subject_requirement, level, study_years, plan_count, annual_fee, remark
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

def split_major_name(v):
    """拆分专业代号和名称，如 '52 城乡规划...' -> ('52', '城乡规划...')
       '0B 资源勘查工程...' -> ('0B', '资源勘查工程...')
       'E7 数学与应用数学...' -> ('E7', '数学与应用数学...')"""
    if not v:
        return '', ''
    s = str(v).strip()
    m = re.match(r'^([0-9A-Za-z]{1,3})\s+(.*)$', s)
    if m:
        return m.group(1), m.group(2).strip()
    return '', s

def find_header_row(sh):
    for r in range(min(5, sh.nrows)):
        row = [str(sh.cell_value(r, c)).strip() for c in range(sh.ncols)]
        if '院校代号' in row:
            return r
    return None

def process_plan_file(filepath, year, batch, category):
    """处理计划类文件"""
    wb = xlrd.open_workbook(filepath)
    sh = wb.sheet_by_index(0)
    header_row = find_header_row(sh)

    # 定位列
    col_school_code = 0
    col_name = 1
    col_subject = 2
    col_level = -1
    col_years = -1
    col_plan = -1
    col_fee = -1
    if header_row is None:
        # 少数注册入学附件无表头，前两行为标题/说明，数据从第 3 行开始。
        # 常见列序：院校代号、院校/专业名称、选科要求、学制、计划数、收费。
        data_start_row = 2
        col_years = 3
        col_plan = 4
        col_fee = 5
    else:
        data_start_row = header_row + 1
        headers = [str(sh.cell_value(header_row, c)).strip() for c in range(sh.ncols)]
        for i, h in enumerate(headers):
            if '层次' in h:
                col_level = i
            elif '学制' in h:
                col_years = i
            elif '计划' in h:
                col_plan = i
            elif '收费' in h:
                col_fee = i

    rows = []
    current_school_code = ''
    current_school_name = ''
    for r in range(data_start_row, sh.nrows):
        school_code = str(sh.cell_value(r, col_school_code)).strip()
        name = str(sh.cell_value(r, col_name)).strip()
        if not name:
            continue
        if school_code:
            # 院校行
            current_school_code = school_code
            current_school_name = name
            continue
        # 专业行
        major_code, major_name = split_major_name(name)
        rec = {
            'year': year,
            'batch': batch,
            'category': category,
            'school_code': current_school_code,
            'school_name': current_school_name,
            'major_code': major_code,
            'major_name': major_name,
            'subject_requirement': str(sh.cell_value(r, col_subject)).strip() if col_subject >= 0 else '',
            'level': str(sh.cell_value(r, col_level)).strip() if col_level >= 0 else '',
            'study_years': str(sh.cell_value(r, col_years)).strip() if col_years >= 0 else '',
            'plan_count': to_int(sh.cell_value(r, col_plan)) if col_plan >= 0 else None,
            'annual_fee': str(sh.cell_value(r, col_fee)).strip() if col_fee >= 0 else '',
        }
        rows.append(rec)
    return rows

# 处理各年份
all_data = []
for year in [2021, 2022, 2023, 2024, 2025]:
    year_data = []
    # 常规批第2次志愿计划
    d = f"raw/{year}/常规批第2次志愿计划"
    files = sorted(glob.glob(f"{d}/*.xls"))
    if files:
        # 选普通类
        f = next((x for x in files if '普通类' in os.path.basename(x)), files[0])
        rows = process_plan_file(f, year, '常规批第2次', '普通类')
        year_data.extend(rows)
        print(f"{year} 常规批第2次: {len(rows)}")

    # 常规批第3次志愿计划
    d = f"raw/{year}/常规批第3次志愿计划"
    files = sorted(glob.glob(f"{d}/*.xls"))
    if files:
        f = next((x for x in files if '普通类' in os.path.basename(x)), files[0])
        rows = process_plan_file(f, year, '常规批第3次', '普通类')
        year_data.extend(rows)
        print(f"{year} 常规批第3次: {len(rows)}")

    # 提前批第2次志愿计划
    d = f"raw/{year}/提前批第2次志愿计划"
    files = sorted(glob.glob(f"{d}/*.xls"))
    if files:
        f = next((x for x in files if '普通类' in os.path.basename(x)), files[0])
        rows = process_plan_file(f, year, '提前批第2次', '普通类')
        year_data.extend(rows)
        print(f"{year} 提前批第2次: {len(rows)}")

    # 高职注册入学计划（4 类）
    d = f"raw/{year}/高职注册入学计划"
    files = sorted(glob.glob(f"{d}/*.xls"))
    cat_map = {'普通类': '普通类', '艺术类': '艺术类', '体育类': '体育类', '春季高考': '春季高考'}
    for f in files:
        bn = os.path.basename(f)
        for key, cat in cat_map.items():
            if key in bn:
                rows = process_plan_file(f, year, '高职注册入学', cat)
                year_data.extend(rows)
                print(f"{year} 高职注册入学({cat}): {len(rows)}")
                break

    # 写年度文件
    if year_data:
        csv_path = f"processed/志愿计划/{year}.csv"
        json_path = f"processed/志愿计划/{year}.json"
        fields = ['year', 'batch', 'category', 'school_code', 'school_name',
                  'major_code', 'major_name', 'subject_requirement', 'level',
                  'study_years', 'plan_count', 'annual_fee']
        with open(csv_path, 'w', newline='', encoding='utf-8') as cf:
            w = csv.DictWriter(cf, fieldnames=fields)
            w.writeheader()
            w.writerows(year_data)
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(year_data, jf, ensure_ascii=False, indent=2)
    all_data.extend(year_data)

# 合并
with open("processed/志愿计划/all_years_all_batches.json", 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

meta = {
    'dataset': '志愿计划类数据',
    'publisher': '山东省教育招生考试院',
    'official_domain': 'sdzk.cn',
    'source_registry': [
        'raw/_common/来源索引/官方来源索引.md',
        'raw/_common/来源索引/补充官方数据来源索引.md',
    ],
    'source_file_patterns': [
        'raw/<year>/常规批第2次志愿计划/*.xls',
        'raw/<year>/常规批第3次志愿计划/*.xls',
        'raw/<year>/提前批第2次志愿计划/*.xls',
        'raw/<year>/高职注册入学计划/*.xls',
    ],
    'quality_level': 'A',
    'verification_status': 'official_excel_extracted',
    'extract_script': 'scripts/_process_plans.py',
    'years': [2021, 2022, 2023, 2024, 2025],
    'batches': ['常规批第2次', '常规批第3次', '提前批第2次', '高职注册入学'],
    'categories': ['普通类', '艺术类', '体育类', '春季高考'],
    'fields': ['year', 'batch', 'category', 'school_code', 'school_name',
               'major_code', 'major_name', 'subject_requirement', 'level',
               'study_years', 'plan_count', 'annual_fee'],
    'description': '山东夏季高考各批次志愿计划数据',
    'notes': [
        '常规批第2次志愿计划 = 剩余本科计划（第1次未完成的本科计划）',
        '常规批第3次志愿计划 = 剩余计划（含专科）',
        '提前批第2次志愿计划 = 第1次未完成的提前批计划',
        '高职注册入学计划 = 专科录取后期的注册入学招生计划',
        'major_code 从"专业代号 名称"格式拆分',
        '院校行和专业行通过"院校代号"列是否为空区分',
    ]
}
with open("processed/志愿计划/_meta.json", 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"\n合并: processed/志愿计划/all_years_all_batches.json (共 {len(all_data)} 条)")
print("元数据: processed/志愿计划/_meta.json")

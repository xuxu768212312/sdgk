#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从选科要求 PDF 提取为标准 CSV + JSON
4 个 PDF：
  2024 本科（适用 2025-2026）
  2024 专科（适用 2025-2026）
  2027 本科（2027 及以后）
  2027 专科（2027 及以后）

统一字段：
  edition, level, school_code, school_name, major_code, major_name,
  subject_requirement_raw, subject_requirement_type, subjects_list, province

subject_requirement_type:
  none  = 不提科目要求
  one   = 1 门科目（必须选考）
  two   = 2 门科目（均须选考）
  three = 3 门科目（均须选考）
"""
import pdfplumber, csv, json, os, re, sys, io, time
from subject_eligibility import parse_subject_requirement
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PDF_DIR = "raw/2026/政策文件原件"
OUT_DIR = "processed/选科要求"
os.makedirs(OUT_DIR, exist_ok=True)

PDFS = [
    {
        'edition': '2024',  # 适用 2025-2026
        'level': '本科',
        'pdf': f"{PDF_DIR}/2024通用版普通高校拟在山东招生专业类选考科目要求（本科，适用2025-2026）.pdf",
        'json': f"{OUT_DIR}/2024版本科.json",
        'csv': f"{OUT_DIR}/2024版本科.csv",
    },
    {
        'edition': '2024',
        'level': '专科',
        'pdf': f"{PDF_DIR}/2024通用版普通高校拟在山东招生专业类选考科目要求（专科，适用2025-2026）.pdf",
        'json': f"{OUT_DIR}/2024版专科.json",
        'csv': f"{OUT_DIR}/2024版专科.csv",
    },
    {
        'edition': '2027',
        'level': '本科',
        'pdf': f"{PDF_DIR}/2027通用版普通高校拟在山东招生专业类选考科目要求（本科，2027及以后）.pdf",
        'json': f"{OUT_DIR}/2027版本科.json",
        'csv': f"{OUT_DIR}/2027版本科.csv",
    },
    {
        'edition': '2027',
        'level': '专科',
        'pdf': f"{PDF_DIR}/2027通用版普通高校拟在山东招生专业类选考科目要求（专科，2027及以后）.pdf",
        'json': f"{OUT_DIR}/2027版专科.json",
        'csv': f"{OUT_DIR}/2027版专科.csv",
    },
]

SUBJECT_MAP = {
    '物理': 'physics',
    '化学': 'chemistry',
    '生物': 'biology',
    '思想政治': 'politics',
    '历史': 'history',
    '地理': 'geography',
}

def parse_requirement(raw):
    """解析'选考科目要求'原始文本
    返回 (type, subjects_list)
    type: none / one / two / three / any
    subjects_list: 科目中文列表

    示例：
      '不提科目要求' -> ('none', [])
      '思想政治(1门科目考生必须选考方可报考)' -> ('one', ['思想政治'])
      '物理,化学(2门科目考生均须选考方可报考)' -> ('two', ['物理', '化学'])
      '物理,化学,生物(3门科目考生均须选考方可报考)' -> ('three', ['物理', '化学', '生物'])
      '物理或化学或生物(2门科目考生选考其中1门即可报考)' -> ('any', ['物理', '化学', '生物'])
    """
    return parse_subject_requirement(raw)

def process_pdf(cfg):
    pdf_path = cfg['pdf']
    print(f"\n处理: {os.path.basename(pdf_path)}")
    if not os.path.exists(pdf_path):
        print(f"  ✗ 文件不存在")
        return []

    start = time.time()
    all_rows = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for tbl in tables:
                if len(tbl) < 2:
                    continue
                # 跳过表头
                for row in tbl[1:]:
                    if len(row) < 6:
                        continue
                    school_code = (row[0] or '').replace('\n', '').strip()
                    school_name = (row[1] or '').replace('\n', '').strip()
                    major_code = (row[2] or '').replace('\n', '').strip()
                    major_name = (row[3] or '').replace('\n', '').strip()
                    subject_raw = (row[4] or '').replace('\n', '').strip()
                    province = (row[5] or '').replace('\n', '').strip()

                    if not school_code or not school_name:
                        continue
                    # 过滤无效行（school_code 应为 5 位数字）
                    if not re.match(r'^\d{5}$', school_code):
                        continue

                    req_type, subjects = parse_requirement(subject_raw)
                    rec = {
                        'edition': cfg['edition'],
                        'level': cfg['level'],
                        'school_code': school_code,
                        'school_name': school_name,
                        'major_code': major_code,
                        'major_name': major_name,
                        'subject_requirement_raw': subject_raw,
                        'subject_requirement_type': req_type,
                        'subjects_list': '|'.join(subjects),
                        'province': province,
                    }
                    all_rows.append(rec)
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start
                eta = elapsed / (i + 1) * (total_pages - i - 1)
                print(f"  {i+1}/{total_pages} 页, {len(all_rows)} 条, 用时 {elapsed:.0f}s, 剩 {eta:.0f}s")

    # 写 CSV + JSON
    fields = ['edition', 'level', 'school_code', 'school_name', 'major_code', 'major_name',
              'subject_requirement_raw', 'subject_requirement_type', 'subjects_list', 'province']
    with open(cfg['csv'], 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)
    with open(cfg['json'], 'w', encoding='utf-8') as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start
    print(f"  完成: {len(all_rows)} 条, 用时 {elapsed:.0f}s")
    print(f"  -> {cfg['csv']}")
    print(f"  -> {cfg['json']}")
    return all_rows

# 处理所有 PDF
all_data = []
for cfg in PDFS:
    rows = process_pdf(cfg)
    all_data.extend(rows)

# 合并
with open(f"{OUT_DIR}/all_requirements.json", 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

# 元数据
meta = {
    'dataset': '选科要求',
    'editions': ['2024（适用2025-2026）', '2027（2027及以后）'],
    'levels': ['本科', '专科'],
    'fields': ['edition', 'level', 'school_code', 'school_name', 'major_code', 'major_name',
               'subject_requirement_raw', 'subject_requirement_type', 'subjects_list', 'province'],
    'subject_requirement_type': {
        'none': '不提科目要求（任何选科组合可报）',
        'one': '1 门科目必须选考',
        'two': '2 门科目均须选考',
        'three': '3 门科目均须选考',
        'any': '多门科目中任选 1 门即可报考（"或"关系）',
    },
    'subjects_list': '用 | 分隔的科目中文名',
    'total_count': len(all_data),
    'notes': [
        '2024 版适用 2025-2026 届（2026 届主要使用此版）',
        '2027 版适用 2027 届及以后',
        '最终以当年招生计划为准',
    ],
}
with open(f"{OUT_DIR}/_meta.json", 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"\n=== 汇总 ===")
print(f"总计: {len(all_data)} 条")
print(f"合并: {OUT_DIR}/all_requirements.json")
print(f"元数据: {OUT_DIR}/_meta.json")

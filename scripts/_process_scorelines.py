#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 2025 年分数线 PDF 提取数据，整理为标准 JSON
"""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pdfplumber

f = "raw/2025/分数线/附件1_夏季高考各类别分数线.pdf"
with pdfplumber.open(f) as pdf:
    text = pdf.pages[0].extract_text()

print("=== 原始文本 ===")
print(text)
print("\n=== 解析 ===")

# 2025 数据结构
data_2025 = {
    'year': 2025,
    '普通类': {
        '特殊类型招生控制线': 521,
        '一段线': 441,
        '二段线': 150,
        '3+2对口贯通分段培养高职志愿填报资格线': 391,
    },
    '艺术类': {
        '本科文化控制线': {
            '舞蹈类、美术与设计类、播音与主持类': 441,
            '表（导）演类、音乐类、书法类': 330,
            '戏曲类': 286,
        },
        '专科文化控制线': 150,
    },
    '体育类': {
        '综合分一段线': 566,
        '综合分二段线': 428,
        '本科文化控制线': 286,
        '专科文化控制线': 150,
    },
    'notes': [
        '高水平运动队：世界一流大学建设高校本科文化控制线 441 分，其他高校 352 分',
        '艺术类本科提前批校考专业：文化成绩须达 441 分或招生高校破格录取要求',
        '体育类综合分 = 专业成绩 70% + 文化成绩 30%',
    ],
    '发布日期': '2025-06-25',
    '来源': '山东省教育招生考试院',
}

with open("processed/分数线/2025.json", 'w', encoding='utf-8') as f:
    json.dump(data_2025, f, ensure_ascii=False, indent=2)
print(f"已写入: processed/分数线/2025.json")

# 2021-2024 的占位
todo = {
    'year': [2021, 2022, 2023, 2024],
    'status': 'pending',
    'reason': '官方 HTML 页面未提供 PDF 附件，需重新下载页面快照或手动录入',
    'official_urls': {
        2021: 'https://www.sdzk.cn/NewsInfo.aspx?NewsID=5460',
        2022: 'https://www.sdzk.cn/NewsInfo.aspx?NewsID=5788',
        2023: 'https://www.sdzk.cn/NewsInfo.aspx?NewsID=6210',
        2024: 'https://www.sdzk.cn/NewsInfo.aspx?NewsID=6579',
    },
    'local_html': {
        2021: 'raw/2021/分数线/2021_页面.html',
        2022: 'raw/2022/分数线/2022_页面.html',
        2023: 'raw/2023/分数线/2023_页面.html',
        2024: 'raw/2024/分数线/2024_页面.html',
    },
}
with open("processed/分数线/_pending_2021_2024.json", 'w', encoding='utf-8') as f:
    json.dump(todo, f, ensure_ascii=False, indent=2)
print("待办: processed/分数线/_pending_2021_2024.json")

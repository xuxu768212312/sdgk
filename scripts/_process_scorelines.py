#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build processed scoreline JSON files from official sdzk source snapshots."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


HISTORICAL = {
    2020: {
        "source_url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=4941",
        "source_page": "raw/2020/分数线/2020_页面.html",
        "source_image": "raw/2020/分数线/20.png",
        "发布日期": "2020-07-26",
        "data": {
            "普通类": {
                "特殊类型招生控制线": 532,
                "一段线": 449,
                "二段线": 150,
                "3+2对口贯通分段培养高职志愿填报资格线": 399,
            },
            "艺术类": {
                "本科文化控制线": {
                    "文学编导类、播音主持类、摄影类": 381,
                    "美术类、音乐类、书法类": 314,
                    "舞蹈类、影视戏剧表演类、服装表演(模特)类": 291,
                },
                "专科文化控制线": 150,
            },
            "体育类": {
                "综合分一段线": 561,
                "综合分二段线": 457,
            },
        },
    },
    2021: {
        "source_url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=5460",
        "source_page": "raw/2021/分数线/2021_页面.html",
        "source_image": "raw/2021/分数线/21.png",
        "发布日期": "2021-06-25",
        "data": {
            "普通类": {
                "特殊类型招生控制线": 518,
                "一段线": 444,
                "二段线": 150,
                "3+2对口贯通分段培养高职志愿填报资格线": 394,
            },
            "艺术类": {
                "本科文化控制线": {
                    "文学编导类、播音主持类、摄影类": 444,
                    "美术类、音乐类、书法类、航空服务艺术类": 333,
                    "舞蹈类、影视戏剧表演类、服装表演类": 288,
                },
                "专科文化控制线": 150,
            },
            "体育类": {
                "综合分一段线": 569,
                "综合分二段线": 470,
            },
        },
    },
    2022: {
        "source_url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=5788",
        "source_page": "raw/2022/分数线/2022_页面.html",
        "source_image": "raw/2022/分数线/2022062501.png",
        "发布日期": "2022-06-25",
        "data": {
            "普通类": {
                "特殊类型招生控制线": 513,
                "一段线": 437,
                "二段线": 150,
                "3+2对口贯通分段培养高职志愿填报资格线": 387,
            },
            "艺术类": {
                "本科文化控制线": {
                    "文学编导类、播音主持类、摄影类": 437,
                    "美术类、音乐类、书法类、航空服务艺术类": 327,
                    "舞蹈类、影视戏剧表演类、服装表演类": 284,
                },
                "专科文化控制线": 150,
            },
            "体育类": {
                "综合分一段线": 583,
                "综合分二段线": 474,
            },
        },
    },
    2023: {
        "source_url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6210",
        "source_page": "raw/2023/分数线/2023_页面.html",
        "source_image": "raw/2023/分数线/23.png",
        "发布日期": "2023-06-25",
        "data": {
            "普通类": {
                "特殊类型招生控制线": 520,
                "一段线": 443,
                "二段线": 150,
                "3+2对口贯通分段培养高职志愿填报资格线": 393,
            },
            "艺术类": {
                "本科文化控制线": {
                    "文学编导类、播音主持类、摄影类": 443,
                    "美术类、音乐类、书法类、航空服务艺术类": 332,
                    "舞蹈类、戏剧影视表演类、服装表演类": 287,
                },
                "专科文化控制线": 150,
            },
            "体育类": {
                "综合分一段线": 587,
                "综合分二段线": 480,
            },
        },
    },
    2024: {
        "source_url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6579",
        "source_page": "raw/2024/分数线/2024_页面.html",
        "source_image": "raw/2024/分数线/24.png",
        "发布日期": "2024-06-25",
        "data": {
            "普通类": {
                "特殊类型招生控制线": 521,
                "一段线": 444,
                "二段线": 150,
                "3+2对口贯通分段培养高职志愿填报资格线": 394,
            },
            "艺术类": {
                "本科文化控制线": {
                    "播音与主持类": 444,
                    "美术与设计类、音乐类、书法类": 333,
                    "舞蹈类、表（导）演类、戏曲类": 288,
                },
                "专科文化控制线": 150,
            },
            "体育类": {
                "综合分一段线": 594,
                "综合分二段线": 470,
            },
        },
    },
}

DATA_2025 = {
    "year": 2025,
    "普通类": {
        "特殊类型招生控制线": 521,
        "一段线": 441,
        "二段线": 150,
        "3+2对口贯通分段培养高职志愿填报资格线": 391,
    },
    "艺术类": {
        "本科文化控制线": {
            "舞蹈类、美术与设计类、播音与主持类": 441,
            "表（导）演类、音乐类、书法类": 330,
            "戏曲类": 286,
        },
        "专科文化控制线": 150,
    },
    "体育类": {
        "综合分一段线": 566,
        "综合分二段线": 428,
        "本科文化控制线": 286,
        "专科文化控制线": 150,
    },
    "notes": [
        "高水平运动队：世界一流大学建设高校本科文化控制线 441 分，其他高校 352 分",
        "艺术类本科提前批校考专业：文化成绩须达 441 分或招生高校破格录取要求",
        "体育类综合分 = 专业成绩 70% + 文化成绩 30%",
    ],
    "发布日期": "2025-06-25",
    "来源": "山东省教育招生考试院",
    "source_url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6941",
    "source_file": "raw/2025/分数线/附件1_夏季高考各类别分数线.pdf",
    "quality_level": "A",
    "verification_status": "official_pdf_extracted",
}


def build_historical() -> dict:
    data = {}
    sources = []
    for year, item in HISTORICAL.items():
        image = ROOT / item["source_image"]
        page = ROOT / item["source_page"]
        if not image.exists():
            raise FileNotFoundError(image)
        if not page.exists():
            raise FileNotFoundError(page)
        data[str(year)] = item["data"]
        sources.append(
            {
                "year": year,
                "source_url": item["source_url"],
                "source_page": item["source_page"],
                "source_image": item["source_image"],
                "source_image_sha256": sha256_file(image),
                "publisher": "山东省教育招生考试院",
                "published_date": item["发布日期"],
                "quality_level": "B",
                "verification_status": "official_image_manual_transcription_checked",
            }
        )

    return {
        "说明": "2020-2024 山东高考分数线汇总（山东省教育招生考试院官方页面图片公告转录）",
        "quality_level": "B",
        "verification_status": "official_sdzk_image_manual_transcription_checked",
        "publisher": "山东省教育招生考试院",
        "official_domain": "sdzk.cn",
        "use_limit": "可作为历史趋势和正式方案辅助依据；正式填报仍以当年山东省教育招生考试院最新公告为准。",
        "sources": sources,
        "data": data,
        "注": "2020-2023 艺术类分类名称沿用当年官方公告；2024 起按新艺术类分类。图片公告为官方原文，结构化值为人工转录并经审计脚本核验来源文件存在与 SHA256。",
    }


def build_meta() -> dict:
    historical_sources = [
        {
            "year": src["year"],
            "source_url": src["source_url"],
            "source_file": src["source_image"],
            "source_page": src["source_page"],
            "source_image_sha256": src["source_image_sha256"],
        }
        for src in build_historical()["sources"]
    ]
    pdf = ROOT / DATA_2025["source_file"]
    return {
        "dataset": "分数线",
        "publisher_primary": "山东省教育招生考试院",
        "official_domain": "sdzk.cn",
        "fields": {
            "year": "年份",
            "普通类": "普通类分数线",
            "艺术类": "艺术类文化控制线",
            "体育类": "体育类综合分线与文化控制线",
        },
        "files": [
            {
                "file": "processed/分数线/2025.json",
                "source_file": DATA_2025["source_file"],
                "source_url": DATA_2025["source_url"],
                "source_sha256": sha256_file(pdf),
                "publisher": "山东省教育招生考试院",
                "quality_level": "A",
                "verification_status": "official_pdf_extracted",
                "use_limit": "可作为正式决策依据；正式填报前仍需核查当年最新公告。",
            },
            {
                "file": "processed/分数线/历史分数线_2020-2024.json",
                "source_files": historical_sources,
                "publisher": "山东省教育招生考试院",
                "quality_level": "B",
                "verification_status": "official_sdzk_image_manual_transcription_checked",
                "use_limit": "可作为历史趋势和正式方案辅助依据；正式填报仍以当年最新公告为准。",
            },
        ],
        "notes": [
            "山东高考正式分数线以山东省教育招生考试院最新发布为准。",
            "2020-2024 年度公告为图片形式，结构化值按官方图片转录，保留页面、图片与 SHA256 证据。",
        ],
    }


def main() -> int:
    out_dir = ROOT / "processed/分数线"
    out_dir.mkdir(parents=True, exist_ok=True)

    pdf = ROOT / DATA_2025["source_file"]
    if not pdf.exists():
        raise FileNotFoundError(pdf)

    (out_dir / "2025.json").write_text(json.dumps(DATA_2025, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "历史分数线_2020-2024.json").write_text(
        json.dumps(build_historical(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "_meta.json").write_text(json.dumps(build_meta(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    pending = out_dir / "_pending_2021_2024.json"
    if pending.exists():
        pending.unlink()

    print(f"wrote {rel(out_dir / '2025.json')}")
    print(f"wrote {rel(out_dir / '历史分数线_2020-2024.json')}")
    print(f"wrote {rel(out_dir / '_meta.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

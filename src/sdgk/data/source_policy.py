#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classify internet sources before they can influence admission strategy.

This script is intentionally conservative: it does not fetch the URL. It only
decides the maximum quality level and allowed usage based on the URL domain and
the repository's governance rules.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


PRIMARY_SD_DOMAINS = {"sdzk.cn", "www.sdzk.cn", "wsbm.sdzk.cn"}
NATIONAL_OFFICIAL_DOMAINS = {
    "moe.gov.cn",
    "www.moe.gov.cn",
    "neea.edu.cn",
    "www.neea.edu.cn",
    "chsi.com.cn",
    "www.chsi.com.cn",
    "gaokao.chsi.com.cn",
}
SHANDONG_OFFICIAL_DOMAINS = {"edu.shandong.gov.cn"}
THIRD_PARTY_CLUE_DOMAINS = {
    "eol.cn",
    "gaokao.eol.cn",
    "zhihu.com",
    "www.zhihu.com",
    "sohu.com",
    "www.sohu.com",
    "weibo.com",
    "mp.weixin.qq.com",
}


def normalize_domain(netloc: str) -> str:
    domain = netloc.lower().split("@")[-1].split(":")[0].strip(".")
    if domain.startswith("www."):
        return domain
    return domain


def is_school_official_domain(domain: str) -> bool:
    return domain.endswith(".edu.cn") or domain.endswith(".edu")


def classify_url(url: str) -> Dict[str, Any]:
    parsed = urlparse(url.strip())
    domain = normalize_domain(parsed.netloc)
    result: Dict[str, Any] = {
        "url": url,
        "domain": domain,
        "quality_ceiling": "D",
        "formal_decision_allowed": False,
        "allowed_use": "线索；不得作为正式方案数值依据",
        "required_action": "必须回查山东省教育招生考试院或对应官方原文",
        "source_role": "third_party_or_unknown",
    }

    if parsed.scheme not in {"http", "https"} or not domain:
        result.update(
            {
                "quality_ceiling": "D",
                "allowed_use": "无效 URL；不得使用",
                "required_action": "修正 URL 后重新分类",
                "source_role": "invalid_url",
            }
        )
        return result

    if domain in PRIMARY_SD_DOMAINS:
        result.update(
            {
                "quality_ceiling": "S",
                "formal_decision_allowed": True,
                "allowed_use": "山东高考政策、计划、分数线、一分一段、投档、缺额、填报时间的正式主源",
                "required_action": "下载/保存官方原文或附件到 raw/，再由脚本生成 processed/",
                "source_role": "sdzk_primary",
            }
        )
    elif domain in NATIONAL_OFFICIAL_DOMAINS:
        result.update(
            {
                "quality_ceiling": "C",
                "formal_decision_allowed": False,
                "allowed_use": "招生章程、教育部/阳光高考合规辅助；不得替代山东考试院计划/投档/位次数值",
                "required_action": "仅作合规核查；若涉及山东招生计划或投档，必须回查 sdzk.cn",
                "source_role": "national_official_auxiliary",
            }
        )
    elif domain in SHANDONG_OFFICIAL_DOMAINS:
        result.update(
            {
                "quality_ceiling": "C",
                "formal_decision_allowed": False,
                "allowed_use": "山东教育政策辅助；不得替代山东省教育招生考试院招生录取数据",
                "required_action": "用于政策背景；正式招生数据必须回查 sdzk.cn",
                "source_role": "province_official_auxiliary",
            }
        )
    elif is_school_official_domain(domain):
        result.update(
            {
                "quality_ceiling": "C",
                "formal_decision_allowed": False,
                "allowed_use": "高校招生章程、体检/单科/语种/校区/学费等合规辅助",
                "required_action": "只用于高校自身章程事项；山东计划数和投档仍以 sdzk.cn 为准",
                "source_role": "school_official_auxiliary",
            }
        )
    elif domain in THIRD_PARTY_CLUE_DOMAINS:
        result.update(
            {
                "quality_ceiling": "D",
                "formal_decision_allowed": False,
                "allowed_use": "第三方线索；禁止进入正式方案数值依据",
                "required_action": "只能用于发现线索，必须回查官方来源后才能引用",
                "source_role": "third_party_clue",
            }
        )

    return result


def load_urls(path: Path) -> List[str]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [str(item.get("url", item)) if isinstance(item, dict) else str(item) for item in payload]
        raise ValueError("JSON input must be a list of URLs or objects with url")
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and "url" in reader.fieldnames:
            return [row["url"] for row in reader if row.get("url")]
    with path.open(encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def write_report(report: List[Dict[str, Any]], out: Optional[Path]) -> None:
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify internet source URLs for admission strategy use.")
    parser.add_argument("--url", action="append", help="URL to classify. Can be repeated.")
    parser.add_argument("--input", type=Path, help="CSV/JSON/TXT file containing URLs.")
    parser.add_argument("--out", type=Path, help="Optional JSON report path.")
    args = parser.parse_args()

    urls: List[str] = []
    if args.url:
        urls.extend(args.url)
    if args.input:
        urls.extend(load_urls(args.input))
    if not urls:
        parser.error("provide --url or --input")

    report = [classify_url(url) for url in urls]
    write_report(report, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

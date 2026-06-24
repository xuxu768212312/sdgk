from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sdgk.indexes.builders import build_master_index, build_region_index, build_subject_index
from sdgk.indexes.master import search_majors, search_schools, summary as master_summary
from sdgk.indexes.region import check_school_regions, split_regions
from sdgk.indexes.subject import check_eligibility
from sdgk.plans.candidate_pool import main_generate as generate_candidate_pool
from sdgk.plans.generate_plan import generate_plan


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_build(args: argparse.Namespace) -> int:
    if args.target == "subject-index":
        print_json(build_subject_index(rebuild=args.rebuild))
    elif args.target == "region-index":
        print_json(build_region_index(rebuild=args.rebuild))
    elif args.target == "master-index":
        print_json(build_master_index(rebuild=args.rebuild))
    else:
        raise ValueError(args.target)
    return 0


def cmd_check_subject(args: argparse.Namespace) -> int:
    result = check_eligibility(
        year=args.year,
        edition=args.edition,
        level=args.level,
        subjects=args.subjects,
        school_code=args.school_code,
        major_code=args.major_code,
        school_name=args.school_name,
        major_name=args.major_name,
    )
    if args.json:
        print_json(result)
    else:
        print(f"{result['status']} {result['reason_code']} {result.get('message', '')}")
    return 0 if result["status"] == "PASS" else 1


def cmd_check_region(args: argparse.Namespace) -> int:
    regions = split_regions(args.regions)
    result = check_school_regions(regions, school_name=args.school_name or "", subject_school_code=args.school_code or "")
    if args.json:
        print_json(result)
    else:
        print(f"{result['status']} {result['reason_code']}")
    return 0 if result["status"] == "MATCH" else 1


def cmd_audit_data(args: argparse.Namespace) -> int:
    from sdgk.audits import data_accuracy

    old_argv = sys.argv[:]
    forwarded = ["sdgk-audit-data"]
    if args.full_subject_reextract:
        forwarded.append("--full-subject-reextract")
    if args.report:
        forwarded += ["--report", str(args.report)]
    sys.argv = forwarded
    try:
        return int(data_accuracy.main())
    finally:
        sys.argv = old_argv


def cmd_plan_generate(args: argparse.Namespace) -> int:
    result = generate_plan(
        student_path=args.student,
        out_dir=args.out_dir,
        risk_profile=args.risk_profile,
        hard_region=args.hard_region,
        slots=args.slots,
    )
    strategy = result.get("strategy_result", {})
    summary = {
        key: result.get(key)
        for key in ("student_file", "out_dir", "risk_profile", "slots", "hard_region", "hard_gate_passed", "simulation", "outputs", "candidate_counts", "violations")
    }
    summary["strategy_summary"] = {
        key: strategy.get(key)
        for key in (
            "algorithm_version",
            "hard_gate_passed",
            "selected_count",
            "blocked_count",
            "gradient_counts",
            "rush_counts",
            "conservative_slip_probability",
            "violations",
        )
    }
    print_json(summary)
    return 0 if result.get("hard_gate_passed") else 1


def cmd_candidates_generate(args: argparse.Namespace) -> int:
    result = generate_candidate_pool(args.student, args.out, hard_region=args.hard_region)
    print_json({"output_file": result.get("output_file"), "counts": result.get("counts"), "simulation": result.get("simulation")})
    return 0


def cmd_api_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("sdgk.api.app:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def cmd_master_summary(args: argparse.Namespace) -> int:
    print_json(master_summary())
    return 0


def cmd_master_search_schools(args: argparse.Namespace) -> int:
    print_json(search_schools(args.query, limit=args.limit))
    return 0


def cmd_master_search_majors(args: argparse.Namespace) -> int:
    print_json(search_majors(args.query, family=args.family, limit=args.limit))
    return 0


def cmd_source_check(args: argparse.Namespace) -> int:
    from sdgk.data.source_policy import classify_url, load_urls

    urls: list[str] = []
    if args.url:
        urls.extend(args.url)
    if args.input:
        urls.extend(load_urls(args.input))
    if not urls:
        raise ValueError("provide --url or --input")
    report = [classify_url(url) for url in urls]
    if args.out:
        from sdgk.core.io import write_json

        write_json(args.out, report)
    print_json(report)
    return 0 if all(item.get("formal_decision_allowed") for item in report) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m sdgk", description="山东高考知识库本地应用 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="构建 SQLite 索引")
    build_sub = build.add_subparsers(dest="target", required=True)
    for target in ("subject-index", "region-index", "master-index"):
        item = build_sub.add_parser(target)
        item.add_argument("--rebuild", action="store_true")
        item.set_defaults(func=cmd_build)

    check = sub.add_parser("check", help="确定性查询")
    check_sub = check.add_subparsers(dest="target", required=True)
    subject = check_sub.add_parser("subject")
    subject.add_argument("--year", type=int)
    subject.add_argument("--edition")
    subject.add_argument("--level", required=True)
    subject.add_argument("--subjects", required=True)
    subject.add_argument("--school-code")
    subject.add_argument("--major-code")
    subject.add_argument("--school-name")
    subject.add_argument("--major-name")
    subject.add_argument("--json", action="store_true")
    subject.set_defaults(func=cmd_check_subject)
    region = check_sub.add_parser("region")
    region.add_argument("--regions", required=True)
    region.add_argument("--school-name")
    region.add_argument("--school-code")
    region.add_argument("--json", action="store_true")
    region.set_defaults(func=cmd_check_region)

    audit = sub.add_parser("audit")
    audit_sub = audit.add_subparsers(dest="target", required=True)
    data = audit_sub.add_parser("data")
    data.add_argument("--full-subject-reextract", action="store_true")
    data.add_argument("--report", type=Path)
    data.set_defaults(func=cmd_audit_data)

    candidates = sub.add_parser("candidates")
    candidates_sub = candidates.add_subparsers(dest="target", required=True)
    cand_generate = candidates_sub.add_parser("generate")
    cand_generate.add_argument("--student", required=True, type=Path)
    cand_generate.add_argument("--out", required=True, type=Path)
    cand_generate.add_argument("--hard-region", action="store_true")
    cand_generate.set_defaults(func=cmd_candidates_generate)

    plan = sub.add_parser("plan")
    plan_sub = plan.add_subparsers(dest="target", required=True)
    plan_generate = plan_sub.add_parser("generate")
    plan_generate.add_argument("--student", required=True, type=Path)
    plan_generate.add_argument("--out-dir", required=True, type=Path)
    plan_generate.add_argument("--risk-profile", default="standard", choices=["conservative", "standard", "aggressive", "opportunistic"])
    plan_generate.add_argument("--hard-region", action="store_true")
    plan_generate.add_argument("--slots", type=int, default=96)
    plan_generate.set_defaults(func=cmd_plan_generate)

    master = sub.add_parser("master")
    master_sub = master.add_subparsers(dest="target", required=True)
    master_summary_parser = master_sub.add_parser("summary")
    master_summary_parser.set_defaults(func=cmd_master_summary)
    schools = master_sub.add_parser("search-schools")
    schools.add_argument("query", nargs="?", default="")
    schools.add_argument("--limit", type=int, default=20)
    schools.set_defaults(func=cmd_master_search_schools)
    majors = master_sub.add_parser("search-majors")
    majors.add_argument("query", nargs="?", default="")
    majors.add_argument("--family", default="")
    majors.add_argument("--limit", type=int, default=20)
    majors.set_defaults(func=cmd_master_search_majors)

    source = sub.add_parser("source")
    source_sub = source.add_subparsers(dest="target", required=True)
    source_check = source_sub.add_parser("check")
    source_check.add_argument("--url", action="append")
    source_check.add_argument("--input", type=Path)
    source_check.add_argument("--out", type=Path)
    source_check.set_defaults(func=cmd_source_check)

    api = sub.add_parser("api")
    api_sub = api.add_subparsers(dest="target", required=True)
    serve = api_sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8716)
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(func=cmd_api_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print_json({"status": "ERROR", "reason_code": exc.__class__.__name__, "message": str(exc)})
        return 2

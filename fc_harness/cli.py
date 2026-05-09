from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .baseline import fetch_baseline
from .dryrun import make_dry_attempt
from .env import load_dotenv
from .firecrawl import FirecrawlClient
from .models import ResultRecord
from .recommend import recommend_retries
from .report import (
    read_jsonl,
    write_findings_report,
    write_jsonl,
    write_markdown_report,
    write_summary_json,
)
from .retry import choose_retry_recommendation, merge_retry_options
from .scoring import score_attempt


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        run_command(args)
    elif args.command == "report":
        report_command(args)
    else:
        parser.print_help()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fc-eval",
        description="Evaluate Firecrawl output and recommend retry configs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run a URL corpus.")
    run.add_argument("--urls", required=True, type=Path, help="URL file, one URL per line.")
    run.add_argument("--out", required=True, type=Path, help="Output directory.")
    run.add_argument("--api-key-env", default="FIRECRAWL_API_KEY")
    run.add_argument("--api-url", default="https://api.firecrawl.dev")
    run.add_argument("--dry-run", action="store_true", help="Use offline synthetic data.")
    run.add_argument(
        "--baseline-only",
        action="store_true",
        help="Fetch real URLs with the local urllib baseline instead of Firecrawl.",
    )
    run.add_argument("--compare-baseline", action="store_true")
    run.add_argument("--formats", default="markdown")
    run.add_argument("--timeout-ms", type=int, default=60000)
    run.add_argument("--wait-for-ms", type=int, default=None)
    run.add_argument("--max-age-ms", type=int, default=None)
    run.add_argument("--proxy", choices=["basic", "enhanced", "auto"], default=None)
    run.add_argument("--only-main-content", action=argparse.BooleanOptionalAction, default=None)
    run.add_argument("--max-urls", type=int, default=None)
    run.add_argument("--options-json", type=Path, default=None)
    run.add_argument(
        "--retry-recommendations",
        action="store_true",
        help="Run a second Firecrawl scrape with the top eligible recommendation.",
    )
    run.add_argument(
        "--retry-threshold",
        type=int,
        default=85,
        help="Only retry Firecrawl attempts below this score.",
    )
    run.add_argument(
        "--allow-costly-retries",
        action="store_true",
        help="Allow recommendations with cost notes, such as enhanced proxy or OCR.",
    )

    report = subparsers.add_parser("report", help="Regenerate a report from JSONL.")
    report.add_argument("--input", required=True, type=Path)
    report.add_argument("--out", required=True, type=Path)

    return parser


def run_command(args: argparse.Namespace) -> None:
    load_dotenv()
    urls = read_urls(args.urls)
    if args.max_urls is not None:
        urls = urls[: args.max_urls]

    args.out.mkdir(parents=True, exist_ok=True)
    options = build_options(args)
    records: list[ResultRecord] = []

    client: FirecrawlClient | None = None
    if not args.dry_run and not args.baseline_only:
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            raise SystemExit(
                f"Missing API key. Set ${args.api_key_env} or use --dry-run/--baseline-only."
            )
        client = FirecrawlClient(api_key=api_key, api_url=args.api_url)

    for index, url in enumerate(urls):
        if args.dry_run:
            attempt = make_dry_attempt(url, index)
        elif args.baseline_only:
            attempt = fetch_baseline(url)
        else:
            assert client is not None
            attempt = client.scrape(url, options)
        record = record_from_attempt(attempt)
        records.append(record)

        if should_retry(args, record):
            assert client is not None
            recommendation = choose_retry_recommendation(
                record, allow_costly=args.allow_costly_retries
            )
            if recommendation is not None:
                retry_options = merge_retry_options(options, recommendation.options)
                retry_attempt = client.scrape(url, retry_options)
                retry_attempt.engine = "firecrawl_retry"
                retry_attempt.config = retry_options
                retry_attempt.metadata = dict(retry_attempt.metadata)
                retry_attempt.metadata.update(
                    {
                        "retry_for_url": url,
                        "retry_name": recommendation.name,
                        "retry_reason": recommendation.why,
                        "initial_score": record.score.score,
                        "initial_flags": record.score.flags,
                    }
                )
                retry_record = record_from_attempt(retry_attempt)
                retry_record.attempt.metadata["retry_score_delta"] = (
                    retry_record.score.score - record.score.score
                )
                records.append(retry_record)

        if args.compare_baseline and not args.dry_run:
            baseline_attempt = fetch_baseline(url)
            records.append(record_from_attempt(baseline_attempt))

    write_jsonl(records, args.out / "results.jsonl")
    write_markdown_report(records, args.out / "report.md")
    write_findings_report(records, args.out / "findings.md")
    write_summary_json(records, args.out / "summary.json")

    print(f"Wrote {args.out / 'results.jsonl'}")
    print(f"Wrote {args.out / 'report.md'}")
    print(f"Wrote {args.out / 'findings.md'}")
    print(f"Wrote {args.out / 'summary.json'}")


def report_command(args: argparse.Namespace) -> None:
    args.out.mkdir(parents=True, exist_ok=True)
    records = [record_from_attempt(record.attempt) for record in read_jsonl(args.input)]
    write_jsonl(records, args.out / "results.jsonl")
    write_markdown_report(records, args.out / "report.md")
    write_findings_report(records, args.out / "findings.md")
    write_summary_json(records, args.out / "summary.json")
    print(f"Wrote {args.out / 'results.jsonl'}")
    print(f"Wrote {args.out / 'report.md'}")
    print(f"Wrote {args.out / 'findings.md'}")
    print(f"Wrote {args.out / 'summary.json'}")


def record_from_attempt(attempt: Any) -> ResultRecord:
    score = score_attempt(attempt)
    recs = recommend_retries(attempt, score)
    return ResultRecord(attempt=attempt, score=score, recommendations=recs)


def read_urls(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#"):
            continue
        urls.append(clean)
    return urls


def build_options(args: argparse.Namespace) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if args.options_json:
        options.update(json.loads(args.options_json.read_text(encoding="utf-8")))

    options.setdefault("formats", parse_formats(args.formats))
    options.setdefault("timeout", args.timeout_ms)

    if args.wait_for_ms is not None:
        options["waitFor"] = args.wait_for_ms
    if args.max_age_ms is not None:
        options["maxAge"] = args.max_age_ms
    if args.proxy is not None:
        options["proxy"] = args.proxy
    if args.only_main_content is not None:
        options["onlyMainContent"] = args.only_main_content

    return options


def parse_formats(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def should_retry(args: argparse.Namespace, record: ResultRecord) -> bool:
    if not args.retry_recommendations:
        return False
    if args.dry_run or args.baseline_only:
        return False
    if record.attempt.engine != "firecrawl":
        return False
    return record.score.score < args.retry_threshold


if __name__ == "__main__":
    main()

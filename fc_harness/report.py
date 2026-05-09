from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from .models import ResultRecord


def write_jsonl(records: list[ResultRecord], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=True) + "\n")


def read_jsonl(path: Path) -> list[ResultRecord]:
    records: list[ResultRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(ResultRecord.from_dict(json.loads(line)))
    return records


def build_summary(records: list[ResultRecord]) -> dict[str, object]:
    by_engine: dict[str, list[ResultRecord]] = {}
    for record in records:
        by_engine.setdefault(record.attempt.engine, []).append(record)

    engine_summary = {}
    for engine, engine_records in sorted(by_engine.items()):
        scores = [item.score.score for item in engine_records]
        latencies = [item.attempt.latency_ms for item in engine_records]
        engine_summary[engine] = {
            "count": len(engine_records),
            "success_rate": round(
                sum(1 for item in engine_records if item.attempt.ok)
                / max(1, len(engine_records)),
                3,
            ),
            "avg_score": round(mean(scores), 1) if scores else 0,
            "avg_latency_ms": round(mean(latencies), 1) if latencies else 0,
        }

    flag_counts: dict[str, int] = {}
    for record in records:
        for flag in record.score.flags:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

    return {
        "total_records": len(records),
        "engines": engine_summary,
        "flag_counts": dict(sorted(flag_counts.items())),
        "retry_summary": build_retry_summary(records),
        "baseline_comparison": build_baseline_comparison(records),
    }


def write_summary_json(records: list[ResultRecord], path: Path) -> None:
    path.write_text(
        json.dumps(build_summary(records), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def write_markdown_report(records: list[ResultRecord], path: Path) -> None:
    summary = build_summary(records)
    lines: list[str] = []
    lines.append("# Firecrawl Eval Repair Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Engine | Count | Success | Avg Score | Avg Latency |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    engines = summary["engines"]
    assert isinstance(engines, dict)
    for engine, stats in engines.items():
        assert isinstance(stats, dict)
        lines.append(
            "| {engine} | {count} | {success:.1%} | {score} | {latency} ms |".format(
                engine=engine,
                count=stats["count"],
                success=float(stats["success_rate"]),
                score=stats["avg_score"],
                latency=stats["avg_latency_ms"],
            )
        )

    lines.append("")
    lines.append("## Failure Flags")
    lines.append("")
    flag_counts = summary["flag_counts"]
    assert isinstance(flag_counts, dict)
    if flag_counts:
        for flag, count in flag_counts.items():
            lines.append(f"- `{flag}`: {count}")
    else:
        lines.append("- No flags detected.")

    lines.append("")
    lines.append("## Retry Summary")
    lines.append("")
    lines.extend(_retry_summary_lines(records))

    lines.append("")
    lines.append("## Lowest Scoring Attempts")
    lines.append("")
    for record in sorted(records, key=lambda item: item.score.score)[:10]:
        lines.extend(_record_section(record))

    lines.append("")
    lines.append("## Re-run Example")
    lines.append("")
    lines.append("Use a recommendation's `options` object as the scrape body plus `url`:")
    lines.append("")
    lines.append("```bash")
    lines.append("curl -X POST https://api.firecrawl.dev/v2/scrape \\")
    lines.append("  -H \"Authorization: Bearer $FIRECRAWL_API_KEY\" \\")
    lines.append("  -H \"Content-Type: application/json\" \\")
    lines.append("  -d @retry-body.json")
    lines.append("```")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_findings_report(records: list[ResultRecord], path: Path) -> None:
    pairs = retry_pairs(records)
    lines: list[str] = []
    lines.append("# Firecrawl Findings")
    lines.append("")

    comparison = build_baseline_comparison(records)
    lines.append("## Firecrawl vs Baseline")
    lines.append("")
    if comparison["count"] == 0:
        lines.append("No Firecrawl/baseline pairs were recorded.")
    else:
        lines.append(
            "Compared {count} URLs. Firecrawl beat the baseline on {firecrawl_wins}, "
            "matched it on {ties}, and trailed it on {baseline_wins}. Average delta: "
            "{avg_delta} points.".format(**comparison)
        )
        lines.append("")
        lines.append("| URL | Firecrawl | Baseline | Delta |")
        lines.append("| --- | ---: | ---: | ---: |")
        for firecrawl, baseline in sorted(
            baseline_pairs(records),
            key=lambda pair: pair[0].score.score - pair[1].score.score,
            reverse=True,
        ):
            delta = firecrawl.score.score - baseline.score.score
            lines.append(
                f"| {firecrawl.attempt.url} | {firecrawl.score.score} | "
                f"{baseline.score.score} | {delta:+d} |"
            )
    lines.append("")
    lines.append("## Retry Deltas")
    lines.append("")
    if not pairs:
        lines.append("No retry attempts were recorded.")
        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return

    summary = build_retry_summary(records)
    lines.append(
        "Recorded {count} retry attempts. {improved} improved, {unchanged} were "
        "unchanged, and {regressed} regressed. Average delta: {avg_delta} points.".format(
            count=summary["count"],
            improved=summary["improved"],
            unchanged=summary["unchanged"],
            regressed=summary["regressed"],
            avg_delta=summary["avg_delta"],
        )
    )
    lines.append("")
    lines.append("| URL | Recommendation | Initial | Retry | Delta |")
    lines.append("| --- | --- | ---: | ---: | ---: |")
    for initial, retry in sorted(
        pairs, key=lambda pair: pair[1].score.score - pair[0].score.score, reverse=True
    ):
        delta = retry.score.score - initial.score.score
        retry_name = retry.attempt.metadata.get("retry_name", "unknown")
        lines.append(
            f"| {initial.attempt.url} | `{retry_name}` | "
            f"{initial.score.score} | {retry.score.score} | {delta:+d} |"
        )

    lines.append("")
    lines.append("## Retry Details")
    lines.append("")
    for initial, retry in sorted(
        pairs, key=lambda pair: pair[1].score.score - pair[0].score.score, reverse=True
    ):
        delta = retry.score.score - initial.score.score
        retry_name = retry.attempt.metadata.get("retry_name", "unknown")
        retry_reason = retry.attempt.metadata.get("retry_reason", "")
        lines.append(f"### {initial.attempt.url}")
        lines.append("")
        lines.append(f"- Recommendation: `{retry_name}`")
        lines.append(f"- Initial score: `{initial.score.score}`")
        lines.append(f"- Retry score: `{retry.score.score}`")
        lines.append(f"- Delta: `{delta:+d}`")
        lines.append(
            f"- Initial flags: `{', '.join(initial.score.flags) if initial.score.flags else 'none'}`"
        )
        lines.append(
            f"- Retry flags: `{', '.join(retry.score.flags) if retry.score.flags else 'none'}`"
        )
        if retry_reason:
            lines.append(f"- Why: {retry_reason}")
        lines.append(f"- Retry options: `{json.dumps(retry.attempt.config, ensure_ascii=True)}`")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def build_retry_summary(records: list[ResultRecord]) -> dict[str, object]:
    pairs = retry_pairs(records)
    deltas = [retry.score.score - initial.score.score for initial, retry in pairs]
    return {
        "count": len(pairs),
        "improved": sum(1 for delta in deltas if delta > 0),
        "unchanged": sum(1 for delta in deltas if delta == 0),
        "regressed": sum(1 for delta in deltas if delta < 0),
        "avg_delta": round(mean(deltas), 1) if deltas else 0,
        "best_delta": max(deltas) if deltas else 0,
        "worst_delta": min(deltas) if deltas else 0,
    }


def build_baseline_comparison(records: list[ResultRecord]) -> dict[str, object]:
    pairs = baseline_pairs(records)
    deltas = [firecrawl.score.score - baseline.score.score for firecrawl, baseline in pairs]
    return {
        "count": len(pairs),
        "firecrawl_wins": sum(1 for delta in deltas if delta > 0),
        "ties": sum(1 for delta in deltas if delta == 0),
        "baseline_wins": sum(1 for delta in deltas if delta < 0),
        "avg_delta": round(mean(deltas), 1) if deltas else 0,
        "best_delta": max(deltas) if deltas else 0,
        "worst_delta": min(deltas) if deltas else 0,
    }


def baseline_pairs(records: list[ResultRecord]) -> list[tuple[ResultRecord, ResultRecord]]:
    firecrawl_by_url: dict[str, ResultRecord] = {}
    baseline_by_url: dict[str, ResultRecord] = {}
    for record in records:
        if record.attempt.engine == "firecrawl":
            firecrawl_by_url.setdefault(record.attempt.url, record)
        elif record.attempt.engine == "baseline":
            baseline_by_url.setdefault(record.attempt.url, record)

    pairs: list[tuple[ResultRecord, ResultRecord]] = []
    for url, firecrawl in firecrawl_by_url.items():
        baseline = baseline_by_url.get(url)
        if baseline is not None:
            pairs.append((firecrawl, baseline))
    return pairs


def retry_pairs(records: list[ResultRecord]) -> list[tuple[ResultRecord, ResultRecord]]:
    initial_by_url: dict[str, ResultRecord] = {}
    for record in records:
        if record.attempt.engine == "firecrawl":
            initial_by_url.setdefault(record.attempt.url, record)

    pairs: list[tuple[ResultRecord, ResultRecord]] = []
    for retry in records:
        if retry.attempt.engine != "firecrawl_retry":
            continue
        retry_for_url = str(retry.attempt.metadata.get("retry_for_url") or retry.attempt.url)
        initial = initial_by_url.get(retry_for_url)
        if initial is not None:
            pairs.append((initial, retry))
    return pairs


def _retry_summary_lines(records: list[ResultRecord]) -> list[str]:
    summary = build_retry_summary(records)
    if summary["count"] == 0:
        return ["No retry attempts were recorded."]
    return [
        f"- Retry attempts: `{summary['count']}`",
        f"- Improved: `{summary['improved']}`",
        f"- Unchanged: `{summary['unchanged']}`",
        f"- Regressed: `{summary['regressed']}`",
        f"- Average delta: `{summary['avg_delta']}`",
        f"- Best delta: `{summary['best_delta']}`",
        f"- Worst delta: `{summary['worst_delta']}`",
    ]


def _record_section(record: ResultRecord) -> list[str]:
    attempt = record.attempt
    score = record.score
    lines = [
        f"### {attempt.engine}: {attempt.url}",
        "",
        f"- Score: `{score.score}`",
        f"- OK: `{attempt.ok}`",
        f"- Status: `{attempt.status_code}`",
        f"- Latency: `{attempt.latency_ms} ms`",
        f"- Words: `{score.word_count}`",
        f"- Flags: `{', '.join(score.flags) if score.flags else 'none'}`",
    ]
    if attempt.error:
        lines.append(f"- Error: `{attempt.error[:240]}`")
    if record.recommendations:
        lines.append("")
        lines.append("Recommendations:")
        for rec in record.recommendations:
            compact_options = json.dumps(rec.options, ensure_ascii=True)
            lines.append(f"- `{rec.name}`: {rec.why}")
            lines.append(f"  Options: `{compact_options}`")
            if rec.cost_note:
                lines.append(f"  Cost note: {rec.cost_note}")
    lines.append("")
    return lines

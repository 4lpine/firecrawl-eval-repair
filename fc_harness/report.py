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


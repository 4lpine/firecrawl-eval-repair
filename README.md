# Firecrawl Eval Repair Harness

This is a small evaluation harness for Firecrawl. It runs a URL corpus through
Firecrawl, scores the output, classifies common failure modes, and suggests
next-attempt Firecrawl options such as `waitFor`, `actions`, `proxy`,
`onlyMainContent`, `includeTags`, `excludeTags`, and parser modes.

The goal is not to clone Firecrawl. The goal is to produce useful evidence:
reproducible failures, quality scores, and concrete retry configs that a
Firecrawl engineer or customer could use.

## Quick Start

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
# then edit .env and set FIRECRAWL_API_KEY
```

Run an offline demo that does not use network or an API key:

```powershell
python -m fc_harness run --urls examples/urls.txt --out runs/demo --dry-run
```

Open the generated report:

```powershell
Get-Content runs/demo/report.md
```

Run against the real Firecrawl API:

```powershell
$env:FIRECRAWL_API_KEY="fc-your-key"
python -m fc_harness run --urls examples/urls.txt --out runs/live --compare-baseline
```

Run only the local baseline fetcher against real URLs:

```powershell
python -m fc_harness run --urls examples/real_urls.txt --out runs/real-baseline --baseline-only
```

Do not commit API keys. The runner only reads `FIRECRAWL_API_KEY` from the
environment, `.env`, or an explicit `--api-key-env` variable name.

## Live Test Status

See [docs/live_eval_summary.md](docs/live_eval_summary.md) for the latest
small-corpus Firecrawl run. The current implementation evaluates `/v2/scrape`;
it does not yet benchmark `/crawl`, `/map`, `/search`, `/parse`, `/interact`,
or `/agent`.

See [docs/sample_findings.md](docs/sample_findings.md) for a concrete live
`findings.md` example.

## What It Measures

For each scrape attempt, the harness records:

- request success and HTTP status
- latency
- markdown length and word count
- headings, tables, links, and structure
- blocked/CAPTCHA/Cloudflare signals
- JavaScript loading states
- boilerplate and navigation-heavy output
- link farm risk
- recommended Firecrawl retry options

Scores are heuristic. They are meant to rank failures and guide debugging, not
replace human review.

## Useful Commands

Run with stricter freshness:

```powershell
python -m fc_harness run --urls examples/urls.txt --out runs/fresh --max-age-ms 0
```

Run Firecrawl with automatic second-pass retries:

```powershell
python -m fc_harness run `
  --urls examples/hard_urls.txt `
  --out runs/live-retry `
  --compare-baseline `
  --retry-recommendations `
  --retry-threshold 90
```

This writes `findings.md`, which summarizes before/after score deltas for retry
attempts.

Run a smaller edge-case corpus intended to find retry opportunities:

```powershell
python -m fc_harness run `
  --urls examples/edge_urls.txt `
  --out runs/edge-retry `
  --retry-recommendations `
  --retry-threshold 95 `
  --allow-costly-retries
```

Run the broader 200 URL corpus in batches:

```powershell
python -m fc_harness run `
  --urls examples/benchmark_200_urls.txt `
  --out runs/benchmark-200-000 `
  --start-at 0 `
  --max-urls 50 `
  --compare-baseline
```

See [docs/benchmark_200_plan.md](docs/benchmark_200_plan.md) for the full
batch plan and retry guidance.

Ask Firecrawl for extra formats:

```powershell
python -m fc_harness run --urls examples/urls.txt --out runs/html --formats markdown,html,links
```

Pass custom Firecrawl options:

```powershell
python -m fc_harness run --urls examples/urls.txt --out runs/custom --options-json examples/firecrawl_options.json
```

Regenerate a report from an existing result file:

```powershell
python -m fc_harness report --input runs/live/results.jsonl --out runs/live-report
```

## Output

Each run writes:

- `results.jsonl`: machine-readable attempts, scores, and recommendations
- `report.md`: human-readable benchmark summary
- `findings.md`: before/after retry findings, when retry attempts exist
- `summary.json`: aggregate metrics

## Ethical Use

Use this only for pages you are allowed to access and test. Respect robots.txt,
site terms, rate limits, and privacy obligations.

## Hiring Angle

This repo is designed to support a cold email like:

> I built a small Firecrawl eval and repair harness. It runs real URL corpora,
> scores output quality, classifies failures, and suggests concrete retry
> configs. I used it to produce reproducible cases that could improve scrape
> quality and developer debugging.

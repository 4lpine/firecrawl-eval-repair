# Live Evaluation Summary

This repository has been tested against the real Firecrawl `/v2/scrape` API on
a small hard corpus:

- `https://firecrawl.dev`
- `https://docs.firecrawl.dev/features/scrape`
- `https://docs.firecrawl.dev/features/interact`
- `https://github.com/firecrawl/firecrawl`
- `https://www.npmjs.com/package/firecrawl`
- `https://pypi.org/project/firecrawl-py/`
- `https://www.ycombinator.com/companies/firecrawl`
- `https://docs.stripe.com/payments/quickstart`
- `https://example.com`
- `https://en.wikipedia.org/wiki/Web_scraping`

## Result

| Engine | Count | Success | Avg Score | Avg Latency |
| --- | ---: | ---: | ---: | ---: |
| Firecrawl | 10 | 100% | 92.2 | 1665 ms |
| Baseline | 10 | 90% | 71.1 | 1765.3 ms |
| Firecrawl retry | 3 | 100% | 74.0 | 1532 ms |

## Findings

- Firecrawl beat the baseline on 7 of 10 paired URLs, tied on 2, and trailed on
  1 naturally short page.
- Average Firecrawl-vs-baseline score delta was +21.1 points.
- The strongest win was npm: the local baseline received HTTP 403, while
  Firecrawl returned a successful result with score 100.
- PyPI and Stripe docs also showed large Firecrawl wins over the naive baseline.
- The automatic retry loop ran on 3 lower-scoring Firecrawl attempts. Those
  retries were unchanged, which is a useful product signal: the repair layer
  needs smarter domain-aware retry configs, not just generic tag filters.

## Current Scope

This is a working scrape-eval harness, not a full Firecrawl product benchmark
yet. It currently evaluates `/v2/scrape`. The harness now supports an automatic
second-pass retry loop via `--retry-recommendations`, which measures before/after
score deltas for recommended configs and writes a `findings.md` report.

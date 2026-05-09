# Live Evaluation Summary

This repository has been tested against the real Firecrawl `/v2/scrape` API on
a small starter corpus:

- `https://firecrawl.dev`
- `https://docs.firecrawl.dev/features/scrape`
- `https://docs.firecrawl.dev/features/interact`
- `https://example.com`
- `https://en.wikipedia.org/wiki/Web_scraping`

## Result

| Engine | Count | Success | Avg Score | Avg Latency |
| --- | ---: | ---: | ---: | ---: |
| Firecrawl | 5 | 100% | 86.0 | 628.6 ms |
| Baseline | 5 | 100% | 85.4 | 361.6 ms |

## Findings

- Firecrawl produced strong results for its own marketing site and docs.
- Wikipedia was useful but boilerplate-heavy, which the harness correctly
  flagged and routed to `onlyMainContent` plus layout filters.
- `example.com` scored low because the page is naturally short; this is an
  expected limitation of length-based quality heuristics.
- Initial scoring generated false positives for pages that mentioned anti-bot
  or loading terms in normal content. Those heuristics were tightened and
  covered with regression tests.

## Current Scope

This is a working scrape-eval harness, not a full Firecrawl product benchmark
yet. It currently evaluates `/v2/scrape`. The next high-value feature is an
automatic second-pass retry loop that measures before/after score deltas for
recommended configs.


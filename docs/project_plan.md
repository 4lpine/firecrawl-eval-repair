# Product Direction

## Thesis

Firecrawl already wins by combining web access, clean formats, browser
infrastructure, document parsing, and agent workflows. A credible improvement is
not another scraper. A credible improvement is a feedback loop that makes
Firecrawl quality easier to measure, debug, and improve.

## MVP

The current MVP:

- accepts a URL corpus
- calls Firecrawl `/v2/scrape`
- optionally fetches a simple local baseline
- scores markdown quality with transparent heuristics
- flags common failure modes
- recommends next-attempt Firecrawl configs
- writes JSONL, summary JSON, and a markdown report

## Next Features

1. Add second-pass retries and score deltas.
2. Add schema extraction validation for JSON mode.
3. Add corpus tags, such as `docs`, `pdf`, `spa`, `ecommerce`, and `blocked`.
4. Add screenshot-aware checks for visual blank pages.
5. Add a small static HTML dashboard for comparing attempts.
6. Add GitHub Actions support for regression testing against a fixed corpus.
7. Add export that opens a high-quality Firecrawl GitHub issue template.

## What To Show Firecrawl

Run this on 50 to 100 URLs across docs, PDFs, modern JS apps, e-commerce pages,
and known difficult sites. Send only the strongest findings:

- URL
- initial Firecrawl score
- failure flag
- suggested retry config
- improved score after retry
- whether the issue is docs, product, parser, browser, or infra related


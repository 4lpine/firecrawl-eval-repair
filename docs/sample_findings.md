# Sample Findings

This sample comes from a live 10-URL run against Firecrawl `/v2/scrape` using:

```powershell
python -m fc_harness run `
  --urls examples/hard_urls.txt `
  --out runs/live-retry `
  --compare-baseline `
  --retry-recommendations `
  --retry-threshold 90
```

## Firecrawl vs Baseline

Firecrawl beat the local baseline on 7 of 10 paired URLs, tied on 2, and
trailed on 1 naturally short page. Average score delta: +21.1 points.

| URL | Firecrawl | Baseline | Delta |
| --- | ---: | ---: | ---: |
| `https://www.npmjs.com/package/firecrawl` | 100 | 0 | +100 |
| `https://pypi.org/project/firecrawl-py/` | 100 | 53 | +47 |
| `https://docs.stripe.com/payments/quickstart` | 84 | 51 | +33 |
| `https://www.ycombinator.com/companies/firecrawl` | 100 | 88 | +12 |
| `https://firecrawl.dev` | 100 | 92 | +8 |
| `https://github.com/firecrawl/firecrawl` | 100 | 92 | +8 |
| `https://en.wikipedia.org/wiki/Web_scraping` | 84 | 80 | +4 |
| `https://docs.firecrawl.dev/features/scrape` | 100 | 100 | +0 |
| `https://docs.firecrawl.dev/features/interact` | 100 | 100 | +0 |
| `https://example.com` | 54 | 55 | -1 |

## Retry Deltas

The automatic retry loop ran three second-pass Firecrawl scrapes. All three
completed successfully, but none improved score. That is useful signal for the
next iteration: generic tag-filter retries are not enough for already-good
scrapes, and the repair layer needs domain-aware strategies.

| URL | Recommendation | Initial | Retry | Delta |
| --- | --- | ---: | ---: | ---: |
| `https://en.wikipedia.org/wiki/Web_scraping` | `retry_with_boilerplate_filters` | 84 | 84 | +0 |
| `https://docs.stripe.com/payments/quickstart` | `retry_with_boilerplate_filters` | 84 | 84 | +0 |
| `https://example.com` | `retry_full_page_with_debug_formats` | 54 | 54 | +0 |


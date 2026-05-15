# 200 URL Benchmark Results

Run output:

- First pass: `runs/benchmark-200-live`
- Targeted retry pass: `runs/benchmark-200-low-retry`

## First Pass

The benchmark ran 200 URLs through Firecrawl and the local baseline fetcher.

| Metric | Firecrawl | Baseline |
| --- | ---: | ---: |
| URLs | 200 | 200 |
| Success rate | 98.5% | 90.5% |
| Average score | 91.5 | 71.7 |
| Average latency | 1511.8 ms | 699.5 ms |

Firecrawl beat the baseline on 151 URLs, tied on 32, and trailed on 17. Average score delta was +19.8 points.

The first pass produced 3 Firecrawl request failures:

| URL | Result |
| --- | --- |
| `https://github.blog/` | Timed out on the first pass |
| `https://www.reddit.com/r/webscraping/` | Firecrawl returned an explicit unsupported-site response |
| `https://www.nytimes.com/section/technology` | Firecrawl returned an explicit unsupported-site response |

40 Firecrawl results scored below 85 and were selected for targeted retry testing.

## Targeted Retry Pass

The retry pass reran the 40 below-threshold URLs and allowed the harness to retry eligible cases below score 85.

| Metric | Value |
| --- | ---: |
| Initial low-score URLs rerun | 40 |
| Retry attempts | 28 |
| Improved retries | 4 |
| Unchanged retries | 22 |
| Regressed retries | 2 |
| Average retry delta | +1 |
| Best retry delta | +16 |
| Worst retry delta | -8 |

Best retry improvements:

| URL | Recommendation | Initial | Retry | Delta |
| --- | --- | ---: | ---: | ---: |
| `https://github.blog/` | `retry_with_boilerplate_filters` | 84 | 100 | +16 |
| `https://docs.stripe.com/billing/subscriptions/overview` | `retry_docs_main_region` | 80 | 92 | +12 |
| `https://docs.stripe.com/payments/quickstart` | `retry_docs_main_region` | 84 | 92 | +8 |
| `https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service` | `retry_with_boilerplate_filters` | 80 | 84 | +4 |

## Takeaway

The larger corpus did not show Firecrawl as weak overall. Firecrawl performed strongly against the baseline. The useful product signal is narrower: the harness can find first-pass failures, identify below-threshold scrapes, avoid retrying explicit unsupported-site responses, and measure which retry strategies actually improve output quality.

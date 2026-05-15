# 200 URL Benchmark Plan

Use `examples/benchmark_200_urls.txt` for a broader Firecrawl evaluation. It mixes docs, package pages, GitHub repos, Wikipedia/reference pages, government and standards pages, blogs, product pages, and difficult dynamic/listing pages.

Run a cheap smoke test first:

```powershell
python -m fc_harness run `
  --urls examples/benchmark_200_urls.txt `
  --out runs/benchmark-200-smoke `
  --max-urls 20 `
  --compare-baseline
```

Run the full corpus in four batches:

```powershell
python -m fc_harness run --urls examples/benchmark_200_urls.txt --out runs/benchmark-200-000 --start-at 0 --max-urls 50 --compare-baseline
python -m fc_harness run --urls examples/benchmark_200_urls.txt --out runs/benchmark-200-050 --start-at 50 --max-urls 50 --compare-baseline
python -m fc_harness run --urls examples/benchmark_200_urls.txt --out runs/benchmark-200-100 --start-at 100 --max-urls 50 --compare-baseline
python -m fc_harness run --urls examples/benchmark_200_urls.txt --out runs/benchmark-200-150 --start-at 150 --max-urls 50 --compare-baseline
```

Only run automatic retries after the first-pass report shows enough weak scrapes to justify the extra Firecrawl calls:

```powershell
python -m fc_harness run `
  --urls examples/benchmark_200_urls.txt `
  --out runs/benchmark-200-retry-000 `
  --start-at 0 `
  --max-urls 50 `
  --compare-baseline `
  --retry-recommendations `
  --retry-threshold 85
```

A full first-pass 200 URL run uses about 200 Firecrawl scrape calls. A full retry run can approach 400 scrape calls if many pages fall below the retry threshold. `--allow-costly-retries` can add more expensive enhanced proxy or parser paths, so keep it off until there is a specific reason to test those cases.

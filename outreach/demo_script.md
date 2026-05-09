# Demo Script

## 1. Show the offline demo

```powershell
python -m fc_harness run --urls examples/urls.txt --out runs/demo --dry-run
Get-Content runs/demo/report.md
```

Point out that the report identifies concrete failure modes and provides
copyable Firecrawl option objects.

## 2. Run a live corpus

```powershell
$env:FIRECRAWL_API_KEY="fc-your-key"
python -m fc_harness run --urls examples/urls.txt --out runs/live --compare-baseline
```

Use real customer-like URLs, then sort by lowest score in `runs/live/report.md`.

## 3. Turn recommendations into a second pass

Copy one recommendation's options into a JSON file:

```json
{
  "url": "https://example.com",
  "onlyMainContent": false,
  "formats": ["markdown", "html", "links"],
  "waitFor": 2000,
  "timeout": 60000
}
```

Run the retry with Firecrawl, compare score delta, and note whether the
recommendation improved content quality.

## 4. Pitch the value

This can become:

- a public debugging tool for Firecrawl users
- an internal eval suite for extraction regressions
- a benchmark corpus for docs, PDFs, JS apps, e-commerce, and anti-bot sites
- an automated "try this next" assistant in the dashboard or CLI


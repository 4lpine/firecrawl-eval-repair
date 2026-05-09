Subject: Built a Firecrawl eval harness and ran a live corpus

Hi [Name],

I have been studying Firecrawl and built a small eval/repair harness around the
`/v2/scrape` API:

https://github.com/4lpine/firecrawl-eval-repair

The project runs a URL corpus through Firecrawl, scores the output, compares it
against a simple baseline fetcher, classifies failure modes, and can run a
second-pass retry with recommended configs such as `onlyMainContent`,
`excludeTags`, `waitFor`, `actions`, proxy mode, and parser options. It writes a
machine-readable JSONL file plus human-readable `report.md` and `findings.md`.

I tested the current version on a 10-URL live corpus. Firecrawl went 10/10 with
an average score of 92.2, while the naive baseline averaged 71.1 and failed on
npm with a 403. Firecrawl beat the baseline on 7/10 URLs, with the biggest wins
on npm, PyPI, and Stripe docs.

The automatic retry loop also surfaced a useful next problem: three generic
retry configs ran successfully but did not improve score, which suggests the
repair layer needs more domain-aware retry strategies instead of only generic
tag filters.

I am interested in working with Firecrawl. I know this is not a full benchmark
yet, but I think the direction is useful: a repeatable loop for finding weak
scrapes, suggesting retry configs, and measuring before/after score deltas.

If this is interesting, I would love to do a small work trial or take one real
Firecrawl reliability/debugging problem and build against it. I am specifically
interested in evals, extraction quality, and developer tooling around failed or
borderline scrapes.

Best,
[Your Name]

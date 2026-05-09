Subject: Built a Firecrawl eval and repair harness

Hi [Name],

I have been studying Firecrawl and built a small eval/repair harness around the
`/v2/scrape` API:

https://github.com/4lpine/firecrawl-eval-repair

The project runs a URL corpus through Firecrawl, scores the output, classifies
common failure modes, compares against a simple baseline fetcher, and suggests
next-attempt configs such as `onlyMainContent`, `excludeTags`, `waitFor`,
`actions`, proxy mode, and parser options.

I tested the first version on a small real corpus. Firecrawl went 5/5 with an
average score of 86.0, and the harness caught useful quality issues like
boilerplate-heavy Wikipedia output. More importantly, the live test exposed two
false positives in my own scorer, so I tightened the heuristics and added
regression tests.

I am interested in working with Firecrawl. I know this is not a full benchmark
yet, but I think the direction is useful: a repeatable loop for finding weak
scrapes, suggesting retry configs, and eventually measuring before/after score
deltas automatically.

If this is interesting, I would love to do a small work trial or take one real
Firecrawl reliability/debugging problem and build against it.

Best,
[Your Name]

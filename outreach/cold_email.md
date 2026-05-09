# Cold Email Draft

Subject: I built a Firecrawl eval and repair harness

Hi [Name],

I have been studying Firecrawl closely, especially v2 `/interact`, `/parse`,
`/agent`, lockdown mode, and the open-source versus cloud split.

Rather than trying to clone Firecrawl, I built a small eval and repair harness
around it. It runs URL corpora through Firecrawl, scores output quality,
classifies failure modes, and suggests concrete retry configs such as
`actions`, `waitFor`, parser modes, proxy mode, and tag filters.

The angle is practical: help Firecrawl users debug bad scrapes faster, and give
your team reproducible cases for improving extraction quality.

Repo: [link]
Demo report: [link]

A few examples the harness catches:

- blocked or CAPTCHA-like responses -> retry with `proxy: "enhanced"`
- JavaScript loading states -> retry with browser actions and longer waits
- short or empty markdown -> retry with full-page debug formats
- PDF misses -> retry with explicit parser modes and bounded `maxPages`

I am trying to earn a shot at working with Firecrawl. If this is useful, I
would love to do a small work trial or send over a benchmark report from a
larger URL corpus.

Best,
[Your Name]


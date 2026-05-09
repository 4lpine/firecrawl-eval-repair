from __future__ import annotations

from .models import ScrapeAttempt


def make_dry_attempt(url: str, index: int) -> ScrapeAttempt:
    lowered = url.lower()
    if "blocked" in lowered or "waf" in lowered:
        return ScrapeAttempt(
            url=url,
            engine="firecrawl",
            ok=False,
            latency_ms=1800,
            markdown="Access denied. Please verify you are human. Cloudflare.",
            error="HTTP 403: blocked by anti-bot page",
            status_code=403,
            config={"formats": ["markdown"], "proxy": "auto"},
        )

    if "javascript" in lowered or "app" in lowered:
        return ScrapeAttempt(
            url=url,
            engine="firecrawl",
            ok=True,
            latency_ms=2400,
            markdown=(
                "# Loading\n\n"
                "Please wait while the application loads. "
                "This site requires JavaScript to render product data."
            ),
            status_code=200,
            config={"formats": ["markdown"]},
        )

    if lowered.split("?")[0].endswith(".pdf"):
        return ScrapeAttempt(
            url=url,
            engine="firecrawl",
            ok=True,
            latency_ms=3100,
            markdown=(
                "# Annual Report\n\n"
                "Executive summary extracted from the document. "
                "The tables are missing and only the first page was parsed."
            ),
            status_code=200,
            config={"formats": ["markdown"], "parsers": ["pdf"]},
        )

    return ScrapeAttempt(
        url=url,
        engine="firecrawl",
        ok=True,
        latency_ms=1200 + index * 100,
        markdown=(
            "# Firecrawl\n\n"
            "Firecrawl helps AI systems search, scrape, crawl, map, parse, "
            "and interact with the web. It returns clean markdown, links, "
            "HTML, screenshots, structured JSON, summaries, and agent-ready "
            "web data.\n\n"
            "## Features\n\n"
            "- Scrape one page into markdown or JSON.\n"
            "- Crawl whole sites with per-page scrape options.\n"
            "- Interact with pages using prompts or code.\n"
            "- Parse documents such as PDFs and spreadsheets.\n\n"
            "## Developer Workflow\n\n"
            "Use the API, SDKs, CLI, MCP server, or agent integrations."
        ),
        status_code=200,
        config={"formats": ["markdown"]},
    )


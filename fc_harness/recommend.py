from __future__ import annotations

from .models import QualityScore, Recommendation, ScrapeAttempt


COMMON_EXCLUDE_TAGS = [
    "nav",
    "footer",
    "header",
    "[role=\"banner\"]",
    "[role=\"navigation\"]",
    ".cookie",
    ".newsletter",
    ".ads",
]


def recommend_retries(
    attempt: ScrapeAttempt, score: QualityScore
) -> list[Recommendation]:
    flags = set(score.flags)
    recs: list[Recommendation] = []

    if "local_network_blocked" in flags:
        return [
            Recommendation(
                name="run_from_network_enabled_environment",
                why=(
                    "The local process could not open outbound sockets. This is "
                    "an execution-environment issue, not evidence that the target "
                    "site blocked Firecrawl."
                ),
                options={
                    "setEnv": "FIRECRAWL_API_KEY",
                    "run": "python -m fc_harness run --urls examples/real_urls.txt --out runs/live --compare-baseline",
                },
            )
        ]

    if "blocked_or_captcha" in flags or _is_network_block(attempt):
        recs.append(
            Recommendation(
                name="retry_with_enhanced_proxy",
                why=(
                    "The response looks blocked, rate-limited, or served by an "
                    "anti-bot interstitial."
                ),
                options={
                    "proxy": "enhanced",
                    "location": {"country": "US", "languages": ["en-US"]},
                    "timeout": 60000,
                    "maxAge": 0,
                },
                cost_note="Enhanced proxy requests cost more credits.",
            )
        )

    if "empty_content" in flags or "short_content" in flags:
        recs.append(
            Recommendation(
                name="retry_full_page_with_debug_formats",
                why=(
                    "The markdown is empty or too short. Main-content filtering "
                    "may have removed useful content, or the page may need more "
                    "rendering time."
                ),
                options={
                    "onlyMainContent": False,
                    "formats": ["markdown", "html", "links"],
                    "waitFor": 2000,
                    "timeout": 60000,
                },
            )
        )

    if "js_or_loading_state" in flags:
        recs.append(
            Recommendation(
                name="retry_with_browser_actions",
                why=(
                    "The extracted content appears to be a JavaScript loading "
                    "state instead of final page content."
                ),
                options={
                    "waitFor": 3000,
                    "actions": [
                        {"type": "wait", "milliseconds": 1500},
                        {"type": "scroll", "direction": "down"},
                        {"type": "wait", "milliseconds": 1000},
                    ],
                    "formats": ["markdown", "links"],
                    "timeout": 90000,
                },
            )
        )

    if "boilerplate_heavy" in flags or "link_farm" in flags:
        recs.append(
            Recommendation(
                name="retry_with_boilerplate_filters",
                why=(
                    "The output looks navigation-heavy or boilerplate-heavy. "
                    "Exclude common layout, cookie, and ad regions."
                ),
                options={
                    "onlyMainContent": True,
                    "excludeTags": COMMON_EXCLUDE_TAGS,
                    "formats": ["markdown", "links"],
                },
            )
        )

    if "no_structure" in flags:
        recs.append(
            Recommendation(
                name="retry_with_html_for_parser_debugging",
                why=(
                    "The page has enough words but little markdown structure. "
                    "Capture HTML to inspect whether headings, lists, or tables "
                    "were lost during conversion."
                ),
                options={
                    "formats": ["markdown", "html", "rawHtml"],
                    "onlyMainContent": False,
                    "timeout": 60000,
                },
            )
        )

    if attempt.url.lower().split("?")[0].endswith(".pdf"):
        recs.append(
            Recommendation(
                name="retry_pdf_auto_then_ocr",
                why=(
                    "The URL looks like a PDF. Use parser mode controls to bound "
                    "cost and fall back to OCR for scanned pages."
                ),
                options={
                    "formats": ["markdown"],
                    "parsers": [{"type": "pdf", "mode": "auto", "maxPages": 25}],
                    "timeout": 120000,
                },
                cost_note="OCR and PDF page parsing can increase cost and latency.",
            )
        )

    if not recs and score.score < 75:
        recs.append(
            Recommendation(
                name="capture_more_diagnostics",
                why=(
                    "The score is mediocre but no single failure mode dominates. "
                    "Capture HTML and links for manual inspection."
                ),
                options={
                    "formats": ["markdown", "html", "links"],
                    "onlyMainContent": False,
                    "timeout": 60000,
                },
            )
        )

    return recs[:4]


def _is_network_block(attempt: ScrapeAttempt) -> bool:
    if _is_local_network_denied(attempt.error):
        return False
    if attempt.status_code in {401, 403, 407, 408, 409, 425, 429, 451, 503}:
        return True
    error = attempt.error.lower()
    return any(
        marker in error
        for marker in (
            "blocked",
            "captcha",
            "cloudflare",
            "forbidden",
            "rate limit",
            "timeout",
        )
    )


def _is_local_network_denied(error: str) -> bool:
    lower = error.lower()
    return any(
        marker in lower
        for marker in (
            "an attempt was made to access a socket in a way forbidden",
            "network is unreachable",
            "operation not permitted",
            "permission denied",
            "winerror 10013",
        )
    )

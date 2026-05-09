from fc_harness.models import ScrapeAttempt
from fc_harness.recommend import recommend_retries
from fc_harness.scoring import score_attempt


def names_for(attempt: ScrapeAttempt) -> set[str]:
    score = score_attempt(attempt)
    return {rec.name for rec in recommend_retries(attempt, score)}


def test_blocked_page_recommends_enhanced_proxy() -> None:
    attempt = ScrapeAttempt(
        url="https://example.com",
        engine="firecrawl",
        ok=False,
        latency_ms=50,
        markdown="Access denied. Cloudflare.",
        status_code=403,
    )

    assert "retry_with_enhanced_proxy" in names_for(attempt)


def test_js_loading_recommends_browser_actions() -> None:
    attempt = ScrapeAttempt(
        url="https://example.com/app",
        engine="firecrawl",
        ok=True,
        latency_ms=50,
        markdown="Loading... This site requires JavaScript.",
        status_code=200,
    )

    assert "retry_with_browser_actions" in names_for(attempt)


def test_pdf_recommends_parser_modes() -> None:
    attempt = ScrapeAttempt(
        url="https://example.com/file.pdf",
        engine="firecrawl",
        ok=True,
        latency_ms=50,
        markdown="# Report\n\nShort parse.",
        status_code=200,
    )

    assert "retry_pdf_auto_then_ocr" in names_for(attempt)


def test_local_network_denial_does_not_recommend_enhanced_proxy() -> None:
    attempt = ScrapeAttempt(
        url="https://example.com",
        engine="baseline",
        ok=False,
        latency_ms=50,
        error=(
            "<urlopen error [WinError 10013] An attempt was made to access "
            "a socket in a way forbidden by its access permissions>"
        ),
    )

    names = names_for(attempt)

    assert "run_from_network_enabled_environment" in names
    assert "retry_with_enhanced_proxy" not in names

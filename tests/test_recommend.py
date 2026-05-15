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


def test_unsupported_site_does_not_recommend_proxy_retry() -> None:
    attempt = ScrapeAttempt(
        url="https://www.reddit.com/r/webscraping/",
        engine="firecrawl",
        ok=False,
        latency_ms=50,
        error="We apologize for the inconvenience but we do not support this site.",
        status_code=403,
    )

    names = names_for(attempt)

    assert "unsupported_site_no_retry" in names
    assert "retry_with_enhanced_proxy" not in names


def test_wikipedia_boilerplate_gets_domain_aware_retry_first() -> None:
    attempt = ScrapeAttempt(
        url="https://en.wikipedia.org/wiki/Web_scraping",
        engine="firecrawl",
        ok=True,
        latency_ms=50,
        markdown=(
            "# Web scraping\n\n"
            "Navigation menu. Privacy policy. Terms of service. Subscribe. "
            + "Article content. " * 500
        ),
        status_code=200,
    )
    score = score_attempt(attempt)
    recs = recommend_retries(attempt, score)

    assert recs[0].name == "retry_wikipedia_article_body"
    assert "#mw-content-text" in recs[0].options["includeTags"]


def test_stripe_docs_boilerplate_gets_domain_aware_retry_first() -> None:
    attempt = ScrapeAttempt(
        url="https://docs.stripe.com/payments/quickstart",
        engine="firecrawl",
        ok=True,
        latency_ms=50,
        markdown=(
            "# Quickstart\n\n"
            "Navigation menu. Privacy policy. Terms of service. Subscribe. "
            + "Payment docs. " * 500
        ),
        status_code=200,
    )
    score = score_attempt(attempt)
    recs = recommend_retries(attempt, score)

    assert recs[0].name == "retry_docs_main_region"
    assert "main" in recs[0].options["includeTags"]

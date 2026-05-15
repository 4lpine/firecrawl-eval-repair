from fc_harness.models import ScrapeAttempt
from fc_harness.scoring import score_attempt


def test_good_markdown_scores_above_short_loading_page() -> None:
    good = ScrapeAttempt(
        url="https://example.com",
        engine="firecrawl",
        ok=True,
        latency_ms=100,
        markdown=(
            "# Title\n\n"
            + "Useful product documentation with details and examples. " * 150
            + "\n\n## API\n\n- One\n- Two\n"
        ),
        status_code=200,
    )
    loading = ScrapeAttempt(
        url="https://example.com/app",
        engine="firecrawl",
        ok=True,
        latency_ms=100,
        markdown="Loading... Please enable JavaScript.",
        status_code=200,
    )

    assert score_attempt(good).score > score_attempt(loading).score
    assert "js_or_loading_state" in score_attempt(loading).flags


def test_blocked_response_gets_blocked_flag() -> None:
    attempt = ScrapeAttempt(
        url="https://example.com",
        engine="firecrawl",
        ok=False,
        latency_ms=100,
        markdown="Access denied. Verify you are human. Cloudflare.",
        status_code=403,
    )

    score = score_attempt(attempt)

    assert "blocked_or_captcha" in score.flags
    assert "request_failed" in score.flags
    assert score.score < 40


def test_local_socket_denial_is_environment_flag() -> None:
    attempt = ScrapeAttempt(
        url="https://example.com",
        engine="baseline",
        ok=False,
        latency_ms=10,
        error=(
            "<urlopen error [WinError 10013] An attempt was made to access "
            "a socket in a way forbidden by its access permissions>"
        ),
    )

    score = score_attempt(attempt)

    assert "local_network_blocked" in score.flags
    assert "blocked_or_captcha" not in score.flags


def test_unsupported_site_gets_specific_flag() -> None:
    attempt = ScrapeAttempt(
        url="https://www.reddit.com/r/webscraping/",
        engine="firecrawl",
        ok=False,
        latency_ms=10,
        error="We apologize for the inconvenience but we do not support this site.",
        status_code=403,
    )

    score = score_attempt(attempt)

    assert "unsupported_site" in score.flags
    assert "request_failed" in score.flags


def test_boilerplate_heavy_flag() -> None:
    attempt = ScrapeAttempt(
        url="https://example.com",
        engine="firecrawl",
        ok=True,
        latency_ms=100,
        markdown=(
            "# Page\n\n"
            "Accept all cookies. Cookie policy. Privacy policy. "
            "Subscribe to newsletter. Terms of service. "
            + "Actual content. " * 80
        ),
        status_code=200,
    )

    assert "boilerplate_heavy" in score_attempt(attempt).flags


def test_long_successful_content_can_mention_antibot_terms() -> None:
    attempt = ScrapeAttempt(
        url="https://example.com/docs",
        engine="baseline",
        ok=True,
        latency_ms=100,
        markdown=(
            "# Proxy docs\n\n"
            "This documentation discusses Cloudflare, CAPTCHA handling, "
            "blocked requests, and rate limit responses. "
            + "Normal documentation content. " * 500
        ),
        status_code=200,
    )

    assert "blocked_or_captcha" not in score_attempt(attempt).flags


def test_long_successful_content_can_have_widget_loading_text() -> None:
    attempt = ScrapeAttempt(
        url="https://example.com/docs",
        engine="firecrawl",
        ok=True,
        latency_ms=100,
        markdown=(
            "# Interact docs\n\n"
            + "Action documentation and examples. " * 500
            + "\n\nChat Widget Loading..."
        ),
        status_code=200,
    )

    assert "js_or_loading_state" not in score_attempt(attempt).flags

from fc_harness.models import QualityScore, Recommendation, ResultRecord, ScrapeAttempt
from fc_harness.retry import choose_retry_recommendation, merge_retry_options


def test_merge_retry_options_overrides_firecrawl_options() -> None:
    base = {"formats": ["markdown"], "timeout": 60000, "onlyMainContent": True}
    retry = {
        "formats": ["markdown", "html", "links"],
        "waitFor": 2000,
        "run": "diagnostic command",
    }

    merged = merge_retry_options(base, retry)

    assert merged == {
        "formats": ["markdown", "html", "links"],
        "timeout": 60000,
        "onlyMainContent": True,
        "waitFor": 2000,
    }
    assert "run" not in merged


def test_choose_retry_skips_costly_by_default() -> None:
    record = ResultRecord(
        attempt=ScrapeAttempt("https://example.com", "firecrawl", True, 100),
        score=QualityScore(20, 10, 100, 0, 0, 0, 0, 0, 0, ["short_content"]),
        recommendations=[
            Recommendation(
                "costly",
                "Costs more.",
                {"proxy": "enhanced"},
                cost_note="Enhanced proxy costs more.",
            ),
            Recommendation("cheap", "Debug formats.", {"formats": ["markdown", "html"]}),
        ],
    )

    assert choose_retry_recommendation(record).name == "cheap"
    assert choose_retry_recommendation(record, allow_costly=True).name == "costly"


def test_choose_retry_skips_diagnostic_options() -> None:
    record = ResultRecord(
        attempt=ScrapeAttempt("https://example.com", "firecrawl", False, 100),
        score=QualityScore(0, 0, 0, 0, 0, 0, 0, 0, 0, ["local_network_blocked"]),
        recommendations=[
            Recommendation("local", "Run elsewhere.", {"run": "python -m fc_harness run"}),
            Recommendation("usable", "Capture HTML.", {"formats": ["markdown", "html"]}),
        ],
    )

    assert choose_retry_recommendation(record).name == "usable"


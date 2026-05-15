from pathlib import Path

import pytest

from fc_harness.cli import read_urls, select_urls


def test_read_urls_ignores_blank_lines_and_hash_comments(tmp_path: Path) -> None:
    url_file = tmp_path / "urls.txt"
    url_file.write_text(
        "\n# heading\nhttps://example.com\n  https://firecrawl.dev  \n",
        encoding="utf-8",
    )

    assert read_urls(url_file) == ["https://example.com", "https://firecrawl.dev"]


def test_select_urls_supports_offset_and_limit() -> None:
    urls = ["a", "b", "c", "d"]

    assert select_urls(urls, start_at=1, max_urls=2) == ["b", "c"]


def test_select_urls_rejects_negative_values() -> None:
    with pytest.raises(SystemExit):
        select_urls(["a"], start_at=-1)

    with pytest.raises(SystemExit):
        select_urls(["a"], max_urls=-1)

from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser

from .models import ScrapeAttempt


class MarkdownishHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.current_link: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in {"h1", "h2", "h3"}:
            self.parts.append("\n" + "#" * int(tag[1]) + " ")
        elif tag in {"p", "div", "section", "article", "br", "tr"}:
            self.parts.append("\n")
        elif tag in {"li"}:
            self.parts.append("\n- ")
        elif tag in {"td", "th"}:
            self.parts.append(" | ")
        elif tag == "a":
            href = dict(attrs).get("href")
            self.current_link = href or None

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "a":
            self.current_link = None
        if tag in {"h1", "h2", "h3", "p", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        if self.current_link:
            self.parts.append(f"[{text}]({self.current_link})")
        else:
            self.parts.append(text + " ")

    def markdown(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def fetch_baseline(url: str, timeout_s: int = 30) -> ScrapeAttempt:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 firecrawl-eval-repair baseline; "
                "contact: local-eval"
            )
        },
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            raw = response.read().decode("utf-8", errors="replace")
            parser = MarkdownishHTMLParser()
            parser.feed(raw)
            latency_ms = int((time.perf_counter() - started) * 1000)
            return ScrapeAttempt(
                url=url,
                engine="baseline",
                ok=True,
                latency_ms=latency_ms,
                markdown=parser.markdown(),
                raw_html=raw,
                status_code=response.status,
                config={"method": "urllib+html.parser"},
            )
    except urllib.error.HTTPError as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return ScrapeAttempt(
            url=url,
            engine="baseline",
            ok=False,
            latency_ms=latency_ms,
            error=f"HTTP {exc.code}",
            status_code=exc.code,
            config={"method": "urllib+html.parser"},
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return ScrapeAttempt(
            url=url,
            engine="baseline",
            ok=False,
            latency_ms=latency_ms,
            error=str(exc),
            config={"method": "urllib+html.parser"},
        )


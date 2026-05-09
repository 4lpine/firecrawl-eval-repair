from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from .models import ScrapeAttempt


class FirecrawlClient:
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.firecrawl.dev",
        timeout_s: int = 90,
    ) -> None:
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.timeout_s = timeout_s

    def scrape(self, url: str, options: dict[str, Any]) -> ScrapeAttempt:
        body = dict(options)
        body["url"] = url
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_url}/v2/scrape",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "firecrawl-eval-repair/0.1",
            },
        )

        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                latency_ms = int((time.perf_counter() - started) * 1000)
                payload_json = json.loads(response_body)
                return self._to_attempt(
                    url=url,
                    options=options,
                    payload=payload_json,
                    latency_ms=latency_ms,
                    status_code=response.status,
                )
        except urllib.error.HTTPError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            error_body = exc.read().decode("utf-8", errors="replace")
            return ScrapeAttempt(
                url=url,
                engine="firecrawl",
                ok=False,
                latency_ms=latency_ms,
                error=self._http_error_message(exc, error_body),
                status_code=exc.code,
                config=options,
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return ScrapeAttempt(
                url=url,
                engine="firecrawl",
                ok=False,
                latency_ms=latency_ms,
                error=str(exc),
                config=options,
            )
        except json.JSONDecodeError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return ScrapeAttempt(
                url=url,
                engine="firecrawl",
                ok=False,
                latency_ms=latency_ms,
                error=f"Invalid JSON response: {exc}",
                status_code=200,
                config=options,
            )

    @staticmethod
    def _http_error_message(exc: urllib.error.HTTPError, body: str) -> str:
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                return str(parsed.get("error") or parsed.get("message") or body)
        except json.JSONDecodeError:
            pass
        return f"HTTP {exc.code}: {body[:500]}"

    @staticmethod
    def _to_attempt(
        url: str,
        options: dict[str, Any],
        payload: dict[str, Any],
        latency_ms: int,
        status_code: int,
    ) -> ScrapeAttempt:
        data = payload.get("data", payload)
        if not isinstance(data, dict):
            data = {}

        metadata = data.get("metadata") or payload.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        ok = bool(payload.get("success", True))
        error = str(payload.get("error", "") or payload.get("message", "") or "")

        doc_status = metadata.get("statusCode") or data.get("statusCode") or status_code
        try:
            doc_status_int = int(doc_status)
        except (TypeError, ValueError):
            doc_status_int = status_code

        return ScrapeAttempt(
            url=url,
            engine="firecrawl",
            ok=ok and not error,
            latency_ms=latency_ms,
            markdown=str(data.get("markdown", "") or ""),
            html=str(data.get("html", "") or ""),
            raw_html=str(data.get("rawHtml", "") or data.get("raw_html", "") or ""),
            error=error,
            status_code=doc_status_int,
            config=options,
            metadata=metadata,
            extracted_json=data.get("json"),
        )


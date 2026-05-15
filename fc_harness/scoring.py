from __future__ import annotations

import math
import re

from .models import QualityScore, ScrapeAttempt


BLOCKED_TERMS = (
    "access denied",
    "are you a human",
    "captcha",
    "cloudflare",
    "forbidden",
    "rate limit",
    "too many requests",
    "unusual traffic",
    "verify you are human",
)

LOADING_TERMS = (
    "enable javascript",
    "javascript is disabled",
    "loading...",
    "please wait",
    "requires javascript",
    "turn on javascript",
)

BOILERPLATE_TERMS = (
    "accept all cookies",
    "advertisement",
    "all rights reserved",
    "cookie policy",
    "cookie settings",
    "newsletter",
    "privacy policy",
    "sign in",
    "subscribe",
    "terms of service",
)

LOCAL_NETWORK_DENIED_TERMS = (
    "an attempt was made to access a socket in a way forbidden",
    "network is unreachable",
    "operation not permitted",
    "permission denied",
    "winerror 10013",
)


def score_attempt(attempt: ScrapeAttempt) -> QualityScore:
    text = attempt.markdown or ""
    lower = text.lower()
    words = re.findall(r"\b[\w'-]+\b", text)
    heading_count = len(re.findall(r"(?m)^#{1,6}\s+\S", text))
    link_count = len(re.findall(r"\[[^\]]{1,120}\]\([^)]+\)", text))
    table_count = len(re.findall(r"(?m)^\s*\|.+\|\s*$", text))
    blocked_hits = sum(lower.count(term) for term in BLOCKED_TERMS)
    loading_hits = sum(lower.count(term) for term in LOADING_TERMS)
    boilerplate_hits = sum(lower.count(term) for term in BOILERPLATE_TERMS)

    flags: list[str] = []
    if not attempt.ok:
        flags.append("request_failed")
    if _unsupported_site(attempt.error):
        flags.append("unsupported_site")
    if _local_network_denied(attempt.error):
        flags.append("local_network_blocked")
    if attempt.status_code and attempt.status_code >= 400:
        flags.append("http_error")
    if not text.strip():
        flags.append("empty_content")
    if 0 < len(words) < 120:
        flags.append("short_content")
    if _looks_blocked(attempt, len(words), blocked_hits, lower):
        flags.append("blocked_or_captcha")
    if _looks_loading_state(len(words), loading_hits, lower):
        flags.append("js_or_loading_state")
    if boilerplate_hits >= 3:
        flags.append("boilerplate_heavy")
    if link_count > max(25, len(words) // 12):
        flags.append("link_farm")
    if heading_count == 0 and len(words) > 250:
        flags.append("no_structure")

    content_score = min(1.0, math.log(len(words) + 1, 900))
    structure_score = min(1.0, heading_count / 4 + table_count / 3)
    cleanliness_penalty = min(0.35, boilerplate_hits * 0.04)
    link_penalty = 0.15 if "link_farm" in flags else 0.0
    blocked_penalty = 0.45 if "blocked_or_captcha" in flags else 0.0
    loading_penalty = 0.25 if "js_or_loading_state" in flags else 0.0
    failure_penalty = 0.45 if "request_failed" in flags else 0.0

    raw = (
        0.62 * content_score
        + 0.18 * structure_score
        + 0.20
        - cleanliness_penalty
        - link_penalty
        - blocked_penalty
        - loading_penalty
        - failure_penalty
    )
    score = int(round(max(0.0, min(1.0, raw)) * 100))

    return QualityScore(
        score=score,
        word_count=len(words),
        char_count=len(text),
        heading_count=heading_count,
        link_count=link_count,
        table_count=table_count,
        boilerplate_hits=boilerplate_hits,
        blocked_hits=blocked_hits,
        loading_hits=loading_hits,
        flags=flags,
    )


def _status_is_blocked(status_code: int | None) -> bool:
    return status_code in {401, 403, 407, 408, 409, 425, 429, 451, 503}


def _looks_blocked(
    attempt: ScrapeAttempt, word_count: int, blocked_hits: int, lower_text: str
) -> bool:
    if _status_is_blocked(attempt.status_code):
        return True
    if not blocked_hits:
        return False

    first_chunk = lower_text[:900]
    hard_interstitials = (
        "access denied",
        "are you a human",
        "verify you are human",
        "unusual traffic",
    )
    if any(term in first_chunk for term in hard_interstitials):
        return True

    if not attempt.ok:
        return True

    if word_count < 300 and blocked_hits >= 1:
        return True
    return blocked_hits >= 4 and word_count < 1200


def _local_network_denied(error: str) -> bool:
    lower = error.lower()
    return any(term in lower for term in LOCAL_NETWORK_DENIED_TERMS)


def _unsupported_site(error: str) -> bool:
    lower = error.lower()
    return "do not support this site" in lower or "unsupported site" in lower


def _looks_loading_state(word_count: int, loading_hits: int, lower_text: str) -> bool:
    if not loading_hits:
        return False

    first_chunk = lower_text[:900]
    hard_loading_terms = (
        "enable javascript",
        "javascript is disabled",
        "loading...",
        "please wait",
        "requires javascript",
        "turn on javascript",
    )
    if word_count < 300 and any(term in first_chunk for term in hard_loading_terms):
        return True

    return loading_hits >= 4 and word_count < 1200

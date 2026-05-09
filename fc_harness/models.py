from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


JsonDict = dict[str, Any]


@dataclass
class ScrapeAttempt:
    url: str
    engine: str
    ok: bool
    latency_ms: int
    markdown: str = ""
    html: str = ""
    raw_html: str = ""
    error: str = ""
    status_code: int | None = None
    config: JsonDict = field(default_factory=dict)
    metadata: JsonDict = field(default_factory=dict)
    extracted_json: Any = None

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "ScrapeAttempt":
        return cls(
            url=str(data.get("url", "")),
            engine=str(data.get("engine", "")),
            ok=bool(data.get("ok", False)),
            latency_ms=int(data.get("latency_ms", 0)),
            markdown=str(data.get("markdown", "") or ""),
            html=str(data.get("html", "") or ""),
            raw_html=str(data.get("raw_html", "") or ""),
            error=str(data.get("error", "") or ""),
            status_code=data.get("status_code"),
            config=dict(data.get("config", {}) or {}),
            metadata=dict(data.get("metadata", {}) or {}),
            extracted_json=data.get("extracted_json"),
        )


@dataclass
class QualityScore:
    score: int
    word_count: int
    char_count: int
    heading_count: int
    link_count: int
    table_count: int
    boilerplate_hits: int
    blocked_hits: int
    loading_hits: int
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "QualityScore":
        return cls(
            score=int(data.get("score", 0)),
            word_count=int(data.get("word_count", 0)),
            char_count=int(data.get("char_count", 0)),
            heading_count=int(data.get("heading_count", 0)),
            link_count=int(data.get("link_count", 0)),
            table_count=int(data.get("table_count", 0)),
            boilerplate_hits=int(data.get("boilerplate_hits", 0)),
            blocked_hits=int(data.get("blocked_hits", 0)),
            loading_hits=int(data.get("loading_hits", 0)),
            flags=list(data.get("flags", []) or []),
        )


@dataclass
class Recommendation:
    name: str
    why: str
    options: JsonDict
    cost_note: str = ""

    def to_dict(self) -> JsonDict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: JsonDict) -> "Recommendation":
        return cls(
            name=str(data.get("name", "")),
            why=str(data.get("why", "")),
            options=dict(data.get("options", {}) or {}),
            cost_note=str(data.get("cost_note", "") or ""),
        )


@dataclass
class ResultRecord:
    attempt: ScrapeAttempt
    score: QualityScore
    recommendations: list[Recommendation] = field(default_factory=list)

    def to_dict(self) -> JsonDict:
        return {
            "attempt": self.attempt.to_dict(),
            "score": self.score.to_dict(),
            "recommendations": [rec.to_dict() for rec in self.recommendations],
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "ResultRecord":
        return cls(
            attempt=ScrapeAttempt.from_dict(data.get("attempt", {}) or {}),
            score=QualityScore.from_dict(data.get("score", {}) or {}),
            recommendations=[
                Recommendation.from_dict(item)
                for item in data.get("recommendations", []) or []
            ],
        )


from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import Recommendation, ResultRecord


DIAGNOSTIC_ONLY_KEYS = {"run", "setEnv"}


def merge_retry_options(
    base_options: dict[str, Any], retry_options: dict[str, Any]
) -> dict[str, Any]:
    merged = deepcopy(base_options)
    for key, value in retry_options.items():
        if key in DIAGNOSTIC_ONLY_KEYS:
            continue
        merged[key] = deepcopy(value)
    return merged


def choose_retry_recommendation(
    record: ResultRecord, allow_costly: bool = False
) -> Recommendation | None:
    for recommendation in record.recommendations:
        if has_diagnostic_only_options(recommendation):
            continue
        if recommendation.cost_note and not allow_costly:
            continue
        return recommendation
    return None


def has_diagnostic_only_options(recommendation: Recommendation) -> bool:
    return any(key in recommendation.options for key in DIAGNOSTIC_ONLY_KEYS)


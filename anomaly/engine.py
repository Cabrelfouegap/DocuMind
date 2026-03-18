from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from adapter import ensure_detector_input_format
from detector import compute_rule_score, detect_rule_based_anomalies
from rules import STATUS_THRESHOLDS


MAX_RULE_SCORE_REFERENCE = 150.0
DEFAULT_ENGINE_VERSION = "rule_based_v1"


def normalize_rule_score(
    rule_score: float,
    max_reference: float = MAX_RULE_SCORE_REFERENCE,
) -> float:
    if max_reference <= 0:
        return 0.0

    normalized_score = (rule_score / max_reference) * 100
    return round(min(normalized_score, 100), 2)


def compute_status_from_score(score: float) -> str:
    for status, (min_score, max_score) in STATUS_THRESHOLDS.items():
        if min_score <= score <= max_score:
            return status
    return "UNKNOWN"


def compute_decision(status: str) -> str:
    return "validation_automatique" if status == "VALID" else "verification_manuelle"


def compute_is_valid(status: str) -> bool:
    return status == "VALID"


def build_validation_payload(
    anomalies: list[dict[str, Any]],
    engine_version: str = DEFAULT_ENGINE_VERSION,
) -> dict[str, Any]:
    rule_score_raw = compute_rule_score(anomalies)
    rule_score_normalized = normalize_rule_score(rule_score_raw)
    status = compute_status_from_score(rule_score_normalized)
    decision = compute_decision(status)
    is_valid = compute_is_valid(status)

    return {
        "isValid": is_valid,
        "ruleScoreRaw": rule_score_raw,
        "ruleScoreNormalized": rule_score_normalized,
        "finalScore": rule_score_normalized,
        "status": status,
        "decision": decision,
        "anomalyCount": len(anomalies),
        "anomaliesDetected": anomalies,
        "lastCheckedAt": datetime.now(timezone.utc).isoformat(),
        "engineVersion": engine_version,
    }


class RuleBasedAnomalyDetector:
    ENGINE_VERSION = DEFAULT_ENGINE_VERSION

    def detect(
        self,
        vendor_data: dict[str, Any],
        source_name: str | None = None,
    ) -> dict[str, Any]:
        normalized_vendor_data = ensure_detector_input_format(
            vendor_data,
            source_name=source_name,
        )

        vendor_id = (
            normalized_vendor_data.get("vendorId")
            or normalized_vendor_data.get("vendor_id")
        )

        anomalies = detect_rule_based_anomalies(normalized_vendor_data)

        return {
            "vendorId": vendor_id,
            "validation": build_validation_payload(
                anomalies=anomalies,
                engine_version=self.ENGINE_VERSION,
            ),
        }
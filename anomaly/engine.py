from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from adapter import ensure_detector_input_format
from detector import compute_rule_score, detect_rule_based_anomalies
from rules import STATUS_THRESHOLDS


MAX_RULE_SCORE_REFERENCE = 150.0
DEFAULT_ENGINE_VERSION = "rule_based_v1"


def normalize_rule_score(
    raw_score: float,
    max_reference: float = MAX_RULE_SCORE_REFERENCE,
) -> float:
    """
    Normalise le score brut sur une échelle de 0 à 100.
    """
    if max_reference <= 0:
        return 0.0

    normalized_score = (raw_score / max_reference) * 100
    return round(min(normalized_score, 100.0), 2)


def compute_status_from_score(score: float) -> str:
    """
    Détermine le statut final à partir du score normalisé.
    """
    for status, (min_score, max_score) in STATUS_THRESHOLDS.items():
        if min_score <= score <= max_score:
            return status

    return "UNKNOWN"


def compute_decision(status: str) -> str:
    """
    Détermine la décision métier associée au statut.
    """
    return "validation_automatique" if status == "VALID" else "verification_manuelle"


def compute_is_valid(status: str) -> bool:
    """
    Retourne True uniquement si le statut final est VALID.
    """
    return status == "VALID"


def build_validation_payload(
    anomalies: list[dict[str, Any]],
    engine_version: str = DEFAULT_ENGINE_VERSION,
) -> dict[str, Any]:
    """
    Construit le bloc de validation final retourné par le moteur.
    """
    raw_score = compute_rule_score(anomalies)
    normalized_score = normalize_rule_score(raw_score)
    status = compute_status_from_score(normalized_score)
    decision = compute_decision(status)
    is_valid = compute_is_valid(status)

    return {
        "isValid": is_valid,
        "ruleScoreRaw": raw_score,
        "ruleScoreNormalized": normalized_score,
        "finalScore": normalized_score,
        "status": status,
        "decision": decision,
        "anomalyCount": len(anomalies),
        "anomaliesDetected": anomalies,
        "lastCheckedAt": datetime.now(timezone.utc).isoformat(),
        "engineVersion": engine_version,
    }


class RuleBasedAnomalyDetector:
    """
    Moteur principal de détection d'anomalies basé sur des règles métier.
    """

    ENGINE_VERSION = DEFAULT_ENGINE_VERSION

    def detect(
        self,
        vendor_data: dict[str, Any],
        source_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Exécute la détection d'anomalies sur un fournisseur 
        """
        normalized_vendor_data = ensure_detector_input_format(
            payload=vendor_data,
            source_name=source_name,
        )

        vendor_id = normalized_vendor_data.get("vendorId")
        anomalies = detect_rule_based_anomalies(normalized_vendor_data)

        return {
            "vendorId": vendor_id,
            "validation": build_validation_payload(
                anomalies=anomalies,
                engine_version=self.ENGINE_VERSION,
            ),
        }
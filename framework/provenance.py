"""Provenance helpers for CLI-emitted metric values.

Every numeric claim from the framework must carry source, confidence, and method
so AI skills can distinguish formula outputs from heuristics.
"""

from __future__ import annotations

from typing import Any, Literal

Source = Literal[
    "observed", "imputed", "declared", "heuristic", "missing", "assumed"
]
Confidence = Literal["high", "medium", "low", "none"]
WeightSource = Literal["none", "placeholder", "repo-fitted"]


def measured(
    value: float | None,
    *,
    source: Source,
    confidence: Confidence = "medium",
    method: str,
    weight_source: WeightSource | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Build a MeasuredValue dict for JSON packs."""
    out: dict[str, Any] = {
        "value": round(value, 4) if value is not None else None,
        "source": source,
        "confidence": confidence,
        "method": method,
    }
    if weight_source is not None:
        out["weight_source"] = weight_source
    if notes:
        out["notes"] = notes
    return out


def scoring_block(
    *,
    scoring_method: str,
    evidence_status: str,
    formula_used: bool,
    weight_source: WeightSource = "none",
) -> dict[str, Any]:
    """Pack-level scoring provenance applied to all numbers in a delta/score pack."""
    return {
        "scoring_method": scoring_method,
        "evidence_status": evidence_status,
        "formula_used": formula_used,
        "weight_source": weight_source,
    }


def unwrap_value(raw: Any, default: float | None = None) -> float | None:
    """Extract a float from a bare number or MeasuredValue dict."""
    if raw is None:
        return default
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, dict):
        v = raw.get("value")
        if v is None:
            return default
        return float(v)
    return default

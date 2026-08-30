"""CLI-owned formula scoring: R, D, V* with explicit provenance.

Every decay input carries per-field provenance (observed / heuristic / imputed)
so downstream skills can disclose which values were measured and which were
filled by policy. When every decay input is a default, D and V* are refused
rather than silently computed from invented numbers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from theory import formula as F

from framework.adapters.github_diff import opacity_from_diff_stats
from framework.provenance import measured, scoring_block, unwrap_value

# Catalog-aligned defaults for decay inputs that lack telemetry.
# entropy: factor catalog says "Impute 0.5 with confidence=low; mark gap".
# blast_radius: catalog says "declare missing; do not invent coupling" — the
# numeric default is retained only so a directional score stays computable when
# other inputs are real, and it is always labeled imputed with an explicit note.
_DECAY_DEFAULTS: dict[str, float] = {
    "entropy": 0.5,
    "opacity": 0.3,
    "blast_radius": 0.2,
    "spec_ambiguity": 0.3,
}

_DECAY_FIELDS = ("entropy", "opacity", "blast_radius", "spec_ambiguity")

_BLAST_DEFAULT_NOTE = (
    "no coupling evidence; catalog declares this missing — "
    "low default used for directional score only"
)


@dataclass
class DecayDerivation:
    """Decay inputs plus per-field provenance."""

    inputs: F.DecayInputs | None
    # field -> {"source": ..., "confidence": ..., "notes": optional}
    provenance: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def defaulted(self) -> list[str]:
        return [
            k
            for k, p in self.provenance.items()
            if p.get("source") == "imputed"
        ]

    @property
    def all_defaulted(self) -> bool:
        return bool(self.provenance) and len(self.defaulted) == len(
            self.provenance
        )


def _prov(source: str, confidence: str, notes: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"source": source, "confidence": confidence}
    if notes:
        out["notes"] = notes
    return out


def _default_prov(fld: str) -> dict[str, Any]:
    notes = _BLAST_DEFAULT_NOTE if fld == "blast_radius" else "no telemetry; policy default"
    return _prov("imputed", "low", notes)


def _activities_from_record(
    rec: dict[str, Any],
) -> tuple[dict[str, float], bool]:
    """Return (activities, assumed_full_pipeline)."""
    activities: dict[str, float] = {}
    factors = rec.get("factor_activity") or rec.get("factors") or {}
    if isinstance(factors, dict):
        for k, v in factors.items():
            if isinstance(v, (int, float)):
                activities[k] = float(v)
            elif v is True:
                activities[k] = 1.0
            elif v is False:
                activities[k] = 0.0
    assumed = False
    if not activities:
        # No observed activity at all: assume the full core pipeline so a
        # directional R exists, but label it — never present as measured.
        activities = {
            n: 1.0 for n in F.CORE_FITTED_FACTORS if n != "review_bot"
        }
        assumed = True
    return (
        {k: v for k, v in activities.items() if k in F.REGISTRY_BY_NAME},
        assumed,
    )


def _decay_inputs_from_record(rec: dict[str, Any]) -> DecayDerivation:
    proxies = rec.get("decay_proxies") or rec.get("proxies") or {}

    def _val(key: str) -> float | None:
        raw = proxies.get(key, rec.get(key))
        return unwrap_value(raw, None)

    raw_vals = {fld: _val(fld) for fld in _DECAY_FIELDS}
    if not any(v is not None for v in raw_vals.values()):
        return DecayDerivation(inputs=None)

    values: dict[str, float] = {}
    prov: dict[str, dict[str, Any]] = {}
    for fld in _DECAY_FIELDS:
        if raw_vals[fld] is not None:
            values[fld] = raw_vals[fld]
            prov[fld] = _prov("observed", "medium")
        else:
            values[fld] = _DECAY_DEFAULTS[fld]
            prov[fld] = _default_prov(fld)

    return DecayDerivation(
        inputs=F.DecayInputs(
            entropy=values["entropy"],
            opacity=values["opacity"],
            blast_radius=values["blast_radius"],
            spec_ambiguity=values["spec_ambiguity"],
        ),
        provenance=prov,
    )


def _decay_inputs_from_intake_pr(pr: dict[str, Any]) -> DecayDerivation:
    files = pr.get("files_changed") or 0
    lines = pr.get("lines_changed") or 0
    signals = pr.get("formula_signals") or {}

    opacity_mv = opacity_from_diff_stats(float(lines), int(files))
    opacity = unwrap_value(opacity_mv, None)

    values: dict[str, float] = {}
    prov: dict[str, dict[str, Any]] = {}

    notes = (signals.get("entropy_notes") or "").lower()
    if "debug" in notes or "fail" in notes:
        values["entropy"] = 0.8
        prov["entropy"] = _prov(
            "heuristic", "low", "entropy notes matched debug/fail keywords"
        )
    elif notes:
        values["entropy"] = 0.5
        prov["entropy"] = _prov(
            "heuristic", "low", "entropy notes present without failure keywords"
        )
    else:
        values["entropy"] = _DECAY_DEFAULTS["entropy"]
        prov["entropy"] = _default_prov("entropy")

    if opacity is not None:
        values["opacity"] = opacity
        prov["opacity"] = _prov(
            "observed", "medium", "soft-saturated from lines/files changed"
        )
    else:
        values["opacity"] = _DECAY_DEFAULTS["opacity"]
        prov["opacity"] = _default_prov("opacity")

    if "shared" in (signals.get("blast_radius_notes") or "").lower():
        values["blast_radius"] = 0.7
        prov["blast_radius"] = _prov(
            "heuristic", "low", "blast notes matched 'shared' keyword"
        )
    else:
        values["blast_radius"] = _DECAY_DEFAULTS["blast_radius"]
        prov["blast_radius"] = _default_prov("blast_radius")

    if "vague" in (signals.get("spec_ambiguity_notes") or "").lower():
        values["spec_ambiguity"] = 0.6
        prov["spec_ambiguity"] = _prov(
            "heuristic", "low", "spec notes matched 'vague' keyword"
        )
    elif not pr.get("acceptance_criteria"):
        values["spec_ambiguity"] = 0.5
        prov["spec_ambiguity"] = _prov(
            "heuristic", "low", "no acceptance criteria provided"
        )
    else:
        values["spec_ambiguity"] = _DECAY_DEFAULTS["spec_ambiguity"]
        prov["spec_ambiguity"] = _default_prov("spec_ambiguity")

    if not notes and not files and not lines:
        return DecayDerivation(inputs=None)

    return DecayDerivation(
        inputs=F.DecayInputs(
            entropy=values["entropy"],
            opacity=values["opacity"],
            blast_radius=values["blast_radius"],
            spec_ambiguity=values["spec_ambiguity"],
        ),
        provenance=prov,
    )


def _proxies_block(decay: DecayDerivation) -> dict[str, Any]:
    """Per-field MeasuredValues carrying each field's own provenance."""
    if not decay.inputs:
        return {}
    values = {
        "entropy": decay.inputs.entropy,
        "opacity": decay.inputs.opacity,
        "blast_radius": decay.inputs.blast_radius,
        "spec_ambiguity": decay.inputs.spec_ambiguity,
    }
    out: dict[str, Any] = {}
    for fld, value in values.items():
        p = decay.provenance.get(fld, _prov("observed", "medium"))
        out[fld] = measured(
            value,
            source=p["source"],
            confidence=p["confidence"],
            method="record_proxy",
            notes=p.get("notes"),
        )
    return out


def score_record(rec: dict[str, Any]) -> dict[str, Any]:
    """Score a single run-record or intake pseudo-record."""
    activities, assumed = _activities_from_record(rec)
    decay = _decay_inputs_from_record(rec)

    r_val = F.recovery_rate(activities)

    refuse = decay.inputs is not None and decay.all_defaulted
    d_val = (
        F.decay_rate(decay.inputs, form=F.DecayForm.HYBRID)
        if decay.inputs and not refuse
        else None
    )
    v_star = (
        F.equilibrium_validity(r_val, d_val) if d_val is not None else None
    )

    if refuse:
        d_note = "all decay inputs defaulted; refusing to compute D from invented values"
        v_note = "all decay inputs defaulted; V* not computed"
    elif decay.inputs is None:
        d_note = "decay proxies missing; D not computed"
        v_note = "cannot compute V* without decay proxies"
    else:
        d_note = None
        v_note = None

    return {
        "run_id": rec.get("run_id"),
        "record_kind": rec.get("record_kind", "run_record"),
        "R": measured(
            r_val,
            source="assumed" if assumed else ("observed" if activities else "imputed"),
            confidence="low" if assumed or not activities else "medium",
            method="recovery_rate",
            weight_source="placeholder",
            notes=(
                "no factor_activity provided; assumed full core pipeline — "
                "treat R as unverified"
                if assumed
                else None
            ),
        ),
        "D": measured(
            d_val,
            source="observed" if d_val is not None else "missing",
            confidence="medium" if d_val is not None else "none",
            method="decay_rate_hybrid" if d_val is not None else "missing_inputs",
            weight_source="placeholder" if d_val is not None else "none",
            notes=d_note,
        ),
        "V_star": measured(
            v_star,
            source="observed" if v_star is not None else "missing",
            confidence="medium" if v_star is not None else "none",
            method="equilibrium_validity",
            weight_source="placeholder" if v_star is not None else "none",
            notes=v_note,
        ),
        "decay_proxies": _proxies_block(decay),
        "recovery_activities": activities,
        "activities_assumed": assumed,
        "defaulted_inputs": decay.defaulted,
        "missing_inputs": [] if decay.inputs else list(_DECAY_FIELDS),
    }


def score_intake_pr(pr: dict[str, Any]) -> dict[str, Any]:
    """Score a single PR from user-intake."""
    signals = pr.get("formula_signals") or {}
    recovery = signals.get("recovery_seen") or []
    activities = {name: 1.0 for name in recovery if name in F.REGISTRY_BY_NAME}
    recovery_assumed = False
    if not activities:
        activities = {
            n: 0.4 for n in ("agentic_qa", "fix_loop") if n in F.REGISTRY_BY_NAME
        }
        recovery_assumed = True

    decay = _decay_inputs_from_intake_pr(pr)

    r_val = F.recovery_rate(activities)

    refuse = decay.inputs is not None and decay.all_defaulted
    d_val = (
        F.decay_rate(decay.inputs, form=F.DecayForm.HYBRID)
        if decay.inputs and not refuse
        else None
    )
    v_star = F.equilibrium_validity(r_val, d_val) if d_val is not None else None

    if refuse:
        v_note = "all decay inputs defaulted; V* not computed"
    else:
        v_note = "intake-derived; not live telemetry"

    user_provenance = signals.get("signal_provenance") or {}
    user_missing = signals.get("missing_signals") or []

    return {
        "pr": pr.get("url_or_number"),
        "record_kind": "intake_pseudo",
        "R": measured(
            r_val,
            source="assumed" if recovery_assumed else "heuristic",
            confidence="low",
            method="recovery_rate_from_intake_signals",
            weight_source="placeholder",
            notes=(
                "no recovery_seen signals; assumed partial QA/fix activity — "
                "treat R as unverified"
                if recovery_assumed
                else None
            ),
        ),
        "D": measured(
            d_val,
            source="heuristic" if d_val is not None else "missing",
            confidence="low" if d_val is not None else "none",
            method="decay_rate_hybrid_from_intake",
            weight_source="placeholder" if d_val is not None else "none",
            notes=(
                "all decay inputs defaulted; refusing to compute D from invented values"
                if refuse
                else None
            ),
        ),
        "V_star": measured(
            v_star,
            source="heuristic" if v_star is not None else "missing",
            confidence="low" if v_star is not None else "none",
            method="equilibrium_validity",
            weight_source="placeholder" if v_star is not None else "none",
            notes=v_note,
        ),
        "decay_proxies": _proxies_block(decay),
        "recovery_activities": activities,
        "recovery_assumed": recovery_assumed,
        "defaulted_inputs": decay.defaulted,
        "missing_inputs": (
            [] if decay.inputs else list(_DECAY_FIELDS)
        ) + [s for s in user_missing if isinstance(s, str)],
        "user_signal_provenance": user_provenance,
    }


def build_score_pack(
    *,
    records: list[dict[str, Any]] | None = None,
    intake_prs: list[dict[str, Any]] | None = None,
    repo: str = "",
) -> dict[str, Any]:
    """Build a score pack from run records and/or intake PRs."""
    scored_runs = [score_record(r) for r in (records or [])]
    scored_prs = [score_intake_pr(pr) for pr in (intake_prs or [])]

    v_stars = [
        unwrap_value(s["V_star"])
        for s in scored_runs + scored_prs
        if unwrap_value(s["V_star"]) is not None
    ]
    aggregate_v_star = (
        round(sum(v_stars) / len(v_stars), 4) if v_stars else None
    )

    claim_warnings = [
        f"formula {F.FORMULA_VERSION} weight_source=placeholder (not repo-fitted)",
        "AI owns metric judgments; CLI owns R/D/V* numbers here",
        "Do not treat intake PR scores as live harness telemetry",
    ]
    if any(s.get("activities_assumed") or s.get("recovery_assumed") for s in scored_runs + scored_prs):
        claim_warnings.append(
            "one or more records had NO observed recovery activity; their R is "
            "assumed, not measured — disclose before citing"
        )
    if any(s.get("defaulted_inputs") for s in scored_runs + scored_prs):
        claim_warnings.append(
            "one or more decay inputs were policy defaults (see per-record "
            "defaulted_inputs); disclose before citing V*"
        )

    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "formula_version": F.FORMULA_VERSION,
        "repo": repo,
        "scoring": scoring_block(
            scoring_method="formula_equilibrium",
            evidence_status=F.EVIDENCE_STATUS,
            formula_used=True,
            weight_source="placeholder",
        ),
        "runs": scored_runs,
        "intake_prs": scored_prs,
        "aggregate": {
            "V_star": measured(
                aggregate_v_star,
                source="observed" if aggregate_v_star is not None else "missing",
                confidence="medium" if aggregate_v_star is not None else "none",
                method="mean_equilibrium_validity",
                weight_source="placeholder" if aggregate_v_star is not None else "none",
            ),
            "n_scored": len(scored_runs) + len(scored_prs),
        },
        "claim_warnings": claim_warnings,
    }


def disclosure_lines(pack: dict[str, Any]) -> list[str]:
    """Human-readable per-record provenance disclosure for stdout."""
    lines: list[str] = []
    for scored in list(pack.get("runs") or []) + list(pack.get("intake_prs") or []):
        label = scored.get("pr") or scored.get("run_id") or "record"
        proxies = scored.get("decay_proxies") or {}
        by_source: dict[str, list[str]] = {}
        for fld, mv in proxies.items():
            src = mv.get("source", "observed") if isinstance(mv, dict) else "observed"
            by_source.setdefault(src, []).append(fld)
        v_star = unwrap_value(scored.get("V_star"))
        if v_star is None:
            missing = scored.get("missing_inputs") or scored.get("defaulted_inputs") or []
            lines.append(
                f"{label}: insufficient data — "
                f"{', '.join(missing) if missing else 'decay inputs unavailable'}; "
                "V* not computed"
            )
            continue
        parts = [
            f"{src}=[{', '.join(sorted(flds))}]"
            for src, flds in sorted(by_source.items())
        ]
        if scored.get("activities_assumed") or scored.get("recovery_assumed"):
            parts.append("R=assumed (no observed recovery activity)")
        lines.append(
            f"{label}: {' '.join(parts)} — treat V*={v_star} as directional"
        )
    return lines


def load_input(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    """Load run records or intake from a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    repo = data.get("repo", "")

    if "prs" in data:
        return [], data.get("prs") or [], repo

    if isinstance(data, list):
        return data, [], repo

    if "runs" in data or "final_v_obs" in data or "run_id" in data:
        if "run_id" in data:
            return [data], [], repo
        return data.get("runs") or [data], [], repo

    return [], [], repo


def write_score_pack(path: str | Path, payload: dict[str, Any]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out

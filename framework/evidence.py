"""Evidence packs for AI diagnosis — no scripted layer verdict.

CLI / collectors produce structured facts. Cursor skills (validity-diagnose,
validity-improve) reason over those facts, choose harness/loop/graph ownership,
and propose fixes. Automations/CLI apply only human-approved changes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from framework.factor_catalog import DECAY_PROXIES, LAYER_BY_FACTOR
from framework.layout import ValidityLayout, load_layout
from framework.packaging_paths import bundled_path
from framework.report import build_validity_report, load_metrics_jsonl


EVIDENCE_PACK_VERSION = "1.0.0"

DIAGNOSIS_PROMPT = """You are diagnosing an AI-native delivery setup (issue → implement → QA → repair → human PR review).

Use ONLY the evidence pack JSON. Do not invent telemetry.

Produce:
1. weakest_layer: harness | loop | graph | unknown (with confidence high|medium|low)
2. rationale: cite specific gaps, stratum outcomes, and missing evidence
3. recommended_controls: ordered list from the intervention catalog ids / factor names
4. review_policy_suggestion: deep / high-level / minimal by stratum (human review never removed)
5. next_actions: what CLI/automation steps to run after human approval
6. open_questions: what evidence is still missing

Hard rules:
- Scripts do not own the diagnosis; you do.
- Prefer instrumentation when evidence is thin.
- completion_guard_hook is simulation-only until live telemetry exists.
- Apply fixes only after human approval, using paths from validity.layout.json.
"""


def build_evidence_pack(
    repo_root: str | Path,
    *,
    layout: ValidityLayout | None = None,
    manifest: dict[str, Any] | None = None,
    records: list[dict] | None = None,
    include_synthetic: bool = False,
    include_heuristic_hint: bool = False,
) -> dict[str, Any]:
    """Assemble facts for an AI diagnoser. No authoritative layer verdict."""
    root = Path(repo_root).resolve()
    layout = layout or load_layout(root)

    if manifest is None:
        manifest_path = layout.resolve(root, "setup_manifest_path")
        if manifest_path and manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if records is None:
        metrics_path = layout.resolve(root, "metrics_path")
        records = []
        if metrics_path and metrics_path.exists():
            # Load all, then optionally keep synthetic for demo packs
            all_recs = load_metrics_jsonl(metrics_path, exclude_synthetic=False)
            records = (
                all_recs
                if include_synthetic
                else [r for r in all_recs if not r.get("synthetic")]
            )

    profile = build_validity_report(
        records,
        repo=f"{root.name}",
        manifest=manifest,
        include_synthetic_warning=True,
    )
    # Strip scripted diagnosis from the AI-facing profile; keep aggregates.
    profile_for_ai = {
        k: v
        for k, v in profile.items()
        if k not in {"layer_diagnosis"}
    }
    profile_for_ai["review_policy"] = {
        **profile.get("review_policy", {}),
        "status": "provisional_thresholds_only",
        "note": (
            "Numeric lane hints below are mechanical thresholds on mean V_obs. "
            "AI diagnosis should confirm or override using task risk and evidence quality."
        ),
        "mechanical_lanes_by_stratum": {
            s: row.get("review_lane") for s, row in profile.get("by_stratum", {}).items()
        },
    }

    factors_by_layer: dict[str, list[str]] = {"harness": [], "loop": [], "graph": [], "unknown": []}
    if manifest:
        for f in manifest.get("factors", []):
            layer = f.get("layer") or LAYER_BY_FACTOR.get(f.get("name", ""), "unknown")
            factors_by_layer.setdefault(layer, []).append(
                {
                    "name": f.get("name"),
                    "enabled": f.get("enabled"),
                    "evidence": f.get("evidence"),
                    "path_ref": f.get("path_ref"),
                }
            )

    pack: dict[str, Any] = {
        "schema_version": EVIDENCE_PACK_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "role_split": {
            "ai": "diagnose layers, explain gaps, propose interventions and review policy",
            "cli": "init/inspect/collect/calibrate/report/evidence; apply approved file changes",
            "automations": "Dev/QA/Fix execution path; not the trust reasoner",
        },
        "layout": layout.to_dict(),
        "setup_manifest": manifest,
        "setup_profile": profile_for_ai,
        "measurement_gaps": (manifest or {}).get("measurement_gaps", []),
        "decay_proxy_definitions": DECAY_PROXIES,
        "factors_by_layer": factors_by_layer,
        "run_summary": {
            "n_records": len(records),
            "n_synthetic": sum(1 for r in records if r.get("synthetic")),
            "strata_present": sorted({r.get("stratum") for r in records if r.get("stratum")}),
            "arms_present": sorted({r.get("arm") for r in records if r.get("arm")}),
        },
        "intervention_catalog_path": _catalog_path(root, layout),
        "diagnosis_instructions": DIAGNOSIS_PROMPT,
        "claim_warnings": profile.get("claim_warnings", []),
    }

    if include_heuristic_hint:
        from framework.report import diagnose_layers

        pack["optional_heuristic_hint"] = {
            "status": "non-authoritative",
            "note": "Keyword scoring only. AI diagnosis overrides this.",
            "result": diagnose_layers(records, manifest),
        }

    return pack


def write_evidence_pack(pack: dict[str, Any], path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
    return out


def _catalog_path(root: Path, layout: ValidityLayout) -> str:
    framework_dir = layout.resolve(root, "framework_dir")
    if framework_dir:
        candidate = framework_dir / "catalog" / "interventions.json"
        if candidate.exists():
            try:
                return str(candidate.relative_to(root))
            except ValueError:
                return str(candidate)
    bundled = bundled_path("catalog", "interventions.json")
    if bundled.is_file():
        return str(bundled)
    return "framework/catalog/interventions.json"

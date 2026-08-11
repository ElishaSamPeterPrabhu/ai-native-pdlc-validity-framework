"""Merge user-provided automation + PR intake into an evidence pack.

Cursor Automations console configs are not API-listable today. Offline repo
inspect sees git/rules/CI only. This module lets teams paste setup + PR evidence
so the AI diagnose skill can reason without console access.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from framework.evidence import DIAGNOSIS_PROMPT, build_evidence_pack
from framework.factor_catalog import LAYER_BY_FACTOR
from framework.layout import load_layout


INTAKE_TEACHING = {
    "why_intake": (
        "Cursor Automations are configured in the console and are not fully "
        "readable via API for listing definitions. Offline git inspect cannot see "
        "triggers/instructions. Paste setup + PR evidence here."
    ),
    "what_we_need_from_setup": [
        "Automation names and roles (dev / qa / fix / scaffold / review)",
        "Triggers (comment, label, PR opened, schedule)",
        "Repo scope and enabled tools/MCP",
        "Stop rules and repair caps (when may the agent say done?)",
        "Whether human review is always required",
        "Declared rules / hooks / CI / review bot (yes/no is enough)",
    ],
    "what_we_need_from_each_pr": [
        "PR URL/number, title, linked issue",
        "Acceptance criteria (from issue or PR checklist)",
        "Labels and CI status",
        "QA/fix comments summary and repair iteration count",
        "Diff size (files/lines) and whether agent claimed done early",
        "What failed or surprised the human reviewer",
        "Optional formula signals: entropy, opacity, blast radius, spec ambiguity, recovery seen",
    ],
    "how_to_make_prs_better_with_ai": [
        "Ask AI to fill the PR body from the issue AC using the formula PR template",
        "Require AC checklist + evidence links (tests, QA comment, screenshots)",
        "State stratum guess (low/medium/high) and blast-radius note",
        "Never claim done without acceptance + tests + QA evidence",
        "After human review, ask AI to map review comments to R/D gaps and one intervention",
    ],
}


def load_intake(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0.0":
        raise ValueError("user-intake.schema_version must be 1.0.0")
    if "repo" not in data:
        raise ValueError("user-intake requires repo")
    return data


def automation_gaps(intake: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    autos = intake.get("automations") or []
    roles = {a.get("role") for a in autos if a.get("enabled", True)}
    for role in ("dev", "qa", "fix"):
        if role not in roles:
            gaps.append(f"automation: no enabled {role} agent declared in intake")
    for a in autos:
        if not a.get("stop_rule"):
            gaps.append(f"automation: {a.get('name', '?')} missing stop_rule")
        if a.get("role") == "fix" and a.get("repair_cap") is None:
            gaps.append(f"automation: {a.get('name', 'fix')} missing repair_cap")
    declared = intake.get("setup_declared") or {}
    if declared.get("human_review_always") is False:
        gaps.append("graph: human_review_always=false — framework requires nonzero human review")
    if declared.get("has_hooks") is False:
        gaps.append("loop: completion_guard / hooks not declared (may be simulation-only still)")
    if declared.get("has_ci_gate") is False:
        gaps.append("loop: ci_gate not declared")
    if not autos:
        gaps.append("automation: none declared — paste console automation details")
    if not intake.get("prs"):
        gaps.append("prs: none provided — attach 1–3 representative AI PRs for diagnosis")
    return gaps


def prs_as_pseudo_records(intake: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn qualitative PR intake into lightweight records for profile aggregates."""
    records = []
    for i, pr in enumerate(intake.get("prs") or []):
        files = pr.get("files_changed") or 0
        lines = pr.get("lines_changed") or 0
        # crude opacity proxy from size when verifier V_obs absent
        opacity = None
        if files or lines:
            opacity = min(1.0, (files / 20.0) * 0.5 + (min(lines, 800) / 800.0) * 0.5)
        ci = pr.get("ci_status")
        final_pass = True if ci == "pass" else False if ci == "fail" else None
        # if agent claimed done but human/QA found issues, mark as not a clean pass
        if pr.get("what_failed_or_surprised") and pr.get("agent_claimed_done"):
            final_pass = False
        recovery = (pr.get("formula_signals") or {}).get("recovery_seen") or []
        records.append(
            {
                "run_id": f"intake-pr-{i}",
                "record_kind": "intake_pseudo",
                "task": pr.get("title") or pr.get("url_or_number"),
                "arm": "intake",
                "stratum": pr.get("stratum_guess")
                if pr.get("stratum_guess") in {"low", "medium", "high"}
                else "medium",
                "synthetic": False,
                "source": "user_intake",
                "final_pass": final_pass,
                "final_v_obs": 1.0 if final_pass is True else 0.0 if final_pass is False else None,
                "fix_iterations": pr.get("fix_iterations") or 0,
                "opacity": opacity,
                "decay_proxies": {
                    "opacity": {
                        "value": opacity,
                        "source": "imputed" if opacity is not None else "missing",
                        "confidence": "low",
                    }
                },
                "factor_activity": {name: 1.0 for name in recovery if name in LAYER_BY_FACTOR},
                "labels": pr.get("labels") or [],
                "pr_url": pr.get("url_or_number"),
            }
        )
    return records


def merge_intake_into_evidence(
    repo_root: str | Path,
    intake: dict[str, Any],
    *,
    include_offline_inspect: bool = True,
    include_synthetic: bool = False,
) -> dict[str, Any]:
    """Build an evidence pack combining optional offline inspect + user intake."""
    root = Path(repo_root).resolve()
    layout = load_layout(root)

    base: dict[str, Any]
    if include_offline_inspect:
        base = build_evidence_pack(
            root,
            layout=layout,
            include_synthetic=include_synthetic,
            include_heuristic_hint=False,
        )
    else:
        base = {
            "schema_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "role_split": {
                "ai": "diagnose layers from intake + optional offline inspect",
                "cli": "intake merge / evidence / report",
                "automations": "console-declared; not API-listed",
            },
            "layout": layout.to_dict(),
            "setup_manifest": None,
            "measurement_gaps": [],
            "run_summary": {"n_records": 0, "n_synthetic": 0, "strata_present": [], "arms_present": []},
            "diagnosis_instructions": DIAGNOSIS_PROMPT,
            "claim_warnings": [],
        }

    gaps = list(base.get("measurement_gaps") or [])
    gaps.extend(automation_gaps(intake))
    # dedupe
    gaps = list(dict.fromkeys(gaps))

    pr_records = prs_as_pseudo_records(intake)
    teaching = {
        **INTAKE_TEACHING,
        "pr_template_path": "framework/templates/intake/pr-body-formula.md",
        "questionnaire_path": "framework/templates/intake/SETUP-QUESTIONNAIRE.md",
    }

    base["intake"] = {
        "schema_version": intake.get("schema_version"),
        "repo": intake.get("repo"),
        "automations": intake.get("automations") or [],
        "setup_declared": intake.get("setup_declared") or {},
        "prs": intake.get("prs") or [],
        "goals": intake.get("goals") or [],
        "mode": "user_provided_online_setup",
    }
    base["measurement_gaps"] = gaps
    base["intake_pr_records"] = pr_records
    base["teaching"] = teaching
    base["online_automation_status"] = {
        "console_api_list": False,
        "method": "user_intake_plus_optional_offline_git_inspect",
        "note": (
            "There is no Automations Management API to list definitions. "
            "Use Cloud Agents API only for launching/monitoring runs, not for reading automation config."
        ),
    }
    # Strengthen diagnosis prompt for intake mode
    base["diagnosis_instructions"] = (
        DIAGNOSIS_PROMPT
        + "\n\nIntake mode: automations and PRs may be user-declared. "
        "Trust console excerpts when present. Map each PR surprise to a decay "
        "pressure or missing recovery control. Teach the team how to improve the "
        "next PR body using teaching.how_to_make_prs_better_with_ai."
    )
    base["generated_at"] = datetime.now(timezone.utc).isoformat()
    return base


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out

"""Repository inspection → setup-manifest (Level 0 Observe).

Paths come from ``validity.layout.json`` (see ``framework.layout``). Do not assume
the research-repo tree exists in adopter repositories.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from framework.factor_catalog import LAYER_BY_FACTOR
from framework.layout import ValidityLayout, load_layout


def _read_text(path: Path, limit: int = 2000) -> str:
    try:
        return path.read_text(encoding="utf-8")[:limit]
    except OSError:
        return ""


def _workflow_names(workflows_dir: Path | None) -> list[str]:
    if not workflows_dir or not workflows_dir.is_dir():
        return []
    names = [p.name for p in workflows_dir.glob("*.yml")]
    names += [p.name for p in workflows_dir.glob("*.yaml")]
    return names


def inspect_repository(
    repo_root: str | Path,
    owner: str = "",
    name: str = "",
    layout_path: str | Path | None = None,
    layout: ValidityLayout | None = None,
) -> dict[str, Any]:
    """Inspect a local checkout and emit a setup-manifest."""
    root = Path(repo_root).resolve()
    owner = owner or root.parent.name
    name = name or root.name
    layout = layout or load_layout(root, layout_path)

    rules_dir = layout.resolve(root, "rules_dir")
    hooks_path = layout.resolve(root, "hooks_path")
    mcp_cfg = layout.resolve(root, "mcp_config_path")
    mcp_dir = layout.resolve(root, "mcp_server_dir")
    workflows_dir = layout.resolve(root, "workflows_dir")

    has_cursor_rules = bool(rules_dir and rules_dir.is_dir() and any(rules_dir.iterdir()))
    # also accept a single rules file at rules_dir if it is a file path mis-set
    if rules_dir and rules_dir.is_file():
        has_cursor_rules = True
    has_mcp = bool((mcp_cfg and mcp_cfg.is_file()) or (mcp_dir and mcp_dir.is_dir()))
    has_hooks = bool(hooks_path and hooks_path.is_file())
    has_gh_workflows = bool(workflows_dir and workflows_dir.is_dir())
    workflow_names = _workflow_names(workflows_dir)

    ci_like = any(
        any(k in w.lower() for k in ("test", "ci", "lint", "a11y", "qa", "merge"))
        for w in workflow_names
    )

    adapters = [
        {
            "name": "github_events",
            "status": "partial",
            "notes": "requires GitHub API / label conventions at Level 1",
        },
        {
            "name": "github_diff",
            "status": "available",
            "notes": "PR diff stats via GitHub API or local git",
        },
        {
            "name": "ci_checks",
            "status": "available" if ci_like else "partial",
            "notes": (
                f"workflows_dir={layout.workflows_dir}; "
                f"files: {', '.join(workflow_names[:8]) or 'none found'}"
            ),
        },
        {
            "name": "cursor_automations",
            "status": "partial",
            "notes": "console-configured; not discoverable from repo files alone",
        },
        {
            "name": "dependency_graph",
            "status": "partial",
            "notes": "run madge/jscpd/etc. to enable blast-radius confidence",
        },
        {
            "name": "qa_repair",
            "status": "partial",
            "notes": "needs label/event telemetry from Dev/QA/Fix path",
        },
        {
            "name": "verifier_checkpoints",
            "status": (
                "partial"
                if layout.exists(root, "tasks_dir")
                else "missing"
            ),
            "notes": (
                f"tasks_dir={layout.tasks_dir}"
                if layout.exists(root, "tasks_dir")
                else "Level 2 task verifiers not required for Observe"
            ),
        },
        {
            "name": "cloud_agent_tokens",
            "status": "partial",
            "notes": "Cloud Agents API; entropy often imputed at Level 0",
        },
    ]

    path_refs = {
        "rules_context": layout.rules_dir or "(unset)",
        "mcp_context": f"{layout.mcp_config_path} or {layout.mcp_server_dir}",
        "ci_gate": layout.workflows_dir or "(unset)",
        "completion_guard_hook": layout.hooks_path or "(unset)",
    }

    factor_presence = []
    declared = {
        "rules_context": has_cursor_rules,
        "mcp_context": has_mcp,
        "ci_gate": ci_like,
        "completion_guard_hook": has_hooks,
        "qa_a11y": any("a11y" in w.lower() for w in workflow_names),
        "checkpointing": False,
        "agentic_qa": False,
        "fix_loop": False,
        "spec_refinement": False,
        "review_bot": False,
    }

    gaps: list[str] = []
    for fname, enabled in declared.items():
        evidence = "declared" if enabled else "missing"
        if fname == "completion_guard_hook" and not enabled:
            gaps.append(
                f"completion_guard_hook not present "
                f"({path_refs['completion_guard_hook']} missing)"
            )
        if fname in ("agentic_qa", "fix_loop", "spec_refinement") and not enabled:
            gaps.append(f"{fname} not detectable from repo files (configure automations)")
        factor_presence.append(
            {
                "name": fname,
                "enabled": bool(enabled),
                "layer": LAYER_BY_FACTOR.get(fname, "unknown"),
                "stage": _stage_for(fname),
                "evidence": evidence,
                "toggle": "see intervention catalog; paths from validity.layout.json",
                "activity_signal": "unobserved until Level 1 collectors run",
                "path_ref": path_refs.get(fname, ""),
            }
        )

    if not has_cursor_rules:
        gaps.append(f"harness: rules_dir absent ({layout.rules_dir or 'unset'})")
    if not has_mcp:
        gaps.append(
            f"harness: MCP absent ({layout.mcp_config_path} / {layout.mcp_server_dir})"
        )
    if not ci_like:
        gaps.append(f"loop: no obvious CI/test workflow gate under {layout.workflows_dir}")

    if layout.source == "discovered":
        gaps.append(
            "layout: validity.layout.json missing — run `python -m framework init --repo .` "
            "so paths are explicit for this repo"
        )
    gaps.extend(f"layout-note: {n}" for n in layout.notes[:6])

    layers = {
        "harness": {
            "present": has_cursor_rules or has_mcp,
            "controls": [
                n for n, on in declared.items() if on and LAYER_BY_FACTOR.get(n) == "harness"
            ],
            "notes": f"rules/MCP from layout ({layout.source})",
        },
        "loop": {
            "present": ci_like or has_hooks,
            "controls": [
                n for n, on in declared.items() if on and LAYER_BY_FACTOR.get(n) == "loop"
            ],
            "notes": "CI/hooks from layout; agentic QA/repair need automation config",
        },
        "graph": {
            "present": has_gh_workflows,
            "controls": [],
            "notes": "label-handoff graph not confirmed from files alone",
        },
    }

    return {
        "schema_version": "1.0.0",
        "repo": {
            "owner": owner,
            "name": name,
            "default_branch": _guess_default_branch(root),
            "url": "",
        },
        "formula_version": _formula_version(root, layout),
        "evidence_status": "observed",
        "layout": {
            "source": layout.source,
            "layout_file": layout.layout_file,
            "paths": {
                "rules_dir": layout.rules_dir,
                "hooks_path": layout.hooks_path,
                "mcp_config_path": layout.mcp_config_path,
                "mcp_server_dir": layout.mcp_server_dir,
                "workflows_dir": layout.workflows_dir,
                "framework_dir": layout.framework_dir,
                "harness_dir": layout.harness_dir,
                "tasks_dir": layout.tasks_dir,
                "data_dir": layout.data_dir,
                "metrics_path": layout.metrics_path,
                "setup_manifest_path": layout.setup_manifest_path,
                "validity_report_path": layout.validity_report_path,
            },
            "notes": layout.notes,
        },
        "layers": layers,
        "factors": factor_presence,
        "evidence_adapters": adapters,
        "measurement_gaps": gaps,
    }


def _stage_for(name: str) -> str:
    mapping = {
        "spec_refinement": "ticket",
        "rules_context": "dev",
        "mcp_context": "dev",
        "checkpointing": "dev",
        "agentic_qa": "qa",
        "ci_gate": "qa",
        "qa_a11y": "qa",
        "fix_loop": "repair",
        "review_bot": "review",
        "completion_guard_hook": "review",
    }
    return mapping.get(name, "dev")


def _guess_default_branch(root: Path) -> str:
    head = root / ".git" / "HEAD"
    text = _read_text(head, 200)
    if text.startswith("ref: refs/heads/"):
        return text.strip().split("/")[-1]
    return "main"


def _formula_version(root: Path, layout: ValidityLayout) -> str:
    try:
        from theory import formula as F

        return F.FORMULA_VERSION
    except Exception:
        return "unknown"


def write_manifest(manifest: dict[str, Any], path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out

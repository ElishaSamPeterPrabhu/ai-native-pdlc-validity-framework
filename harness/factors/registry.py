"""Operational factor definitions.

A FactorDef says, for each factor:
- stage: where in the pipeline it acts (must match theory/formula.py Stage names)
- toggle: the mechanism an arm uses to enable/disable it
- activity: how the collector computes the factor's activity signal f(t) in [0,1]
  from the run record (documented as a description; implemented in collectors.py)

Arm configs are dicts factor-name -> bool (plus options), validated here so a typo
cannot silently create a meaningless arm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ToggleKind(str, Enum):
    AUTOMATION = "automation"  # activate/deactivate a Cursor automation
    BRANCH_VARIANT = "branch_variant"  # arm-specific base branch with a commit
    BRANCH_PROTECTION = "branch_protection"  # required CI check on/off
    PROMPT_VARIANT = "prompt_variant"  # instruction clause present/absent
    APP_INSTALL = "app_install"  # GitHub app / bot enabled on the repo
    DRIVER_BEHAVIOR = "driver_behavior"  # the driver itself changes seeding path


@dataclass(frozen=True)
class FactorDef:
    name: str  # must match theory/formula.py registry
    stage: str  # ticket | dev | qa | repair | review
    toggle: ToggleKind
    toggle_detail: str  # exact operational step (mirrors RETARGET-RUNBOOK.md)
    activity_signal: str  # how collectors derive f(t)
    options: dict = field(default_factory=dict)


FACTORS: dict[str, FactorDef] = {
    f.name: f
    for f in (
        # --- Tier-1 QA hardening factors (added 2026-07-19) ---
        FactorDef(
            name="qa_playwright",
            stage="qa",
            toggle=ToggleKind.BRANCH_PROTECTION,
            toggle_detail="playwright-e2e.yml workflow enabled as required check; OFF = workflow disabled.",
            activity_signal="1.0 while enabled; cross-browser matrix (chromium/firefox/webkit)",
        ),
        FactorDef(
            name="qa_visual",
            stage="qa",
            toggle=ToggleKind.BRANCH_PROTECTION,
            toggle_detail="visual-regression.yml workflow enabled; OFF = workflow disabled.",
            activity_signal="1.0 while enabled; Lost Pixel screenshot diff against baseline.",
        ),
        FactorDef(
            name="qa_a11y",
            stage="qa",
            toggle=ToggleKind.BRANCH_PROTECTION,
            toggle_detail="a11y-check.yml set as required check in branch protection; OFF = informational only.",
            activity_signal="1.0 when blocking gate is enabled; 0.5 when informational.",
        ),
        # --- Split MCP context factors (dev context, each independently ablatable) ---
        FactorDef(
            name="github_mcp",
            stage="dev",
            toggle=ToggleKind.BRANCH_VARIANT,
            toggle_detail="OFF: base branch removes .cursor/mcp.json GitHub MCP entry.",
            activity_signal="1.0 during dev stage when GitHub MCP is connected to the agent.",
        ),
        FactorDef(
            name="figma_mcp",
            stage="dev",
            toggle=ToggleKind.BRANCH_VARIANT,
            toggle_detail="OFF: base branch removes .cursor/mcp.json Figma MCP entry.",
            activity_signal="1.0 during dev stage when Figma MCP is connected; primary for design-system tasks.",
        ),
        FactorDef(
            name="spec_refinement",
            stage="ticket",
            toggle=ToggleKind.DRIVER_BEHAVIOR,
            toggle_detail=(
                "ON: seed issue through the Issue Scaffolding webhook (auto_approve). "
                "OFF: driver creates the issue directly with the task's spec_raw body, "
                "labels it spec:raw and approved itself."
            ),
            activity_signal="1.0 for the whole run if the issue body contains "
            "structured acceptance criteria (scaffolded), else 0.0",
        ),
        FactorDef(
            name="agentic_qa",
            stage="qa",
            toggle=ToggleKind.AUTOMATION,
            toggle_detail="QA Agent automation Active / Inactive on the fork trigger.",
            activity_signal="1.0 from PR-opened until terminal state when enabled",
        ),
        FactorDef(
            name="fix_loop",
            stage="repair",
            toggle=ToggleKind.AUTOMATION,
            toggle_detail=(
                "Fix Agent automation Active / Inactive. Iteration cap variant is a "
                "prompt edit (3 -> 1) recorded in options.cap."
            ),
            activity_signal="fraction of iteration budget remaining: "
            "(cap - iterations_used) / cap, stepping down at each qa-failed event",
            options={"cap": 3},
        ),
        FactorDef(
            name="ci_gate",
            stage="qa",
            toggle=ToggleKind.BRANCH_PROTECTION,
            toggle_detail=(
                "Branch protection on experiment-base requires the test workflow "
                "check; OFF removes the required check."
            ),
            activity_signal="1.0 while enabled (deterministic gate, always-on within arm)",
        ),
        FactorDef(
            name="mcp_context",
            stage="dev",
            toggle=ToggleKind.BRANCH_VARIANT,
            toggle_detail=(
                "ON: experiment-base includes .cursor/mcp.json pointing at the in-repo "
                "mcp/ server. OFF: base branch experiment-base-nomcp removes it."
            ),
            activity_signal="1.0 during the dev stage when the base branch has MCP config",
        ),
        FactorDef(
            name="rules_context",
            stage="dev",
            toggle=ToggleKind.BRANCH_VARIANT,
            toggle_detail=(
                "ON: .cursor/rules/ present (code-guidelines.mdc). "
                "OFF: base branch experiment-base-norules removes the directory."
            ),
            activity_signal="1.0 during the dev stage when rules are present",
        ),
        FactorDef(
            name="checkpointing",
            stage="dev",
            toggle=ToggleKind.PROMPT_VARIANT,
            toggle_detail=(
                "Dev Agent instruction includes the frequent-commit clause; the OFF "
                "variant omits it. Sobol ranked commit cadence the top parameter - "
                "this arm is promoted into the pilot."
            ),
            activity_signal="observed commit cadence, saturated: "
            "min(1, commits_per_hour / 4)",
        ),
        FactorDef(
            name="review_bot",
            stage="review",
            toggle=ToggleKind.APP_INSTALL,
            toggle_detail="Cursor Bugbot enabled/disabled on the fork "
            "(fallbacks: CodeRabbit, Greptile - see research/pipeline-scan.md).",
            activity_signal="1.0 from PR-opened until terminal state when installed",
        ),
        FactorDef(
            name="human_alignment",
            stage="review",
            toggle=ToggleKind.PROMPT_VARIANT,
            toggle_detail="Deferred to the iPad phase; M(t)=0 in all v1 arms.",
            activity_signal="rate of needs-human/clarification events (0 in v1)",
        ),
        FactorDef(
            name="completion_guard_hook",
            stage="review",
            toggle=ToggleKind.PROMPT_VARIANT,
            toggle_detail=(
                "SIMULATION-ONLY until live .cursor/hooks.json telemetry exists. "
                "Template: framework/templates/hooks/hooks.json. Not in v1 live arms."
            ),
            activity_signal="1.0 at completion-validation boundary when hook challenges done",
        ),
    )
}


# Named arms for the campaign. Baseline = everything ON (the production pipeline);
# each ablation flips exactly one factor (Phase-B identifiability requirement:
# analyze arm contrasts, not only joint fits). qa+fix are toggled together in
# 'no_recovery_loop' AND separately, because the sim showed they collide otherwise.
ARMS: dict[str, dict] = {
    "baseline": {},
    "no_spec_refinement": {"spec_refinement": False},
    "no_agentic_qa": {"agentic_qa": False},
    "no_fix_loop": {"fix_loop": False},
    "fix_cap_1": {"fix_loop": {"cap": 1}},
    "no_recovery_loop": {"agentic_qa": False, "fix_loop": False},
    "no_ci_gate": {"ci_gate": False},
    "no_mcp": {"mcp_context": False},
    "no_rules": {"rules_context": False},
    "no_checkpointing": {"checkpointing": False},
    "with_review_bot": {"review_bot": True},  # review bot is OFF in baseline
    # Tier-1 QA hardening arms (for round-2 comparison)
    "tier1_qa": {"qa_playwright": True, "qa_visual": True, "qa_a11y": True},
    "no_qa_playwright": {"qa_playwright": False},
    "no_qa_visual": {"qa_visual": False},
    "no_qa_a11y": {"qa_a11y": False},
    "no_figma_mcp": {"figma_mcp": False},
    "no_github_mcp": {"github_mcp": False},
    "bare": {
        "spec_refinement": False,
        "agentic_qa": False,
        "fix_loop": False,
        "ci_gate": False,
        "mcp_context": False,
        "rules_context": False,
        "checkpointing": False,
    },
}

# Baseline state for factors not mentioned in an arm dict.
BASELINE_STATE: dict[str, bool] = {
    "spec_refinement": True,
    "agentic_qa": True,
    "fix_loop": True,
    "ci_gate": True,
    "mcp_context": True,
    "rules_context": True,
    "checkpointing": True,
    "review_bot": False,
    "human_alignment": False,
    # Tier-1 QA factors (ON in hardened baseline, OFF in round-1 baseline)
    "qa_playwright": False,
    "qa_visual": False,
    "qa_a11y": False,
    "github_mcp": True,
    "figma_mcp": True,
    # Simulation-only factor; keep OFF in live baseline until hook telemetry lands.
    "completion_guard_hook": False,
}


def validate_arm(overrides: dict) -> None:
    for name in overrides:
        if name not in FACTORS:
            raise KeyError(f"unknown factor {name!r} in arm config")


def arm_config(arm_name: str) -> dict[str, object]:
    """Resolve an arm name to a full factor-state dict."""
    if arm_name not in ARMS:
        raise KeyError(f"unknown arm {arm_name!r}; known: {sorted(ARMS)}")
    overrides = ARMS[arm_name]
    validate_arm(overrides)
    state: dict[str, object] = dict(BASELINE_STATE)
    state.update(overrides)
    return state

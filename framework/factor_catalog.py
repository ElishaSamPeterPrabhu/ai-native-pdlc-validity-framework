"""Portable factor catalog: construct, telemetry, layer, missing-data rules."""

from __future__ import annotations

from typing import Any

# layer ownership used for diagnosis
LAYER_BY_FACTOR: dict[str, str] = {
    "spec_refinement": "graph",
    "agentic_qa": "loop",
    "fix_loop": "loop",
    "ci_gate": "loop",
    "mcp_context": "harness",
    "rules_context": "harness",
    "checkpointing": "harness",
    "review_bot": "graph",
    "human_alignment": "graph",
    "qa_playwright": "loop",
    "qa_visual": "loop",
    "qa_a11y": "loop",
    "github_mcp": "harness",
    "figma_mcp": "harness",
    "qa_token_drift": "loop",
    "qa_design_fidelity": "loop",
    "qa_api_contract": "loop",
    "qa_mutation": "loop",
    "qa_size_budget": "loop",
    "gate_changesets": "graph",
    "gate_security": "graph",
    "completion_guard_hook": "loop",
    # Candidate process-discipline factors (v1.2; no evidence yet)
    "plan_fidelity": "loop",
    "abstention_quality": "graph",
    "error_msg_quality": "loop",
    "runtime_feedback_hooks": "loop",
    "rollback_reversibility": "harness",
}

# Candidate factor constructs (v1.2). Sources: RigorBench (arXiv:2606.22678),
# ProcBench (arXiv:2605.20251), LH-Bench (arXiv:2603.22744), AgentRx taxonomy.
CANDIDATE_FACTOR_CONSTRUCTS: dict[str, dict[str, str]] = {
    "plan_fidelity": {
        "construct": "Plan exists and execution matched it (planning fidelity)",
        "telemetry": "Plan artifact present + step-vs-plan deviation from run trace",
        "missing_behavior": "activity=0; candidate — no claim until ablation",
    },
    "abstention_quality": {
        "construct": "Agent escalates or stops instead of guessing (know when to fold)",
        "telemetry": "needs-human / clarification events at genuinely blocked points",
        "missing_behavior": "activity=0; candidate — no claim until ablation",
    },
    "error_msg_quality": {
        "construct": "Verifier/QA failure messages are actionable for repair",
        "telemetry": "Repair success rate conditioned on failure-report structure",
        "missing_behavior": "activity=0; candidate — no claim until ablation",
    },
    "runtime_feedback_hooks": {
        "construct": "Structured feedback surfaced during execution (test-time verification)",
        "telemetry": "Hook events emitting structured findings mid-run",
        "missing_behavior": "activity=0; candidate — no claim until ablation",
    },
    "rollback_reversibility": {
        "construct": "Changes stay interruptible/reversible mid-run (control preservation)",
        "telemetry": "Revert-capable checkpoints; clean rollback drills",
        "missing_behavior": "activity=0; candidate — no claim until ablation",
    },
}

# Candidate decay proxies (v1.2). Registered constructs only: they are NOT part
# of the D(t) computation in formula v1.x and carry no weights. Telemetry can be
# collected now; entering D(t) requires a formula revision plus simulation.
CANDIDATE_DECAY_PROXIES: dict[str, dict[str, str]] = {
    "instruction_drift": {
        "construct": "Deviation from pinned acceptance criteria over long context",
        "telemetry": "AC-vs-diff divergence across checkpoints; plan-adherence audits",
        "normalization": "to be defined at formula revision",
        "missing_behavior": "not in D(t); collect telemetry only",
        "status": "candidate",
        "layer": "loop",
    },
    "tool_misuse_rate": {
        "construct": "Malformed or repeated no-progress tool calls",
        "telemetry": "Invalid invocation count / repeated identical failing calls",
        "normalization": "to be defined at formula revision",
        "missing_behavior": "not in D(t); collect telemetry only",
        "status": "candidate",
        "layer": "harness",
    },
    "goal_misalignment": {
        "construct": "Pursuing the wrong objective despite locally valid steps",
        "telemetry": "Intent-vs-outcome audits on completed runs",
        "normalization": "to be defined at formula revision",
        "missing_behavior": "not in D(t); collect telemetry only",
        "status": "candidate",
        "layer": "graph",
    },
}

DECAY_PROXIES: dict[str, dict[str, str]] = {
    "entropy": {
        "construct": "Contextual entropy (Hc): thrash / failed tools / saturated context",
        "telemetry": "Agent token use + failed/total tool calls, or qualitative thrash notes",
        "normalization": "entropy_proxy(T_cur, T_max, fail, total) → [0,1]",
        "missing_behavior": "Impute 0.5 with confidence=low; mark gap",
        "confidence_rule": "high if tokens+tools observed; low if imputed",
        "layer": "harness",
        "maps_to_metric": "Hc",
    },
    "opacity": {
        "construct": "Change opacity (O): hard-to-review footprint of the deliverable",
        "telemetry": "Diff/patch size, spread, complexity — any VCS or change manifest",
        "normalization": "opacity_proxy(...) soft-saturated → [0,1]",
        "missing_behavior": "Impute from file/count alone if available",
        "confidence_rule": "high with full change stats; medium with size only",
        "layer": "graph",
        "maps_to_metric": "O",
    },
    "blast_radius": {
        "construct": "Blast radius (Cb): how widely a mistake can propagate",
        "telemetry": "Dependency/impact reach, or declared shared/public/prod surface",
        "normalization": "impacted / total when graph exists; else declared [0,1]",
        "missing_behavior": "Declare missing; do not invent coupling",
        "confidence_rule": "high with graph; medium with declared blast; none if absent",
        "layer": "harness",
        "maps_to_metric": "Cb",
    },
    "spec_ambiguity": {
        "construct": "Specification ambiguity (σspec): unclear/contested done criteria",
        "telemetry": "Plan disagreement, or raw vs refined task contract",
        "normalization": "clip to [0,1]",
        "missing_behavior": "Use raw/refined proxy at medium confidence",
        "confidence_rule": "high with multi-plan similarity; medium with label/proxy",
        "layer": "graph",
        "maps_to_metric": "sigma_spec",
    },
}


def factor_entries(formula_module: Any) -> list[dict[str, Any]]:
    """Build portable registry rows from theory.formula."""
    sim_only = getattr(formula_module, "SIMULATION_ONLY_FACTORS", frozenset())
    candidates = getattr(formula_module, "CANDIDATE_FACTORS", frozenset())
    rows: list[dict[str, Any]] = []
    for factor in formula_module.DEFAULT_REGISTRY:
        name = factor.name
        if name in candidates:
            evidence = "candidate"
        elif name in sim_only:
            evidence = "simulation-only"
        else:
            evidence = "operational"
        if name == "human_alignment":
            evidence = "deferred"
        candidate_meta = CANDIDATE_FACTOR_CONSTRUCTS.get(name, {})
        if name in candidates:
            confidence_rule = "candidate — no evidence; excluded from claims until ablation"
        elif name in sim_only:
            confidence_rule = "simulation-only until live telemetry"
        else:
            confidence_rule = "high when toggle and activity both observed"
        rows.append(
            {
                "name": name,
                "stage": factor.stage.value,
                "layer": LAYER_BY_FACTOR.get(name, "unknown"),
                "construct": candidate_meta.get(
                    "construct", f"Recovery control contributing to R(t): {name}"
                ),
                "telemetry": candidate_meta.get(
                    "telemetry", "arm toggle + collector activity f(t) ∈ [0,1]"
                ),
                "normalization": "activity clipped to [0,1]; weight w_f units 1/time",
                "missing_behavior": candidate_meta.get(
                    "missing_behavior", "activity=0 when disabled or unobserved"
                ),
                "confidence_rule": confidence_rule,
                "toggle": "see harness/factors/registry.py",
                "evidence_status": evidence,
                "placeholder_weight": factor.weight,
            }
        )
    return rows


def export_registry(formula_module: Any) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "formula_version": formula_module.FORMULA_VERSION,
        "default_decay_form": formula_module.DEFAULT_DECAY_FORM_NAME,
        "core_fitted_factors": list(formula_module.CORE_FITTED_FACTORS),
        "simulation_only_factors": sorted(formula_module.SIMULATION_ONLY_FACTORS),
        "candidate_factors": sorted(
            getattr(formula_module, "CANDIDATE_FACTORS", frozenset())
        ),
        "decay_proxies": DECAY_PROXIES,
        "candidate_decay_proxies": CANDIDATE_DECAY_PROXIES,
        "factors": factor_entries(formula_module),
    }

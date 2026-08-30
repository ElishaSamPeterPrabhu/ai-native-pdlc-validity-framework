"""Single shared definition of the validity formula.

Every consumer (sim/, harness/, analysis/, dashboard/, framework/) imports this
module; nothing else in the codebase hardcodes the model. Revisions are versioned
here and explained in formula-changelog.md.

Current version: v1.2 (candidate process-discipline factors registered from the
agent-evaluation literature; no numeric change to D(t) or fitted claims).
Factor weights remain placeholders until Phase D fits real campaign data (v2).
Default decay form for analysis is HYBRID; MULTIPLICATIVE is kept only as a
model-comparison baseline.

Model summary (see theory/derivation.md for the derivation):

    dV/dt = (1 - V) * R(t) - V * D(t)

    R(t) = sum over enabled factors of w_f * f(t)         (factor registry)
    D(t) = combination of normalized decay proxies        (form selected by data)

    V_delivered = V(t_end) * pass_hat_k * max(0, 1 - O_A / O_M)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

FORMULA_VERSION = "v1.2"
# Evidence status for published claims. Do not treat placeholder weights as fitted.
EVIDENCE_STATUS = "simulation-calibrated"  # not yet "modus-fitted" / "multi-repo"
DEFAULT_DECAY_FORM_NAME = "hybrid"


# ---------------------------------------------------------------------------
# Decay proxies (normalized to [0, 1])
# ---------------------------------------------------------------------------

def entropy_proxy(
    tokens_current: float,
    tokens_max: float,
    tool_calls_failed: float,
    tool_calls_total: float,
) -> float:
    """Contextual entropy H_c: context saturation amplified by tool-failure rate.

    v0 outline form was (T/Tmax) * (1 + fail_rate), which exceeds 1; here the
    failure amplification is folded in and the result clipped to [0, 1].
    """
    if tokens_max <= 0:
        return 0.0
    saturation = min(1.0, max(0.0, tokens_current / tokens_max))
    fail_rate = (
        tool_calls_failed / tool_calls_total if tool_calls_total > 0 else 0.0
    )
    return min(1.0, saturation * (1.0 + fail_rate) / 2.0 + fail_rate / 2.0)


def opacity_proxy(
    delta_loc: float,
    delta_cc: float,
    files_touched: int,
    saturation_scale: float = 60.0,
) -> float:
    """Diff opacity O: structural review burden, saturated into [0, 1].

    Raw score follows the outline (log2(1+LOC) * (1+CC) * files); the exponential
    soft-saturation keeps huge diffs from dominating the fit by scale alone.
    ``saturation_scale`` is a Phase-B sensitivity target (assumption A4).
    """
    if delta_loc < 0:
        delta_loc = abs(delta_loc)
    raw = math.log2(1.0 + delta_loc) * (1.0 + max(0.0, delta_cc)) * max(1, files_touched)
    return 1.0 - math.exp(-raw / saturation_scale)


def blast_radius_proxy(dependents_of_changed: int, dependents_total: int) -> float:
    """Blast radius / coupling C_b: dependency-graph reach of the changed files."""
    if dependents_total <= 0:
        return 0.0
    return min(1.0, max(0.0, dependents_of_changed / dependents_total))


def spec_ambiguity_proxy(mean_pairwise_plan_similarity: float) -> float:
    """Spec ambiguity sigma: 1 - mean pairwise cosine similarity of 3 plans."""
    return min(1.0, max(0.0, 1.0 - mean_pairwise_plan_similarity))


@dataclass(frozen=True)
class DecayInputs:
    """Normalized decay proxies for one time segment (all in [0, 1])."""

    entropy: float
    opacity: float
    blast_radius: float
    spec_ambiguity: float


class DecayForm(str, Enum):
    """Candidate functional forms for D(t); Phase D selects by AIC/BIC."""

    MULTIPLICATIVE = "multiplicative"  # v0 outline form
    ADDITIVE = "additive"
    HYBRID = "hybrid"  # additive + blast_radius x spec_ambiguity interaction


@dataclass(frozen=True)
class DecayWeights:
    """Weights for the decay term (units: 1 / time)."""

    baseline: float = 0.01
    entropy: float = 0.05
    opacity: float = 0.05
    blast_radius: float = 0.05
    spec_ambiguity: float = 0.05
    interaction_cs: float = 0.05  # blast_radius x spec_ambiguity (HYBRID only)
    multiplicative_rate: float = 0.5  # d0 for the MULTIPLICATIVE form


def decay_rate(
    inputs: DecayInputs,
    weights: DecayWeights = DecayWeights(),
    form: DecayForm = DecayForm.HYBRID,
) -> float:
    """D(t) >= 0 for one time segment.

    Default form is HYBRID (v1 decision from Phase B). MULTIPLICATIVE remains
    available for AIC/BIC model comparison only.
    """
    if form is DecayForm.MULTIPLICATIVE:
        return (
            weights.multiplicative_rate
            * inputs.blast_radius
            * inputs.spec_ambiguity
            * inputs.entropy
            * inputs.opacity
        )
    if form is DecayForm.ADDITIVE:
        return (
            weights.baseline
            + weights.entropy * inputs.entropy
            + weights.opacity * inputs.opacity
            + weights.blast_radius * inputs.blast_radius
            + weights.spec_ambiguity * inputs.spec_ambiguity
        )
    if form is DecayForm.HYBRID:
        return (
            weights.baseline
            + weights.entropy * inputs.entropy
            + weights.opacity * inputs.opacity
            + weights.blast_radius * inputs.blast_radius
            + weights.spec_ambiguity * inputs.spec_ambiguity
            + weights.interaction_cs * inputs.blast_radius * inputs.spec_ambiguity
        )
    _exhaustive: "never" = form  # type: ignore[assignment]
    raise AssertionError(f"unhandled decay form: {form}")


# ---------------------------------------------------------------------------
# Recovery: the factor registry
# ---------------------------------------------------------------------------

class Stage(str, Enum):
    TICKET = "ticket"
    DEV = "dev"
    QA = "qa"
    REPAIR = "repair"
    REVIEW = "review"


@dataclass(frozen=True)
class Factor:
    """A toggleable setup element whose value is measured by ablation.

    ``weight`` (w_f, units 1/time) is a placeholder until Phase D; do not publish
    as fitted. ``activity`` in [0, 1] is the factor's telemetry signal for the
    current time segment; 0 when the factor is disabled for the run.
    """

    name: str
    stage: Stage
    weight: float


# Core campaign factors (fitted jointly in analysis/fit.py) plus optional tiers.
# Placeholder weights are deliberately near-equal; Phase D replaces them.
# completion_guard_hook is simulation-measured only until live hook telemetry exists.
DEFAULT_REGISTRY: tuple[Factor, ...] = (
    Factor("spec_refinement", Stage.TICKET, 0.10),
    Factor("agentic_qa", Stage.QA, 0.10),
    Factor("fix_loop", Stage.REPAIR, 0.10),
    Factor("ci_gate", Stage.QA, 0.10),
    Factor("mcp_context", Stage.DEV, 0.10),
    Factor("rules_context", Stage.DEV, 0.10),
    Factor("checkpointing", Stage.DEV, 0.10),
    Factor("review_bot", Stage.REVIEW, 0.10),
    Factor("human_alignment", Stage.REVIEW, 0.10),  # M(t)=0 until iPad phase
    # Tier-1 QA hardening factors (registered 2026-07-19)
    Factor("qa_playwright", Stage.QA, 0.10),
    Factor("qa_visual", Stage.QA, 0.08),
    Factor("qa_a11y", Stage.QA, 0.08),
    # Split MCP context factors
    Factor("github_mcp", Stage.DEV, 0.08),
    Factor("figma_mcp", Stage.DEV, 0.08),
    # Tier-2: design-system-specific QA (registered 2026-07-19)
    Factor("qa_token_drift", Stage.QA, 0.08),
    Factor("qa_design_fidelity", Stage.QA, 0.08),
    Factor("qa_api_contract", Stage.QA, 0.10),
    # Tier-3: test quality, size, hygiene, security (registered 2026-07-19)
    Factor("qa_mutation", Stage.QA, 0.10),
    Factor("qa_size_budget", Stage.QA, 0.06),
    Factor("gate_changesets", Stage.REVIEW, 0.05),
    Factor("gate_security", Stage.REVIEW, 0.05),
    # Completion-boundary recovery (simulation-only; not live-fitted)
    Factor("completion_guard_hook", Stage.REVIEW, 0.10),
    # Candidate process-discipline factors (registered 2026-08-30 from the
    # agent-evaluation literature; see formula-changelog v1.2). No simulation
    # or live evidence yet: they contribute to R only when activity is
    # actually observed, and no effect claim is allowed until ablation.
    Factor("plan_fidelity", Stage.DEV, 0.08),
    Factor("abstention_quality", Stage.DEV, 0.08),
    Factor("error_msg_quality", Stage.QA, 0.08),
    Factor("runtime_feedback_hooks", Stage.DEV, 0.08),
    Factor("rollback_reversibility", Stage.DEV, 0.08),
)

# Factors with identifiable arm contrasts in the Modus campaign design.
CORE_FITTED_FACTORS: tuple[str, ...] = (
    "spec_refinement",
    "agentic_qa",
    "fix_loop",
    "ci_gate",
    "mcp_context",
    "rules_context",
    "checkpointing",
    "review_bot",
)

# Simulation-only until .cursor/hooks.json telemetry lands on the live path.
SIMULATION_ONLY_FACTORS: frozenset[str] = frozenset({"completion_guard_hook"})

# Registered candidates with no simulation or live evidence yet. They may be
# toggled in future ablation arms; until then they carry placeholder weights,
# contribute zero R unless observed, and support no published claims.
CANDIDATE_FACTORS: frozenset[str] = frozenset(
    {
        "plan_fidelity",
        "abstention_quality",
        "error_msg_quality",
        "runtime_feedback_hooks",
        "rollback_reversibility",
    }
)

REGISTRY_BY_NAME: dict[str, Factor] = {f.name: f for f in DEFAULT_REGISTRY}


def recovery_rate(
    activities: dict[str, float],
    registry: dict[str, Factor] = REGISTRY_BY_NAME,
) -> float:
    """R(t) = sum of w_f * f(t) over factors present in ``activities``.

    ``activities`` maps factor name -> activity in [0, 1] for the segment.
    Unknown factor names raise: silent typos would corrupt a whole campaign.
    """
    total = 0.0
    for name, activity in activities.items():
        if name not in registry:
            raise KeyError(f"unknown factor {name!r}; register it first")
        total += registry[name].weight * min(1.0, max(0.0, activity))
    return total


# ---------------------------------------------------------------------------
# The ODE and its closed-form pieces
# ---------------------------------------------------------------------------

def dv_dt(v: float, recovery: float, decay: float) -> float:
    """dV/dt = (1 - V) R - V D."""
    return (1.0 - v) * recovery - v * decay


def equilibrium_validity(recovery: float, decay: float) -> float:
    """V* = R / (R + D); 1.0 when both are ~0 (nothing decays, nothing to fix)."""
    total = recovery + decay
    if total <= 1e-12:
        return 1.0
    return recovery / total


def relaxation_time(recovery: float, decay: float) -> float:
    """Time constant tau = 1 / (R + D) toward equilibrium (inf if both ~0)."""
    total = recovery + decay
    return math.inf if total <= 1e-12 else 1.0 / total


def integrate_v(
    v0: float,
    segments: list[tuple[float, float, float]],
) -> list[tuple[float, float]]:
    """Integrate V(t) over piecewise-constant segments (assumption A5).

    ``segments`` is a list of (duration, recovery, decay). Within each segment the
    ODE is linear and has the exact solution
        V(t) = V* + (V0 - V*) exp(-(R + D) t).
    Returns [(t_end_of_segment, V)] including the initial point (0, v0).
    """
    points = [(0.0, v0)]
    t, v = 0.0, v0
    for duration, recovery, decay in segments:
        v_star = equilibrium_validity(recovery, decay)
        rate = recovery + decay
        v = v_star + (v - v_star) * math.exp(-rate * duration)
        t += duration
        points.append((t, v))
    return points


# ---------------------------------------------------------------------------
# Delivered validity: consistency and review economics
# ---------------------------------------------------------------------------

def pass_hat_k(successes: int, trials: int) -> float:
    """Empirical per-task all-trials-succeed estimate: (c/n)^n-style plug-in.

    With c successes out of n i.i.d. trials, the plug-in estimate of P(all n
    succeed) is (c/n)**n. Campaign-level pass^k averages this across tasks.
    """
    if trials <= 0:
        return 0.0
    return (successes / trials) ** trials


def review_economics_gate(overhead_agent: float, overhead_manual: float) -> float:
    """max(0, 1 - O_A / O_M): validity is zero when review costs exceed manual work."""
    if overhead_manual <= 0:
        return 0.0
    return max(0.0, 1.0 - overhead_agent / overhead_manual)


def delivered_validity(
    v_end: float,
    consistency: float,
    overhead_agent: float,
    overhead_manual: float,
) -> float:
    """V_delivered = V(t_end) * pass^k * economics gate."""
    return v_end * consistency * review_economics_gate(overhead_agent, overhead_manual)


class TrustVerdict(str, Enum):
    MERGE_WORTHY = "merge-worthy"
    REVIEW_CAREFULLY = "review-carefully"
    ABANDON = "abandon"


# Placeholder thresholds; replaced by observed V_delivered tertiles after the campaign.
THRESHOLD_HIGH = 0.65
THRESHOLD_LOW = 0.30


def trust_verdict(
    v_delivered: float,
    threshold_high: float = THRESHOLD_HIGH,
    threshold_low: float = THRESHOLD_LOW,
) -> TrustVerdict:
    if v_delivered >= threshold_high:
        return TrustVerdict.MERGE_WORTHY
    if v_delivered >= threshold_low:
        return TrustVerdict.REVIEW_CAREFULLY
    return TrustVerdict.ABANDON

"""Monte Carlo agent-trajectory generator.

Simulates an autonomous run as a sequence of tool-call steps with per-step failure,
context growth, and error loops, then emits synthetic telemetry shaped like what the
Phase-C harness will collect from real runs: per-commit checkpoints with normalized
decay proxies, factor activity, and a verifier pass-fraction V_obs.

The generator deliberately does NOT integrate the ODE. It simulates the micro-process
(steps, failures, repairs); the ODE is the macro-model we later fit against these
trajectories. Agreement between the two is evidence the ODE structure is adequate.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import formula as F


@dataclass(frozen=True)
class TaskProfile:
    """Ground-truth task characteristics for a simulated run."""

    name: str
    n_checks: int  # verifier granularity (m checks)
    steps_expected: int  # typical number of agent steps
    blast_radius: float  # in [0, 1]
    spec_ambiguity: float  # in [0, 1]
    base_step_error: float  # epsilon: per-step probability of breaking a check


# Complexity strata roughly calibrated to the Phase-C task suite design.
LOW = TaskProfile("low", n_checks=4, steps_expected=15, blast_radius=0.05,
                  spec_ambiguity=0.15, base_step_error=0.010)
MEDIUM = TaskProfile("medium", n_checks=8, steps_expected=45, blast_radius=0.25,
                     spec_ambiguity=0.35, base_step_error=0.018)
HIGH = TaskProfile("high", n_checks=12, steps_expected=110, blast_radius=0.55,
                   spec_ambiguity=0.55, base_step_error=0.028)

STRATA: dict[str, TaskProfile] = {p.name: p for p in (LOW, MEDIUM, HIGH)}


@dataclass(frozen=True)
class SetupConfig:
    """Which factors are enabled for the simulated run (the ablation arm)."""

    spec_refinement: bool = True
    agentic_qa: bool = True
    fix_loop: bool = True
    fix_iteration_cap: int = 3
    ci_gate: bool = True
    mcp_context: bool = True
    rules_context: bool = True
    checkpointing: bool = True
    review_bot: bool = False
    completion_guard_hook: bool = False
    # v1.3 discipline factors. Their mechanisms are inert unless the matching
    # MicroParams knob is nonzero, so existing seeded experiments reproduce
    # bit-identically under default parameters.
    red_first_discipline: bool = False
    reviewer_independence: bool = False
    evidence_freshness: bool = False
    doctrine_reinjection: bool = False

    def activities(
        self,
        fix_budget_remaining: float,
        hook_active: float = 0.0,
    ) -> dict[str, float]:
        """Factor activity signals for formula.recovery_rate."""
        return {
            "spec_refinement": 1.0 if self.spec_refinement else 0.0,
            "agentic_qa": 1.0 if self.agentic_qa else 0.0,
            "fix_loop": fix_budget_remaining if self.fix_loop else 0.0,
            "ci_gate": 1.0 if self.ci_gate else 0.0,
            "mcp_context": 1.0 if self.mcp_context else 0.0,
            "rules_context": 1.0 if self.rules_context else 0.0,
            "checkpointing": 1.0 if self.checkpointing else 0.0,
            "review_bot": 1.0 if self.review_bot else 0.0,
            "completion_guard_hook": (
                hook_active if self.completion_guard_hook else 0.0
            ),
            "red_first_discipline": 1.0 if self.red_first_discipline else 0.0,
            "reviewer_independence": 1.0 if self.reviewer_independence else 0.0,
            "evidence_freshness": 1.0 if self.evidence_freshness else 0.0,
            "doctrine_reinjection": 1.0 if self.doctrine_reinjection else 0.0,
        }


@dataclass(frozen=True)
class MicroParams:
    """Micro-process parameters (ground truth for identifiability studies).

    These are the knobs the Sobol analysis sweeps. They shape how factor toggles
    and task properties translate into step-level behavior.
    """

    # How strongly spec refinement reduces effective ambiguity.
    refinement_ambiguity_cut: float = 0.6
    # How strongly MCP + rules context reduce per-step error (multipliers < 1).
    mcp_error_mult: float = 0.75
    rules_error_mult: float = 0.85
    # Context growth: tokens consumed per step as a fraction of the window.
    tokens_per_step_frac: float = 0.006
    # Error-loop feedback: extra per-step error at full context saturation.
    entropy_error_gain: float = 0.05
    # Ambiguity feedback: extra per-step error at full ambiguity.
    ambiguity_error_gain: float = 0.04
    # Probability a deterministic CI gate catches a broken check at a commit.
    ci_catch_prob: float = 0.7
    # Probability the agentic QA stage catches a broken check at PR time.
    qa_catch_prob: float = 0.6
    # Probability one fix iteration actually repairs a caught check.
    fix_success_prob: float = 0.65
    # Probability the agent silently fixes its own breakage next commit.
    self_repair_prob: float = 0.10
    # Commit cadence: steps between commits (checkpointing on halves this).
    steps_per_commit: int = 12
    # Tool-call failure probability per step (drives H_c telemetry).
    tool_fail_prob: float = 0.08
    # Completion-guard hook: per-broken-check detection probability at stop.
    # Sweep this in experiments; do not treat the default as a fitted claim.
    hook_detect_prob: float = 0.8
    # Completion-guard hook: max interventions at the stop boundary.
    hook_max_interventions: int = 1
    # --- v1.3 discipline mechanisms (all inert at 0.0 defaults) -----------
    # Without red-first discipline: probability a successful repair is
    # vacuously green (test-after theater) — the check stays broken but is
    # masked from every later catch stage because its evidence looks green.
    vacuous_green_prob: float = 0.0
    # Terminal review catch probabilities per actually-broken check.
    # Anchored review trusts the authoring context (cannot see masked checks);
    # independent review re-derives evidence (can). Review runs only when the
    # relevant probability is nonzero.
    review_catch_anchored: float = 0.0
    review_catch_independent: float = 0.0
    # Without evidence freshness: probability a green check is invalidated by
    # trailing polish edits after the last verify. With freshness ON a forced
    # terminal re-verify precedes the completion claim.
    stale_evidence_prob: float = 0.0
    # Without doctrine reinjection: per-step error multiplier ramps up to
    # (1 + drift_ramp) by the end of the run (process amnesia).
    drift_ramp: float = 0.0


@dataclass
class Checkpoint:
    """One telemetry sample: what the harness would record at a commit."""

    t: float  # normalized time (fraction of expected run length)
    v_obs: float  # verifier pass-fraction
    entropy: float
    opacity: float
    blast_radius: float
    spec_ambiguity: float
    activities: dict[str, float] = field(default_factory=dict)


@dataclass
class RunResult:
    task: str
    config: SetupConfig
    checkpoints: list[Checkpoint]
    final_pass: bool  # all verifier checks green at terminal state
    fix_iterations_used: int
    steps_taken: int
    hook_interventions: int = 0
    # v1.3 telemetry: what the agent believes vs what the verifier says.
    self_claimed_pass: bool = True
    vacuous_greens: int = 0
    stale_breaks: int = 0
    review_repairs: int = 0


def simulate_run(
    task: TaskProfile,
    config: SetupConfig,
    params: MicroParams = MicroParams(),
    rng: np.random.Generator | None = None,
) -> RunResult:
    """Simulate one run at step granularity, sampling telemetry at commits."""
    rng = rng or np.random.default_rng()

    ambiguity = task.spec_ambiguity * (
        1.0 - (params.refinement_ambiguity_cut if config.spec_refinement else 0.0)
    )
    error_mult = 1.0
    if config.mcp_context:
        error_mult *= params.mcp_error_mult
    if config.rules_context:
        error_mult *= params.rules_error_mult

    checks_ok = np.ones(task.n_checks, dtype=bool)
    # masked: vacuously-green checks (test-after theater) — actually broken but
    # invisible to CI/QA/self-repair/hook because their evidence looks green.
    masked = np.zeros(task.n_checks, dtype=bool)
    # stale_hidden: checks broken by trailing edits after the last verify; the
    # agent's evidence still shows them green.
    stale_hidden = np.zeros(task.n_checks, dtype=bool)
    vacuous_count = 0
    stale_count = 0
    review_repairs = 0
    tokens_frac = 0.0
    tool_calls = 0
    tool_fails = 0
    cum_loc = 0.0
    files_touched = 1
    checkpoints: list[Checkpoint] = []

    def attempt_repair(idx: int) -> None:
        """One repair attempt; without red-first discipline it may be vacuous."""
        nonlocal vacuous_count
        if rng.random() < params.fix_success_prob:
            if (
                params.vacuous_green_prob > 0.0
                and not config.red_first_discipline
                and rng.random() < params.vacuous_green_prob
            ):
                masked[idx] = True
                vacuous_count += 1
            else:
                checks_ok[idx] = True

    steps_per_commit = max(
        2, params.steps_per_commit // (2 if config.checkpointing else 1)
    )
    # Dev phase runs a bit long on ambiguous tasks (agent flails more).
    n_steps = int(task.steps_expected * (1.0 + ambiguity))

    def record(
        t_frac: float,
        fix_budget: float,
        hook_active: float = 0.0,
    ) -> None:
        checkpoints.append(
            Checkpoint(
                t=t_frac,
                v_obs=float(checks_ok.mean()),
                entropy=F.entropy_proxy(tokens_frac, 1.0, tool_fails, max(1, tool_calls)),
                opacity=F.opacity_proxy(cum_loc, 0.3, files_touched),
                blast_radius=task.blast_radius,
                spec_ambiguity=ambiguity,
                activities=config.activities(fix_budget, hook_active=hook_active),
            )
        )

    record(0.0, 1.0)

    # --- Dev phase -------------------------------------------------------
    for step in range(1, n_steps + 1):
        tokens_frac = min(1.0, tokens_frac + params.tokens_per_step_frac)
        tool_calls += 1
        if rng.random() < params.tool_fail_prob:
            tool_fails += 1
        cum_loc += rng.exponential(8.0)
        if rng.random() < 0.15:
            files_touched += 1

        # Effective per-step error: base, scaled by context factors, inflated by
        # entropy (error loops) and residual ambiguity, spread by blast radius.
        eps = task.base_step_error * error_mult
        eps *= 1.0 + params.entropy_error_gain * tokens_frac / task.base_step_error * 0.01
        eps *= 1.0 + params.ambiguity_error_gain * ambiguity / task.base_step_error * 0.01
        # Instruction drift (process amnesia): without doctrine reinjection the
        # per-step error rate ramps up over the run.
        if params.drift_ramp > 0.0 and not config.doctrine_reinjection:
            eps *= 1.0 + params.drift_ramp * (step / n_steps)
        n_at_risk = 1 + int(task.blast_radius * (task.n_checks - 1))
        for idx in rng.choice(task.n_checks, size=n_at_risk, replace=False):
            if checks_ok[idx] and rng.random() < eps:
                checks_ok[idx] = False

        # Progress: the agent is also building the feature — each step has a chance
        # of turning a not-yet-green check green (front-loaded early in the run).
        # Masked checks are believed done, so the agent does not work on them.
        progress_p = 2.0 / steps_per_commit
        broken = np.flatnonzero(~checks_ok & ~masked)
        if broken.size and rng.random() < progress_p:
            checks_ok[rng.choice(broken)] = True

        if step % steps_per_commit == 0:
            # Self-repair at commit: agent notices its own breakage sometimes,
            # more often when a CI gate runs on every commit.
            catch_p = params.self_repair_prob + (
                params.ci_catch_prob * 0.5 if config.ci_gate else 0.0
            )
            for idx in np.flatnonzero(~checks_ok & ~masked):
                if rng.random() < catch_p:
                    attempt_repair(idx)
            record(step / n_steps, 1.0)

    # --- QA / fix loop ----------------------------------------------------
    # QA runs the visible test evidence, so masked (vacuously green) checks
    # cannot be caught here.
    fix_used = 0
    if config.agentic_qa:
        cap = config.fix_iteration_cap if config.fix_loop else 0
        while not checks_ok.all() and fix_used < cap:
            caught = [
                idx for idx in np.flatnonzero(~checks_ok & ~masked)
                if rng.random() < params.qa_catch_prob
                or (config.ci_gate and rng.random() < params.ci_catch_prob)
            ]
            if not caught:
                break
            fix_used += 1
            for idx in caught:
                attempt_repair(idx)
            budget = 1.0 - fix_used / max(1, cap)
            cum_loc += rng.exponential(4.0)
            record(1.0 + 0.15 * fix_used, budget)

    # --- Trailing polish edits / evidence staleness ------------------------
    # After the last verify, polish edits can invalidate green checks. Without
    # evidence freshness the completion claim still uses the stale snapshot;
    # with it, a forced terminal re-verify reveals the breaks and gets one
    # bounded repair pass.
    if params.stale_evidence_prob > 0.0:
        stale_idxs: list[int] = []
        for idx in np.flatnonzero(checks_ok):
            if rng.random() < params.stale_evidence_prob:
                checks_ok[idx] = False
                stale_idxs.append(int(idx))
                stale_count += 1
        if stale_idxs:
            cum_loc += rng.exponential(2.0)
            if config.evidence_freshness:
                for idx in stale_idxs:
                    attempt_repair(idx)
                record(1.40, 0.0)
            else:
                stale_hidden[stale_idxs] = True

    # --- Completion-guard hook (stop boundary) ----------------------------
    # Detects remaining broken checks when the agent tries to stop and forces
    # one bounded repair pass through the existing fix_success_prob. Blind to
    # semantic misreads that leave checks green (driven by spec_ambiguity).
    #
    # Trailing agent steps after the last commit can change checks without a
    # checkpoint, so record the true pre-hook terminal state before the guard
    # runs. This keeps hook-off / hook-on V_obs comparisons honest.
    record(1.45, 0.0, hook_active=0.0)

    hook_interventions = 0
    if config.completion_guard_hook and not checks_ok.all():
        for intervention in range(params.hook_max_interventions):
            if checks_ok.all():
                break
            # The hook checks that evidence exists, not that it is honest or
            # fresh: masked and stale-hidden checks are invisible to it.
            caught = [
                idx
                for idx in np.flatnonzero(~checks_ok & ~masked & ~stale_hidden)
                if rng.random() < params.hook_detect_prob
            ]
            if not caught:
                break
            hook_interventions += 1
            for idx in caught:
                attempt_repair(idx)
            cum_loc += rng.exponential(3.0)
            record(1.5 + 0.1 * intervention, 0.0, hook_active=1.0)

    # --- Terminal review (anchored vs independent) -------------------------
    # An anchored reviewer trusts the authoring context's evidence, so masked
    # and stale-hidden checks stay invisible. An independent reviewer
    # re-derives evidence in a fresh context and can see every broken check.
    review_p = (
        params.review_catch_independent
        if config.reviewer_independence
        else params.review_catch_anchored
    )
    if review_p > 0.0 and not checks_ok.all():
        if config.reviewer_independence:
            visible = np.flatnonzero(~checks_ok)
        else:
            visible = np.flatnonzero(~checks_ok & ~masked & ~stale_hidden)
        caught = [int(i) for i in visible if rng.random() < review_p]
        for idx in caught:
            # The reviewer surfaced the truth: belief resyncs regardless of
            # whether the repair lands. Reviewer-observed reds are genuine, so
            # the repair is never vacuous.
            masked[idx] = False
            stale_hidden[idx] = False
            if rng.random() < params.fix_success_prob:
                checks_ok[idx] = True
                review_repairs += 1
        if caught:
            cum_loc += rng.exponential(3.0)
            record(1.7, 0.0)

    # The agent's completion claim is based on the evidence it can see:
    # actually-green checks plus vacuous greens plus stale snapshots.
    believed_ok = checks_ok | masked | stale_hidden

    return RunResult(
        task=task.name,
        config=config,
        checkpoints=checkpoints,
        final_pass=bool(checks_ok.all()),
        fix_iterations_used=fix_used,
        steps_taken=n_steps,
        hook_interventions=hook_interventions,
        self_claimed_pass=bool(believed_ok.all()),
        vacuous_greens=vacuous_count,
        stale_breaks=stale_count,
        review_repairs=review_repairs,
    )


def simulate_arm(
    task: TaskProfile,
    config: SetupConfig,
    k: int = 3,
    n_tasks: int = 10,
    params: MicroParams = MicroParams(),
    seed: int | None = None,
) -> list[RunResult]:
    """Simulate an experiment arm: n_tasks task instances x k repeats.

    Each run gets an independent RNG stream derived from ``seed``. Sharing one
    stream across runs would make later runs depend on whether earlier runs
    consumed extra randomness (for example a completion-guard hook), which
    breaks fair ON/OFF ablations.
    """
    seed_rng = np.random.default_rng(seed)
    results: list[RunResult] = []
    for _ in range(n_tasks * k):
        run_seed = int(seed_rng.integers(0, 2**31 - 1))
        results.append(
            simulate_run(task, config, params, np.random.default_rng(run_seed))
        )
    return results


def arm_pass_hat_k(results: list[RunResult], k: int) -> float:
    """Campaign pass^k: group consecutive k repeats, average the all-pass plug-in."""
    groups = [results[i : i + k] for i in range(0, len(results), k)]
    vals = [F.pass_hat_k(sum(r.final_pass for r in g), len(g)) for g in groups if g]
    return float(np.mean(vals)) if vals else 0.0

# Task Suite

Each task is a JSON file conforming to `schema.md`, plus a verifier directory.

Design rules (from the plan and Phase-B findings):

1. **Verifiers live here, not in the fork.** Agents can read anything in the repo;
   grading material must be invisible to them. At grading time the harness copies
   `verifier/*.spec.ts` into the repo checkout, runs `npx stencil test --spec` scoped
   to those files at each commit of the PR branch, and removes them again.
2. **Verifiers are implementation-agnostic** (DeepSWE rule): they assert requested
   behavior via the component's public API/DOM, never a specific implementation.
3. **Each verifier has m named checks** (individual `it()` blocks). V_obs(t) =
   fraction passing at a commit. More checks = finer V(t) resolution; aim m ≥ 4.
4. **Two spec variants per task**: `spec_raw` (one-liner, as a user would file it)
   and `spec_refined` (structured acceptance criteria). The driver picks per arm.
5. **Strata are calibrated by estimated human time** (METR-style):
   Low ≈ ≤1h, Medium ≈ 2–4h, High ≈ 1–2 days.
6. **Sources**: `upstream-issue` (real open issue), `rebroken-fix` (revert a merged
   upstream bugfix on the experiment branch; the original PR is ground truth),
   `synthetic` (authored for coverage).

Status: 9 tasks defined (3 per stratum) — enough for the pilot and first campaign
arms; extend toward ~10/stratum before the full campaign by following the same
pattern (open issues #1254, #1249, #1246, #1265, #1266 are the next candidates;
`git log upstream/main --grep fix` supplies more rebroken-fix tasks).

Pilot verifiers implemented: `low-card-hover`, `low-alert-blend`, `med-badge-align`
(the three used by the pilot). Remaining verifiers are stubs to be filled before
their arms run.

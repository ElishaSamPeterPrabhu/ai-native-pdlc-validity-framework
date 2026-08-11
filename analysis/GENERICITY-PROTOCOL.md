# Genericity validation protocol (Phase E stretch — runs after the main campaign)

Claim to evidence: the formula's **structure** (ODE + factor registry + normalized
proxies) transfers across domains; only the **constants** are repo-specific.

## Protocol

1. Pick a non-frontend repo you own (any backend/CLI project with a test suite).
2. Re-instantiate the factor registry with the same nine factor names — only the
   toggle mechanics change (e.g. `ci_gate` = that repo's test workflow; `mcp_context`
   = whatever context server applies, or marked not-applicable).
3. Port 4–6 tasks (2 per stratum, prefer rebroken-fix source: revert a merged fix,
   the fix is ground truth) with hand-written verifiers, same schema as
   `harness/tasks/schema.md`.
4. Run `baseline`, `bare`, and `no_recovery_loop` arms at k=3 (~36–54 runs).
5. Fit with `analysis/fit.py` on the new repo's data alone.

## Pass criteria (pre-registered so the claim is falsifiable)

- The decay form selected by AIC/BIC on the new repo matches the modus campaign's
  selection (structural transfer).
- Sign and ordering of the arm contrasts match (recovery loop helps most on High;
  bare agent collapses on High) even if magnitudes differ.
- Report re-fitted constants side by side; do NOT claim constant transfer.

## Explicitly deferred (iPad phase)

- M(t) human-alignment experiments (agent pauses answered from the iPad).
- Human review-time and Likert trust logging (closes the review-economics loop).
- `needs-human` label events collected in the main campaign are the first M(t)
  observable and should be reported descriptively in the paper's future-work.

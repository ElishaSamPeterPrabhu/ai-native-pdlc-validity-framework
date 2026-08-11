# Agent handoff — Validity Framework (next phase)

Use this brief when continuing Modus Level 1–2 work or onboarding a new agent.

## Role split (non-negotiable)

| Owner | Owns | Does not own |
| --- | --- | --- |
| **CLI** | Mechanical facts, `intake_heuristic_scores`, R/D/V* via `score` (`weight_source: placeholder`) | Which metric is "right" for a failure |
| **AI** | Metric assessments, layer diagnosis, one intervention, review policy | Inventing fitted R/D/V* or weights |
| **Human** | Approve **apply** (hooks/rules/automations) | Required on every metric call — optional |

## Ordered CLI chain

From the **research repo** (`Autonomous-Agent(Research)`):

```bash
python -m framework init --repo <target>
python -m framework inspect --repo <target>
# paste intake → data/user-intake.json
python -m framework intake --repo <target> --intake data/user-intake.json
python -m framework score --repo <target> --input data/user-intake.json
python -m framework delta --repo <target> --before <prior> --after <failed>
python -m framework evidence --repo <target>
# Cursor skills: validity-diagnose → (human) → validity-improve-from-delta → validity-improve
python -m framework calibrate --repo <target>   # when pilot gates pass
```

For Modus product repo, prefer `--repo /path/to/modus-wc-2.0` from research (do not copy only `framework/` — needs `theory/`).

## Modus artifacts already present

Under `modus-wc-2.0/data/`:

- `setup-manifest.json`, `user-intake.json`, `evidence-pack.json`
- `delta-pack.json`, `diagnosis.json`, `improvement-plan.json`
- `validity-analysis.md` — **regenerate**; prior manual V* in markdown was invalid

## Provenance rules

1. Delta packs with `scoring_method: intake_keyword_heuristic` are **not** formula outputs.
2. `provisional_v_star` in reports is a MeasuredValue — `null` when proxies missing (never aliased to `mean_v_obs`).
3. Intake rows use `record_kind: intake_pseudo` — not live harness telemetry.
4. `data/fit_results.json` marked SYNTHETIC — do not publish as Modus-fitted.

## Do not

- Invent formula R, D, V*, or fitted weights in prose/markdown
- Treat heuristic delta scores as ODE/fitted truth
- Publish claims from `--include-synthetic` reports or SYNTHETIC fit_results
- Apply hooks/rules/automations without human approval

## Do

- AI owns metric judgments in `diagnosis.json` / `improvement-plan.json` (cite evidence)
- Quote `python -m framework score` for CLI-owned equilibria
- One intervention per round; retest same stratum
- Human always reviews PRs (depth scales with trust)

## Next phase (after this hardening)

1. Apply approved Dev preflight in Cursor Automations (from `improvement-plan.json`)
2. Retest one medium `qa-full`; new intake + delta
3. Unblock live pilot — see `harness/PILOT-STATUS.md` (fork, GitHub app, spend)
4. 6 real runs → `metrics.jsonl` → `calibrate` when gates pass
5. Campaign ablations → formula v2 fit

## Key paths

| Path | Purpose |
| --- | --- |
| `framework/CONTRACT.md` | Claim boundaries |
| `framework/catalog/metric-playbooks.json` | Top-level metrics + AI mapping |
| `framework/catalog/interventions.json` | Control implementations |
| `harness/PILOT-STATUS.md` | Live pilot unblock |
| `.cursor/skills/validity-*` | AI workflows |

# Adoption Guide: AI-Native PDLC Validity Framework

**How any team can apply the formula and the reference setup to their own repo.**

Canonical contract: [`framework/CONTRACT.md`](../framework/CONTRACT.md).  
CLI / schemas / skills: [`framework/README.md`](../framework/README.md).

## What you are and are not expected to do

The verifier specs in `harness/tasks/verifiers/` are **our research methodology** —
the mechanism we used to produce precise `V_obs(t)` ground truth for fitting. They
are not something Level 0 adopters need to write.

What you get from this research preview:

- The formula structure (`theory/formula.py`, version **v1.1**)
- Portable schemas + CLI to inspect, diagnose, and report
- Cursor skills that propose rules/hooks/workflows (human approval required)
- Modus as the worked reference path

What you do **not** get yet:

- Modus-fitted “factory” weights (current `data/fit_results.json` is **SYNTHETIC**)
- A Marketplace trust-gate with calibrated thresholds
- Live completion-guard effect sizes (simulation-only)

## Adoption levels (aligned with TTC abstracts)

| Level | Name | Effort | Outcome |
| --- | --- | --- | --- |
| **0** | **Observe** | hours | Provisional setup signal + measurement gaps from CI/diff/events |
| **1** | **Instrument** | about a week | Per-run records; setup profile begins to accumulate |
| **2** | **Calibrate and improve** | a sprint | Repo-specific arm contrasts / fitted weights; review-depth policy |

Level 0 is **observe**, not a scored every-PR oracle. A PR contributes evidence and
may receive a review-depth **recommendation**; precise scores wait for Level 2.

### Level 0 — Observe

```bash
python -m framework init --repo .          # writes validity.layout.json + layout rule
# edit paths if this product repo differs from the research defaults
python -m framework inspect --repo .
python -m framework evidence --repo .      # facts for AI diagnosis
python -m framework report --repo . --include-synthetic
```

Then run the **validity-diagnose** Cursor skill on the evidence pack. After you
accept the diagnosis, **validity-improve** applies approved fixes via CLI paths
and automations. Setup skill (`validity-setup`) may propose collectors/rules/hooks
but must not install them without approval, and must not replace AI diagnosis with
script heuristics.

**Signals used:** PR diff opacity, optional blast radius, CI status, declared
rules/MCP/hooks. Missing fields are labeled imputed/missing with confidence.

### Level 1 — Instrument

1. Labels: `approved`, `qa-failed`, `needs-human`, `qa-skip`, `qa-full`, `experiment-run`
2. Automations: adapt `harness/AUTOMATION-PROMPTS.md` + `harness/CONSOLE-TRIGGERS.md` (official repo; comment commands **by Me** only)
3. Collectors: `python harness/collectors.py …` → `data/metrics.jsonl`
4. Dashboard (optional): `python dashboard/server.py`

### Level 2 — Calibrate and improve

1. 5–10 tasks with verifiers (`harness/tasks/schema.md`)
2. Baseline + variance-first ablations (`bare`, `no_recovery_loop`, …)
3. `python -m framework calibrate` (blocked until ≥6 real terminal runs)
4. Diagnose layer → apply one intervention from `framework/catalog/interventions.json`
5. Remeasure; update review lanes from measured trust + task risk

## Review policy

Human review is **never removed**.

- **Deep** — major / high-risk / low measured trust
- **High-level** — trusted medium work
- **Minimal** — small low-risk work with high measured trust (still nonzero)

## Packaging status

| Artifact | Status |
| --- | --- |
| Contract, schemas, CLI, skills, templates | **research preview** |
| Level 0 observe path | **available now** |
| Level 1 collectors / Modus harness | **available now** |
| Level 2 real Modus fit (v2) | **pending live campaign** |
| Packaged GitHub Action trust gate | **deferred** until real weights |
| Phase E second-repo validation | **not run** |

See `framework/VALIDATION.md` and `harness/PILOT-STATUS.md`.

# AI-Native PDLC Validity Framework — Contract (research preview)

**Status:** research preview  
**Formula version:** v1.1 (`theory/formula.py`)  
**Evidence status:** simulation-calibrated (not Modus-fitted; not multi-repo validated)

This contract is the published boundary for what the framework measures, what a
single PR contributes, and which claims are allowed before Phase D/E data land.

## 1. Unit of analysis

| Quantity | Scope | Meaning |
| --- | --- | --- |
| `V_obs(t)` | One agent run | Verifier pass-fraction at commit checkpoints |
| Run record | One issue→PR attempt | Telemetry for decay proxies, recovery activity, stages |
| **Setup-validity profile** | Periodic, by task class | Aggregate trust in the delivery setup for low/medium/high work |
| Review-depth policy | Setup + task risk | Deep / high-level / minimal-but-nonzero human review |

A PR **contributes evidence** to the setup profile and may receive a **policy
recommendation**. It does **not** receive a precise fitted validity score until
repository-specific calibration exists (Level 2 / Phase D).

## 2. Operating model (AI reasons, CLI/automations act)

| Layer | Responsibility |
| --- | --- |
| **AI skills** (`validity-score` → `validity-diagnose` → `validity-improve`) | Post-run formula quote (`score`); metric judgments; layer diagnosis; intervention choice; review policy |
| **CLI** (`init`, `inspect`, `evidence`, `intake`, `score`, `collect`, `calibrate`, `report`) | Mechanical facts, labeled heuristics, R/D/V* formula eval (placeholder weights), apply **approved** writes |
| **Automations** (Dev/QA/Fix) | Execute the delivery path; definitions often console-only (not API-listed) |
| **Human** | Provides automation/PR intake when needed; approves **apply**; always reviews PRs |

**Number ownership:** CLI computes R, D, V* and intake keyword heuristics (with
provenance). AI owns metric assessments (evidence → metric id, severity, dominant
metric) — human optional on that judgment, required before apply. AI must not
invent fitted weights or formula equilibria without quoting `python -m framework score`.

Scripted `diagnose --heuristic` is a smoke-test hint only. Authoritative diagnosis
comes from the AI skill reading `python -m framework evidence`.

## 3. Canonical outputs

CLI / report (facts):

1. **Evidence coverage** — which proxies and factors were observed vs imputed
2. **Decay pressures** — normalized `Hc`, `O`, `Cb`, `σspec` (with confidence)
3. **Recovery controls** — enabled factors and activity signals by layer
4. **Observed outcomes** — `V_obs` / pass@1 / pass^k when available
5. **Mechanical lane hints** — V_obs thresholds only (AI may override)

AI diagnosis (reasoning):

6. **Layer diagnosis** — weak **harness**, **loop**, or **graph** owner + confidence
7. **Review policy suggestion** — deep | high-level | minimal (never zero)

Equilibrium form (fitted hypothesis, not a PR oracle):

```
V* = R / (R + D)
```

## 4. Adoption levels (aligned)

| Level | Name | What you do | What you get |
| --- | --- | --- | --- |
| **0** | Observe | Compute provisional signals from existing CI, diffs, events | Coverage gaps + directional setup signal (no factory certainty) |
| **1** | Instrument | Capture handoffs, verifiers/CI, repair attempts, review burden | Per-run records feeding a setup profile |
| **2** | Calibrate and improve | Baseline + factor-off tasks; fit weights; change setup; remeasure | Repo-specific R/D contributions and review policy |

Level 0 is **observe**, not a Marketplace trust-gate with Modus factory weights.
A drop-in PR gate is deferred until real fitted weights exist.

## 5. Claim boundaries

Allowed now:

- Structure of the recovery/decay ODE and factor registry
- Simulation structure checks (Phase B) and registered hook-ablation predictions
- Pilot instrumentation design and Modus reference path description
- Qualitative Modus false-completion lesson as motivation
- Modus console Automations loop-closure pilot (#34 → Dev preflight → #42 QA
  pass), with `intake_pseudo` / placeholder V\* directional only (not fitted)

Not allowed as empirical results until evidence lands:

- Modus-fitted / “factory” weights from `data/fit_results.json` (currently SYNTHETIC)
- Live completion-guard effect sizes (simulation-only; see `SIMULATION_ONLY_FACTORS`)
- Cross-repository constant transfer
- Calibrated review-economics (`O_A` human ground truth deferred)
- Merge-throughput gains from risk-scaled review depth

## 6. Architectural layers

| Layer | Owns | Example factors |
| --- | --- | --- |
| Harness | Tools, rules, MCP, permissions, persistence | `mcp_context`, `rules_context`, `github_mcp` |
| Loop | Implement → evidence → repair stop rules | `agentic_qa`, `fix_loop`, `ci_gate`, `completion_guard_hook` |
| Graph | Handoffs, retries, human gates, routing | label transitions, review bot, human PR gate |

## 7. Layout policy (path contract)

- Every adopter repo must have **`validity.layout.json`** (or
  `.cursor/validity.layout.json`) naming where rules, hooks, MCP, workflows,
  metrics, and optional harness/theory live.
- Create it with `python -m framework init --repo .`; agents must follow
  `.cursor/rules/validity-layout.mdc` and must not assume research-repo folders.
- Inspection reports layout source + path refs; missing layout is a measurement gap.

## 8. Version policy

- `FORMULA_VERSION` in `theory/formula.py` is authoritative.
- Changelog entries in `theory/formula-changelog.md` must match that version.
- Default decay form for analysis: **HYBRID**; multiplicative kept for comparison.
- v2 ships only when real campaign arm contrasts and AIC/BIC selection are written back.

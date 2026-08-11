# When the score drops: what should the user do?

## Short answer

1. **CLI** computes which signals moved (`delta`) and formula R/D/V* (`score`).
2. **AI** maps those signals to **generic top-level metrics**, decides which matter most, explains them, proposes **one** fix.
3. **Human** approves **apply**; retest **comparable difficulty**.
4. Repeat. New failure modes can become new controls (trial-and-error).

Metrics are **not** frontend- or backend-specific. Stack details are evidence; AI maps them to the nearest top-level metric.

**Who owns numbers:**
- CLI: `intake_heuristic_scores` (keyword hints), R/D/V* from `score` (placeholder weights)
- AI: authoritative metric assessment in `diagnosis.json` / `improvement-plan.json`
- Human: required on apply, optional on metric judgment

## Top-level metrics (only these)

| Id | Meaning |
| --- | --- |
| `V_obs` | Requirements/checks satisfied at latest checkpoint |
| `V_star` | Equilibrium trust R/(R+D) |
| `Hc` | Context thrash / error accumulation |
| `O` | Hard-to-review change opacity |
| `Cb` | Blast radius / impact reach |
| `sigma_spec` | Spec ambiguity |
| `R_recovery` | Detect+repair strength |
| `pass_at_1` | Correct on first delivery |

Definitions, signals, mapping examples, control classes: `catalog/metric-playbooks.json`.

## Flow

```bash
python -m framework delta --before data/round-good.json --after data/round-failed.json
python -m framework score --input data/user-intake.json   # CLI-owned R/D/V*
# Cursor skill: validity-improve-from-delta
```

AI must:

1. Map evidence → nearest metric (cite snippet)  
2. Teach what that metric means in this workflow  
3. Suggest one raise-R or lower-D change  
4. Retest plan  

## Trial-and-error → new controls

If no control class fits a repeated failure, log a candidate, try one change, keep only if the next delta improves the mapped metric.

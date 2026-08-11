# Top-level metrics (any workflow) — measure and improve

These metrics are **domain-agnostic**. Frontend, backend, data, infra, or mixed
workflows all map evidence onto the same set. AI chooses the nearest metric.

Full playbooks + mapping rules: [`catalog/metric-playbooks.json`](catalog/metric-playbooks.json).  
Score-drop loop: [`IMPROVE-LOOP.md`](IMPROVE-LOOP.md).

## Top-level set

| Id | Means | Typical evidence (any stack) |
| --- | --- | --- |
| `V_obs` | Requirements/checks satisfied now | AC, tests, policy gates, human reject |
| `V_star` | Equilibrium trust R/(R+D) | Chronic rework despite “busy” agents |
| `Hc` | Context thrash / error accumulation | Failed tool loops, transcript thrash |
| `O` | Hard-to-review change opacity | Huge/sprawling deliverables |
| `Cb` | Blast radius | Shared module, public contract, prod path |
| `sigma_spec` | Spec ambiguity | Vague ticket, missing acceptance |
| `R_recovery` | Detect+repair strength | No gate/repair; false completion |
| `pass_at_1` | Correct on first delivery | Success only after repair/human poke |

## How telemetry maps (when you have it)

| Proxy / signal | Metric |
| --- | --- |
| entropy_proxy / thrash notes | `Hc` |
| opacity_proxy / change size | `O` |
| dependency/impact reach | `Cb` |
| raw vs refined spec | `sigma_spec` |
| gates/QA/repair/hooks that fired | `R_recovery` |
| check pass fraction | `V_obs` |

Missing telemetry: AI still maps **qualitative** failure notes to the nearest metric.

## When a round is worse

```bash
python -m framework delta --before data/round-good.json --after data/round-failed.json
# skill: validity-improve-from-delta  → map → explain → one fix
```

Claim boundaries: `framework/CONTRACT.md`.

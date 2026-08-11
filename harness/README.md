# Harness

The experiment driver and telemetry collectors around the existing Cursor
Automations pipeline. The pipeline does the work; this code seeds it, watches it,
and grades it.

```
driver.py            seed issue -> /approve -> await terminal state -> snapshot/cleanup
collectors.py        artifacts -> per-commit V_obs + proxies + stage transitions
factors/registry.py  operational factor definitions + named experiment arms
tasks/               task suite (JSON specs + verifier specs)
RETARGET-RUNBOOK.md  one-time console steps to point the automations at the fork
```

## Requirements

- `gh` CLI authenticated with access to `ElishaSamPeterPrabhu/modus-wc-2.0` (verified).
- Local fork checkout at `/Users/eprabhu/Desktop/Projects/mine/modus-wc-2.0`
  with `npm install` done (verified) — used for diff stats and verifier grading.
- The automations retargeted per `RETARGET-RUNBOOK.md` (console-side, manual).

## Typical usage

```bash
# pilot: one task, baseline arm, 2 repeats
python harness/driver.py --arm baseline --task low-card-hover --repeats 2

# collect + grade after runs finish
python harness/collectors.py data/runs/baseline__low-card-hover__r1 ...

# ablation arm
python harness/driver.py --arm no_mcp --task all --repeats 3
```

## Telemetry coverage vs the plan

| Proxy | Source | Status |
| --- | --- | --- |
| V_obs(t) | verifier at every PR commit | implemented (`grade_commits`) |
| O(t) opacity | git diff stats per commit | implemented |
| C blast radius | madge reverse-dependency reach (fallback heuristic) | implemented |
| ρ checkpointing | commit timestamps (cadence) | implemented (in checkpoints) |
| stage transitions, fix iterations | issue/PR label timelines | implemented |
| H_c entropy | tokens + tool-failure rate from cloud run logs | **partial**: needs read-only Cloud Agents API access (`CURSOR_API_KEY`); until wired, H_c is imputed from run duration + fix iterations |
| σ_spec plan variance | embedding variance of 3 generated plans | **deferred**: requires LLM+embedding calls per issue; v1 uses the spec:raw/spec:refined arm assignment as the (causal) ambiguity variable, which is stronger than the proxy anyway |

Both partial items are additive: they extend `collectors.py` without changing
records already collected.

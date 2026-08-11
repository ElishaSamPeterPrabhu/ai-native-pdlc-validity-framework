# Research Preview — AI-Native PDLC Validity Framework

**Version:** framework `0.1.0` · formula `v1.1`  
**Evidence:** simulation-calibrated (live Modus campaign and Phase E pending)

Install: `pip install pdlc-validity`  
Repository: https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework

## Publish contents

| Path | Contents |
| --- | --- |
| [`framework/`](framework/) | Contract, schemas, CLI, adapters, intervention catalog, templates |
| [`.cursor/skills/validity-*`](.cursor/skills/) | Setup, calibrate, and improve Cursor skills |
| [`theory/formula.py`](theory/formula.py) | Canonical ODE + factor registry |
| [`research/adoption-guide.md`](research/adoption-guide.md) | Level 0–2 adoption (Observe → Instrument → Calibrate) |
| [`framework/VALIDATION.md`](framework/VALIDATION.md) | Pilot / campaign / Phase E success criteria |

## Start here

```bash
python -m framework init --repo .     # validity.layout.json + layout rule
python -m framework inspect --repo .
python -m framework validate --repo . --out data/validation
```

Read [`framework/CONTRACT.md`](framework/CONTRACT.md) before citing results. Do not treat
`data/fit_results.json` as factory calibration (it is marked SYNTHETIC).

## Novelty claim (narrow)

To our knowledge, the combination of a fitted recovery/decay trust model, factor
valuation by ablation, harness/loop/graph diagnosis, and risk-scaled human review
policy for AI-native software delivery is the contribution. Individual ingredients
(harness engineering, evidence gates, review routing) exist elsewhere.

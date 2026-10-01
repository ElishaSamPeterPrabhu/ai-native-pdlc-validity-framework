# Workflow-builder skill evals

Tests whether the `workflow-*` skills rebuild the setups we already run, from a
repo with those setups hidden. Pass criteria are pre-registered in
[`criteria.json`](criteria.json); do not loosen them after seeing results.

| Layer | What | Needs |
| --- | --- | --- |
| L0 | `test_contract.py`: skill frontmatter, kit mirrors, signal contract vs label router, placeholders, schemas, scorer self-test | nothing (runs in CI) |
| L1 | `run_eval.py` + `score.py`: golden retrodiction, `skills` vs `bare` arm, k=3 | `CURSOR_API_KEY`, `pip install -e '.[evals]'`, local `modus-wc-2.0` clone |
| L2 | live shadow runs on official PRs / copied pilot sheet | not built yet |

## Scenarios

| id | Target | Hidden ground truth |
| --- | --- | --- |
| `eng-modus` | trimble-oss/modus-wc-2.0 @ `97128dc` | Dev/QA automations, label router, hooks, agents |
| `prod-ticket` | fork pilot branch @ `a9d5248` | `automation.mdc`, agents, pilot label router |
| `generic-ctrl` | this repo @ `15c2ab0` | starter kit and `workflow-*` skills (control, not gated) |

Each has `setup.json` (pinned SHA, held-out paths), `persona.json` (scripted team
answers), and `expected.json` (checks; `critical` ones decide success, `safety`
failures are counted separately). `fixtures/*/golden` are hand-built passing runs
the scorer self-test mutates into failures.

## Run

```bash
pip install -e '.[evals]'
export CURSOR_API_KEY=...            # MODUS_WC_REPO defaults to ../modus-wc-2.0
python -m unittest discover -s harness/skill-evals -p "test_*.py"
python harness/skill-evals/run_eval.py --smoke      # 1 run, check wiring
python harness/skill-evals/run_eval.py              # 3 scenarios x 2 arms x k=3
python harness/skill-evals/score.py                 # data/skill-evals/results.json + report.md
```

Model defaults to `composer-2.5` (`--model` to override). Agents load
`setting_sources=["project"]` only, so personal rules and skills do not leak
into either arm. The `prod-ticket` ref must exist locally: `git fetch fork`.

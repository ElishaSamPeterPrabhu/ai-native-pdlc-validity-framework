---
name: validity-score
description: >-
  After a Dev/QA/Fix, /ask, or /refine automation run, invoke pdlc-validity
  (or local python -m framework) to emit score-pack R/D/V* standings. Use when
  the user asks where the setup stands, after an automation finishes, or before
  validity-diagnose.
---

# Validity Score (post-automation formula)

## Goal

Run the CLI formula after an automation so the human sees **where we stand**.
CLI owns R, D, V*. You only present those numbers and a short comparison table.

## When to run

- A Dev, QA, Fix, `/ask`, or `/refine` run just finished
- The user asks “where do we stand” / “run the formula”
- Before handing off to **validity-diagnose**

## Repo

`--repo` is the **official** Modus checkout: [trimble-oss/modus-wc-2.0](https://github.com/trimble-oss/modus-wc-2.0).
Do not score the ElishaSamPeterPrabhu experiment fork unless the human asks for historical pilot packs.

## CLI command

Prefer the PyPI entrypoint. Do **not** `pip install` into the product repo.

```bash
REPO="<official-modus-wc-2.0-checkout>"

if command -v pdlc-validity >/dev/null 2>&1; then
  CLI="pdlc-validity"
elif [ -n "$VALIDITY_VENV" ] && [ -x "$VALIDITY_VENV/bin/python" ]; then
  CLI="$VALIDITY_VENV/bin/python -m framework"
else
  CLI="python -m framework"
fi

# Layout first
$CLI init --repo "$REPO"
$CLI inspect --repo "$REPO"

# After a PR/issue run: keep intake current, then score
$CLI intake --repo "$REPO" --intake "$REPO/data/user-intake.json" --out "$REPO/data/evidence-pack.json"
$CLI score --repo "$REPO" --input "$REPO/data/user-intake.json" --out "$REPO/data/score-pack.json"

# Optional vs last snapshot
# $CLI delta --repo "$REPO" --before "$REPO/data/user-intake-round34.json" --after "$REPO/data/user-intake.json" --out "$REPO/data/delta-pack.json"
```

If `pdlc-validity` is missing, use this research repo’s `.venv`:

```bash
cd "<research-repo>" && source .venv/bin/activate
python -m framework score --repo "$REPO" --input "$REPO/data/user-intake.json" --out "$REPO/data/score-pack.json"
```

## Steps

1. Read `validity.layout.json` under `--repo` (create via `init` if missing). Use only those paths for intake, score pack, and metrics.
2. If the latest PR/issue is not in `user-intake.json`, append a PR row from GitHub facts (`gh pr view`, reviews, labels). Record `needs-human`, `/ask`, `/refine`, and `## NOT FEASIBLE` under `formula_signals.recovery_seen` when they happened. Do not invent `M(t)` / `human_alignment` scores (formula v1 leaves them unused).
3. Run `intake` then `score` as above.
4. Quote **only** `data/score-pack.json` (or layout `data_dir`) for R, D, V*.
5. **Provenance disclosure (mandatory, before any standing):** for each scored
   record, read `decay_proxies.*.source`, `defaulted_inputs`,
   `missing_inputs`, and `activities_assumed`/`recovery_assumed`, then state
   which inputs were `observed` (measured), `heuristic` (keyword rules on
   notes), `imputed` (policy defaults), or `missing`. The CLI prints the same
   disclosure lines on stdout — repeat them, do not paraphrase them away.
6. If a record's V* is missing (`source=missing`), say exactly: "The framework
   does not have the necessary data to compute this; the gap is <missing
   inputs>." Never substitute an estimate.
7. Present a standings table: this PR vs prior PR in the same intake, plus aggregate V* if present.
8. Label every number: `weight_source` from the pack (usually `placeholder`); `record_kind=intake_pseudo`; `n_runs` = line count of layout `metrics_path` (0 until collectors).
9. Stop. Do **not** diagnose harness/loop/graph — that is **validity-diagnose**.

## Hard rules

- Never invent R, D, V*, or fitted weights.
- Never invent factor activity or decay proxy values; a factor not present in
  `recovery_seen` or telemetry contributes zero to R.
- Never present a defaulted or heuristic input as measured; disclose per-field
  `source` before citing any standing (see `.cursor/rules/factor-provenance.mdc`).
- Never treat `delta-pack` `intake_heuristic_scores` as formula output.
- Human review is never removed.
- `completion_guard_hook` stays simulation-only until live telemetry exists.
- Do not run `calibrate` from this skill.

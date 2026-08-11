# Modus Validity Pilot — Results

**Repo:** https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0  
**Upstream:** https://github.com/trimble-oss/modus-wc-2.0  
**Pilot branch:** `framework-test`  
**Formula:** v1.1 · `weight_source=placeholder` · `record_kind=intake_pseudo`  
**Score pack generated:** 2026-08-07T09:19:29Z  
**n_scored:** 2 · **metrics.jsonl runs:** 0

---

## Setup

### Automations (Cursor Cloud, Trimble console)

| Agent | ID | Trigger | Stop rule |
|-------|-----|---------|-----------|
| Dev Agent | `69f213ff-4748-4bed-a065-9ba8b97d6bfe` | `/approve` on issue in modus-wc-2.0 | PRE-OPEN PR GATE (QA STEP 1) before Open PR; `qa-skip` or `qa-full` |
| QA Agent | `aac94e20-8523-48e4-a239-26daa40f1675` | PR opened by Anyone; label `qa-full`; label `qa-rerun` added | `## QA PASSED` or `## QA FAILED`; `qa-failed` on fail |
| Fix Agent | `915ae382-a9d0-4d76-9742-3e6121108a3b` | `qa-failed` on PR | Read `## QA REPORT` or `## QA FAILED`; local verify; remove then add `qa-rerun`; repair cap 3 |

QA Agent GitHub connection: connected.

### Controls applied during the pilot

| Control | Target |
|---------|--------|
| `dev_preflight_stop_boundary` | Dev Agent — QA STEP 1 before Open PR; stop-boundary in PR body |
| `fix_agent_qa_header_alignment` | Fix Agent — accepts `## QA FAILED` / `## QA REPORT` |
| `fix_agent_qa_rerun_toggle` | Fix Agent — remove `qa-rerun` if present, then add |
| `qa_agent_github_connect` | QA Agent GitHub tools/triggers |
| `qa_agent_qa_full_trigger` | QA Agent — `qa-full` label trigger |
| `completion_guard_hook` | `.cursor/hooks.json` (simulation-only) |

### Diagnosis

- Weakest layer: **loop**
- Confidence: high
- Loop status (after retest): `closed_qa_passed`

---

## Round 1 — Baseline (pre-intervention)

**PR:** [#34](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/34) — feat(menu-item): add end-icon slot support  
**Issue:** [#30](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/30)  
**Branch:** `exp/30-menu-item-end-icon`  
**Stratum:** medium  
**Opened:** 2026-07-20 · **Last update:** 2026-07-23  
**State (as of 2026-08-10):** open, not merged, mergeable_state `unstable`  
**Labels:** `qa-full`, `experiment-run`, `task:medium`

### Diff

| Metric | Value |
|--------|-------|
| Files changed | 16 |
| Lines changed | 594 |
| Commits | 12 |

### Loop events

| Stage | Result |
|-------|--------|
| Dev stop-boundary in PR body | No |
| Dev pre-flight before Open PR | No |
| agent_claimed_done | true |
| QA | `## QA FAILED` (2026-07-20) |
| Fix iterations | 0 |
| QA round 2 | None |

### QA failure detail (PR #34)

| Check | Result |
|-------|--------|
| `npm run tailwind:build` | Missing script |
| `npm run embed:css` | Missing script |
| `npm run embed:component-css` | Missing script |
| `npm test` | Pass (55 suites, 1642 tests) |
| `npm run lint` | Fail (2 files not in PR diff) |

### CI (head checks)

| Check | Conclusion |
|-------|------------|
| Node 20 tests | success |
| playwright-e2e (chromium/firefox/webkit) | success |
| a11y-check | success |
| spellcheck | success |
| visual-regression | success |
| merge-gate | failure |
| build-and-deploy (Blazor Story) | failure |
| qa-approval | skipped |

### Formula scores (score-pack)

| | Value |
|--|-------|
| R | 0.20 |
| D | 0.1562 |
| V* | 0.5615 |

`recovery_seen`: ci_gate, agentic_qa

---

## Interventions (between rounds)

1. Appended Dev Agent PRE-OPEN PR GATE (run QA STEP 1 commands; put Stop-boundary check in PR body).
2. Updated Fix Agent to accept `## QA FAILED` as well as `## QA REPORT`.
3. Connected QA Agent GitHub; set PR-open trigger to Anyone; added `qa-full` and `qa-rerun` label triggers.
4. Installed `.cursor/hooks.json` completion-guard template.
5. After PR #42 round-2 miss: updated Fix Agent to remove-then-add `qa-rerun` (GitHub fires on label-added only).

---

## Round 2 — Retest (post-intervention)

**PR:** [#42](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/pull/42) — fix(checkbox,switch): update internal value on input change  
**Issue:** [#28](https://github.com/ElishaSamPeterPrabhu/modus-wc-2.0/issues/28)  
**Branch:** `exp/28-checkbox-switch-value`  
**Stratum:** medium  
**Opened:** 2026-08-05  
**Labels (final):** `qa-full`  
**State:** open · mergeable · mergeStateStatus `UNSTABLE`

### Diff (final, after Fix)

| Metric | Value |
|--------|-------|
| Files changed | 16 |
| Additions | 169 |
| Deletions | 43 |
| Lines changed | 212 |
| Commits | 5 (4 Dev + 1 Fix) |
| Files at first open (before Fix) | 5 |

### Loop timeline (UTC, 2026-08-05)

| Time | Event |
|------|-------|
| 09:30 | Dev commits + PR open; Stop-boundary check: **yes** (command table in body) |
| 09:34 | Label `qa-full` added |
| 09:55 | Label `qa-rerun` added (manual kick for first QA) |
| 10:00 | QA round 1: `## QA FAILED` — `npm run lint` (11 Prettier files); label `qa-failed` added |
| 10:03 | Fix Agent: commit `b404802` (Prettier + table generic); removes `qa-failed`; comments fix applied |
| 10:03–10:16 | No QA round 2 — `qa-rerun` already present; no new label-added event |
| 10:16–10:17 | Manual remove + re-add `qa-rerun` |
| 10:17–10:20 | QA Agent run `bc-8cd16c11-18cb-4d99-9148-30f45b2a124a` |
| 10:20 | QA round 2: `## QA PASSED` — all checks passed; `qa-rerun` removed |

### Dev stop-boundary table (from PR body)

| Command | Result |
|---------|--------|
| `npx tailwindcss -i …` | Pass |
| `node scripts/embed-css.js && node scripts/generate-variables-css.js` | Pass |
| `node scripts/embed-component-css.js` | Pass |
| `npm test` | Pass (55 suites, 1643 tests) |
| `npm run lint` | Pre-existing failures noted on main; changed files eslint OK |

### Loop outcome

| Stage | Result |
|-------|--------|
| Dev stop-boundary | Yes |
| Dev pre-flight before Open PR | Yes |
| QA rounds | 2 |
| QA round 1 | FAILED (lint) |
| Fix iterations | 1 |
| QA round 2 | PASSED |
| Manual `qa-rerun` toggle for round 2 | Yes |
| Final QA outcome | passed |
| agent_claimed_done | true |

### CI (after Fix)

| Check | Conclusion |
|-------|------------|
| Node 20 tests | success |
| playwright-e2e (all browsers) | success |
| a11y, spellcheck, visual-regression | success |
| merge-gate | success |
| Cursor Automation: QA Agent | success |
| build-and-deploy (Publish Blazor Story) | failure |
| Publish Storybook / qa-approval | skipped |

### Formula scores (score-pack)

| | Value |
|--|-------|
| R | 0.30 |
| D | 0.1066 |
| V* | 0.7377 |

`recovery_seen`: ci_gate, agentic_qa, fix_loop

---

## Score comparison

| | PR #34 | PR #42 | Δ |
|--|--------|--------|---|
| R | 0.20 | 0.30 | +0.10 |
| D | 0.1562 | 0.1066 | −0.0496 |
| V* | 0.5615 | 0.7377 | +0.1762 |

**Aggregate V\*** (mean of both): **0.6496**

Command:

```bash
python -m framework score --repo <modus> --input data/user-intake.json --out data/score-pack.json
```

---

## Delta pack notes (intake heuristic, not formula)

From `delta-pack.json` (before = round34 snapshot, after = full intake):

| Metric | Before | After | Δ |
|--------|--------|-------|---|
| Hc | 0.0 | 0.4 | +0.4 |
| Cb | 0.0 | 0.35 | +0.35 |
| O | 0.6 | 0.6 | 0 |
| R_recovery (heuristic) | 0.3 | 0.3 | 0 |
| pass_at_1 (heuristic) | 0.0 | 0.0 | 0 |

Dominant worsened heuristic metric: **Hc** (Fix lint sweep expanded PR #42 from 5 → 16 files).

---

## Observed facts (summary)

1. Without Dev PRE-OPEN PR GATE, medium PR #34 opened “done,” QA failed on missing npm scripts, Fix never ran (`fix_iterations=0`).
2. With gate + QA/Fix wiring, medium PR #42 showed stop-boundary evidence, QA failed once on lint, Fix ran once, QA passed on round 2.
3. Round 2 on #42 did not fire until `qa-rerun` was removed and re-added (label already present since 09:55).
4. Placeholder formula scores: R 0.20→0.30, D 0.1562→0.1066, V* 0.5615→0.7377; aggregate V* 0.6496.
5. Blazor Story `build-and-deploy` failed on both PRs’ check sets checked; core unit/e2e checks passed on #42 after Fix.
6. `metrics.jsonl` has 0 runs; scores are intake_pseudo with placeholder weights.

---

## Artifact paths (fork `framework-test`)

- `data/user-intake.json`
- `data/score-pack.json`
- `data/delta-pack.json`
- `data/evidence-pack.json`
- `data/diagnosis.json`
- `data/improvement-plan.json`
- `data/validity-analysis.md`
- `data/validity-report.json`
- `data/setup-manifest.json`
- `validity.layout.json`
- `.cursor/hooks.json`

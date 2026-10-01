# L2 engineering: generated automations vs official console config

Compared: `data/skill-evals/runs-v4/eng-modus__skills__r{1,2,3}/workspace/data/automations/`
against `harness/console-paste/*`, `harness/AUTOMATION-PROMPTS.md`, `harness/CONSOLE-TRIGGERS.md`.
Method: string counts across files (not semantic review). Counts below are occurrences.

## Caveats

- The three PRs (#1544, #1562, #1565) are human-authored. Their only agent-like signal is a human "Moving to QA" handoff, plus Copilot review. No `Routing:` block and no `## QA` verdict exists on any of them. This validates the intake/score path on real PRs. It does not show that generated Dev/QA agents work live.
- Console automations are not API-readable. The "live" side is the documented config in this repo, not the console itself.
- Generated files were produced from a replayed interview persona, not a real session.

## Matches (all 3 runs)

| Control | Generated | Live |
|---|---|---|
| Comment triggers Me-only, never Anyone | yes (all runs, dev/ask-refine) | yes |
| QA triggered by label added, not PR opened | yes (qa.md in all runs) | yes |
| `Routing:` block in Dev output | yes (5-11 mentions) | yes |
| `qa-rerun` handling | yes | yes |
| NOT FEASIBLE / NEED CLARIFICATION outcomes | yes | yes |
| `needs-human` escalation and iteration cap | yes (cap mentioned in all runs) | yes |
| Fix agent inactive | r1, r2 fold fixing into Dev; r3 emits a fix.md | live: Fix inactive |

## Gaps (generated config lacks what live has)

| Live feature | Live count | Generated (r1/r2/r3) |
|---|---|---|
| Routing fields `QA-depth`, `QA-scope`, `QA-themes`, `QA-assert`, `QA-graph` | 15 / 19 for depth / graph | 0 / 0 / 0 |
| Label auth through gh API with `GITHUB_AUTH_TOKEN` / `OPERATOR_GH_TOKEN` | 4 | 0 / 0 / 0 |
| `gh label create` bootstrap | 5 | 0 / 0 / 0 |
| Playwright-based visual/computed-style QA | 12 | 0 / 0 / 0 |
| `/clarify` command | 7 | 0 / 0 / 0 |
| `getComputedStyle` assertions | n/a | 0 / 0 / 0 |

## Reading

- The generic contract (triggers, safety, routing, escalation) is reproduced. This is what the L1 scorer checks, and it passes.
- Repo-specific depth is not reproduced: the QA routing schema, label-auth workaround, and Playwright steps. These come from months of operating the official setup, not from the interview. They are expected gaps, not skill bugs.
- Possible follow-up for `workflow-setup-cursor`: when the repo profile shows Storybook/Playwright and a label-driven QA, emit an optional "QA routing fields" section and a label-auth note (a label added by the default Cursor token does not retrigger other automations). This should be a skill change only if the user wants it. The L1 criteria are not affected.
- Hooks and agents are hidden in the replay (writes outside `data/automations/` are not captured in the eval workspace), so hook/agent parity was not assessed.

## Scores (from CLI, see `score-pack.json`)

Provenance, before any standing:

- record_kind: `intake_pseudo` for all three. weight_source: `placeholder`.
- observed: opacity (from lines/files changed), and the CI and review-bot recovery activities that I supplied from the PR checks.
- heuristic: spec_ambiguity (0.5, "no acceptance criteria provided"), plus R, D and V* themselves.
- imputed: entropy (0.5), blast_radius (0.2). No telemetry, policy default.
- missing: none flagged by the CLI. Fix agent not declared, which is a recorded gap.

| PR | R | D | V* (directional) |
|---|---|---|---|
| #1544 | 0.2 | 0.0875 | 0.6956 |
| #1562 | 0.2 | 0.0803 | 0.7136 |
| #1565 | 0.2 | 0.0778 | 0.7199 |
| aggregate | | | 0.7097 |

V* is directional only: low confidence, placeholder weights, two of four decay inputs imputed. Not a claim that the setup is 71% valid. Differences between PRs mostly reflect size (opacity). #1565 scores highest although Copilot flagged an unimplemented requirement, so the score does not capture that failure. That is a limit of intake scoring.

## Measurement gaps

- Monitor registration: `dashboard/monitor` does not exist yet, so not done.
- No live telemetry for entropy or blast_radius.
- No Dev/QA agent runs on these PRs, so agentic_qa, fix_loop and spec_refinement stay unobserved.

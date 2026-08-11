# Pipeline Scan: ticket → dev → QA → review (July 2026)

Two jobs: (1) position the in-house label-handoff pipeline against what exists,
(2) shortlist add-on tools per stage as factor-registry candidates. Selection
criteria: headless/API-triggerable, works on a GitHub fork, free or cheap tier.

## 0. What the fork already has (inspected 2026-07-19)

`ElishaSamPeterPrabhu/modus-wc-2.0` (local: `/Users/eprabhu/Desktop/Projects/mine/modus-wc-2.0`):

- Tests: Stencil/Jest spec tests (`npm test`, `test:coverage`).
- Storybook 8.6 with `@storybook/addon-a11y` and `@storybook/test` already installed;
  `.storybook/a11yConfig.js` present. No Vitest addon (SB8-era test-runner path).
- CI workflows already present: `lint.yml`, `a11y-check.yml`, `qa-approval.yml`
  (environment-gated approval), `merge-gate.yml`, `copilot-pr-review.yml`, sonar,
  spellcheck. The QA/merge gating skeleton exists — factors toggle these.
- `.cursor/rules/code-guidelines.mdc` present (the rules_context factor toggle).
- `mcp/` directory: present upstream, NOT in the fork's current main → the fork needs
  an upstream sync before the MCP ablation (testbed todo).
- Last sync: merge commit "Merge upstream/main into fork" on current main.

## 1. Ticket/spec stage

| Option | Status | Notes |
| --- | --- | --- |
| **In-house Issue Scaffolding automation** (adopted) | Running | Webhook → structured issue with acceptance criteria + `approved`/`needs-review` labels. Matches the Atlassian spec-driven pattern (issue = durable, machine-readable contract). This toggle IS the σ_spec manipulation. |
| Specship | reference only | Commercial ticket-to-PR: acceptance criteria → failing tests → PR. Cite as convergent design; no need to adopt. |
| Augment "Cosmos" intake | reference only | Task intake → scoped spec → plan posted on ticket. Same pattern at enterprise scale. |

**Factor:** `spec_refinement` (Issue Scaffolding on/off). Already in registry.

## 2. Dev stage

| Option | Status | Notes |
| --- | --- | --- |
| **In-house Dev Agent** (adopted) | Running | `/approve` trigger, Composer 2.5, self-provisions architecture.mdc. |
| Modus MCP server (`mcp/` upstream) | adopt as factor | The flagship "necessary MCP" ablation. Requires fork sync first. |
| `.cursor/rules` | adopt as factor | Present in fork; toggle = file present/removed. |
| Commit-cadence instruction | adopt as factor | Prompt-level toggle; Sobol ranked cadence (`steps_per_commit`) the single highest-leverage parameter on High tasks — promote this ablation arm. |

## 3. QA stage

| Option | Status | Notes |
| --- | --- | --- |
| **In-house QA Agent** (adopted) | Running | Agentic QA with skip-logic; the `agentic_qa` factor. |
| **Stencil/Jest spec tests via CI** (adopted) | In fork | The deterministic `ci_gate` factor — cheapest to toggle (branch-protection required check on/off). |
| Storybook a11y (axe-core) | adopt (second gate) | `a11y-check.yml` already exists; blocking vs non-blocking is a clean sub-toggle. |
| Storybook interaction tests (`@storybook/test` play functions) | adopt for verifiers | Not a factor: verifier building material. Verifiers = Jest spec + SB interaction + a11y assertions per task. |
| Chromatic visual regression | shortlisted, deferred | Free OSS tier; needs baseline management per reset-branch, which fights the harness's reset-per-run design. Revisit after pilot. OSS fallbacks: Lost Pixel, BackstopJS. |
| Playwright/browser-use agentic QA vs built Storybook | experimental, deferred | "Agentic-QA vs deterministic-gate" comparison is interesting but not v1. |

## 4. Review stage (pipeline's thinnest coverage — one bot gets adopted)

| Option | Status | Notes |
| --- | --- | --- |
| **Cursor Bugbot** (adopt as the `review_bot` factor) | shortlisted #1 | Native to the existing Cursor stack (same org billing, no new vendor onboarding); benchmarked mid-pack-to-strong (F1 49–80.5% depending on benchmark), lower noise than high-recall tools. Toggle: enable/disable on the fork. |
| CodeRabbit | fallback | Free OSS tier, cleanest signal-to-noise in independent tests (44% catch, 2 FPs), diff-only. Use if Bugbot enablement on a personal fork is blocked. |
| Greptile | fallback | Full-repo indexing, highest vendor-claimed catch (82%, drops to 45% independently); free tier since June 2026; noisier. |
| GitHub `copilot-pr-review.yml` | already in fork | Confound alert: this workflow already reviews PRs — it must be OFF in all arms except an explicit review-bot arm, or it contaminates the baseline. |

Published-benchmark disagreement (44–82% same-tool spread) is the argument for our
neutral, formula-grounded ablation. See research/related-work.md §1.

## 5. Merge gate

In-house trust gate (dashboard phase) — consumes `V_delivered`, posts verdict as PR
comment/check. `qa-approval.yml` + `merge-gate.yml` in the fork are the mounting points.

## 6. Decisions

1. Registry v1 factor→mechanism mapping confirmed; no new external tool is required
   to start the campaign except the review bot (Bugbot first choice).
2. Fork must be synced with upstream to obtain `mcp/` before the MCP arm.
3. `copilot-pr-review.yml` disabled by default (baseline contamination).
4. Chromatic and agentic-browser-QA deferred to post-pilot.
5. Promote the commit-cadence ablation arm (Sobol top rank) into the pilot.

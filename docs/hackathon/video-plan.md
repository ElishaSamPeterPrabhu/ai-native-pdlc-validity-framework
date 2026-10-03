# Hackathon video: Script A (5 minutes)

**Working title:** Trust AI code by design.

**Format:** 1920x1080, screen recording plus voiceover. Dark theme, editor font 18pt or larger. No Marvel names, logos or clips.

**Companion:** [`video-script-vee.md`](video-script-vee.md) is Script B, the same five phases and timestamps narrated by the mascot Vee. Use one script or the other for the audio.

## Tag legend

| Tag | Meaning |
| --- | --- |
| `REC-*` | Screen video, saved to `docs/hackathon/video/raw/` |
| `SHOT-*` | Still screenshot, saved to `raw/` |
| `CARD-*` | Title or text card, built later in the production plan |
| `MON-*` | Timeline Monitor capture. Blocked on the monitor agent, each has a fallback |

## Honesty rules

- Every spoken number traces to a committed file or a linked public source.
- V* values are directional: `weight_source=placeholder`, `record_kind=intake_pseudo`.
- Skill-eval numbers come from a replayed persona, n=3 per arm.
- External studies (Faros, Stack Overflow, METR, DORA, GitClear) are quoted as published, shown apart from our own numbers. Say "associated with" for Faros and DORA.
- Show your own GitHub account, blur or crop the teammate's handle and avatar.
- Nothing on screen may show tokens, emails or private repo names.

## The formula, in one breath

Trust is a balance. Recovery R is what your setup does to catch and fix mistakes: rules, hooks, CI gates, QA and Fix agents, review bots. Decay D is what erodes trust as work runs: context drift, vague specs, hard-to-review diffs, wide blast radius. Validity V* = R / (R + D).

The toolkit (`starter-kit/` plus the `workflow-*` skills) builds the setup. The formula measures it.

---

## Phase 1: The speed revolution (0:00-0:40)

**Say**
> Not long ago, a feature meant days of typing. Today an agent reads an approved ticket and opens a pull request in minutes. Writing code is close to free.

**Show**
- `CARD-01`: split timeline, "days" next to "minutes".
- `REC-01`: an official PR timeline from branch to PR, 10-15 s, sped up. Source: [#1457](https://github.com/trimble-oss/modus-wc-2.0/pull/1457), the Conversation tab top.

**Dashboard:** none.

## Phase 2: The trust and review bottleneck (0:40-1:40)

**Say**
> But every one of those pull requests still lands on one person. Reviewing AI code blind is a heavy cognitive load, and the data says so. Teams that adopt AI heavily merge far more pull requests, and review time goes up with it. The code that is almost right is the hardest to catch. So the answer is not to review harder. It is to trust AI code by design: hooks, rules, skills and continuous validation that do the checking, so a reviewer looks at evidence instead of re-deriving the code.

**Show**
- `REC-02`: the official PR list, filter `is:pr state:closed author:cursor[bot]`, then scroll a long thread and a large diff. Source: [#1417](https://github.com/trimble-oss/modus-wc-2.0/pull/1417) (+533/-40, 19 files, 25+ comments) and [#1481](https://github.com/trimble-oss/modus-wc-2.0/pull/1481).
- `REC-03`: `dashboard/demo-story` build, the ball moving through the delivery nodes and stalling.
- `CARD-02`: the four trust killers: context drift, spec ambiguity, blast radius, review overhead.
- `CARD-02a-e`: stat cards, one per study (below), each with its source in small text.
- `SHOT-01`: a PR showing its QA evidence (the Routing comment and the QA review) next to the bare PR list.

**Dashboard:** none. The story app is the visual.

### Stat cards (use three or four)

| Card | Number | Say | Source |
| --- | --- | --- | --- |
| 02a | PRs merged +98%, review time +91%, PR size +154%, bugs per developer +9% | "The bottleneck moved from writing to reviewing." | [Faros AI Engineering Report 2025](https://www.faros.ai/blog/ai-software-engineering), about 10,000 developers |
| 02b | 66% say "almost right, but not quite" is their top frustration. 33% trust AI output, 46% distrust it | "Plausible code is harder to review than broken code." | [Stack Overflow 2025](https://survey.stackoverflow.co/2025/ai/) |
| 02c | 19% slower with AI, while believing 20% faster | "Feeling faster is not being faster." On screen: early-2025 tools, 2026 follow-up is mixed | [METR 2025](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) |
| 02d | Every 25% more AI adoption is associated with 7.2% lower delivery stability | "The fundamentals matter more with AI, not less." | [DORA 2024](https://dora.dev/research/2024/dora-report/) |
| 02e | Copy-pasted lines 8.3% to 12.3%, refactored lines 24.1% to 9.5% | "Reviewers catch duplication the agent cannot see." | [GitClear 2025](https://www.gitclear.com/ai_assistant_code_quality_2025_research) |

**Bridge to Phase 3 (say):** "Each of these problems is a decay term we can measure, and each fix is a recovery factor."
- Bigger PRs: opacity and blast radius.
- Almost-right code and vague specs: spec ambiguity.
- Long agent runs: context drift.
- Missing gates: weak recovery.

## Phase 3: The toolkit and the formula (1:40-3:05), main demo

**Say**
> Here is the toolkit. Drop the starter kit into a repo and ask for the workflow builder. It reads the code, asks how your team works, and writes the rules, hooks and automations. Then the formula scores that setup: recovery against decay, validity as the balance. It points at the weakest layer, you fix that layer, and you run it again. Build, monitor, measure, improve.

**Show, in order**
1. `CARD-03`: loop diagram, Build, Monitor, Measure, Improve, with badges "CLI owns the facts", "AI skills reason", "Humans approve".
2. `REC-04`: Cursor chat on a sample repo, "use workflow-builder". Discover summarizes the stack, interview asks two questions, design shows the flow, setup writes Dev, QA and Fix files. About 40 s, sped up. **Recorded by you** (Cursor app).
3. `MON-01`: **dashboard**, monitor wall with the lifeline approve, Dev, PR, QA FAILED, Fix, QA PASSED. Fallback `REC-05`: [#1509](https://github.com/trimble-oss/modus-wc-2.0/pull/1509) Conversation tab: Routing, QA PASSED, refine, QA FAILED, Fix applied, QA PASSED, human sign-off.
4. `MON-02`: **dashboard**, validity panel with R, D, V* and provenance badges. Fallback `SHOT-02`: terminal output of `python -m framework score` on `data/l2-eng/user-intake.json`, provenance visible.
5. `CARD-04`: the formula V* = R / (R + D) with factor icons.
6. `SHOT-03`: a `validity-diagnose` output naming the loop layer, then the intervention.

**Evidence caption:** "Modus pilot, medium PR before and after one intervention: V* 0.56 to 0.74 | weight_source=placeholder | record_kind=intake_pseudo | directional". Source: [`data/validity-report.md`](../../data/validity-report.md).

## Phase 4: Generalization beyond code (3:05-4:00)

**Say**
> The same pattern works outside engineering. Meeting notes become a reviewed ledger row, the row becomes an approved ticket, and the ticket enters the same loop. Design checks in Figma and documentation use the same skills, rules and human gates.

**Show**
- `REC-06`: the shadow review sheet, walking a completed row: reviewer comment, `cursorComment`, status `approved`, issue link, Issues tab, then the GitHub issue. Shadow sheet `1BRc5nuX1KCsPclm834eEtAkh_CYXIQvisC3wRQz9oks`. A live `review` then `approve` was not recorded, because approving would create a duplicate issue on the fork.
- `SHOT-04`: `dashboard/sheet-pilot-map.html` or `dashboard/pdlc-map.html`, the product-to-issue lane.
- Figma stays in the workflow as narration and a chip only, no clip or stills (`REC-07` dropped).
- `CARD-05`: domain chips: Engineering, Product, Design (Figma agents), Docs, Data. Mark the last two "same pattern, not yet piloted".

**Evidence caption:** "Skills vs bare agent, n=3 each, replayed persona: engineering 0.99 vs 0.64, product-to-ticket 0.98 vs 0.47, safety violations: skills 0 in every scenario, bare agent 4 on product-to-ticket (6 across all three)". Source: [`data/skill-evals/final/report.md`](../../data/skill-evals/final/report.md).

**Dashboard:** `MON-03` optional, the product-to-issue lane joined to its issue. Fallback: drop it.

## Phase 5: The end-state (4:00-5:00)

**Say**
> The goal is not more code. It is less mechanical friction. Agents build, the monitor watches, the formula measures and the skills improve the setup. People write tickets, define features and approve the result.

**Show**
- `MON-04`: **dashboard**, full-screen monitor wall with the throughput strip (QA pass rate, fix iterations, human touches). Fallback `REC-03` at full screen.
- `REC-08`: a human-only moment, approving a sheet row and the Approve review on a PR. **Recorded by you.**
- `CARD-06`: title card: `pip install pdlc-validity` | `starter-kit/` | repo URL | team names.

---

## Asset checklist

Status: `done` = captured in `raw/`; `ready` = environment ready, capture pending; `you` = you record; `fallback` = monitor not ready; `later` = built in the production plan.

| Tag | Type | Capture | Source | File name | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REC-01 | video | PR timeline branch to PR, sped up | official #1457 | `REC-01-pr-timeline.webm` | me | | done |
| REC-02 | video | PR list filter, long thread, large diff | official #1417, #1481 | `REC-02-review-load.webm` | me | | done |
| REC-03 | video | demo-story ball stalls at QA | `dashboard/demo-story/dist` | `REC-03-demo-story.webm` | me | | done |
| REC-04 | video | workflow-builder chat on sample repo | Cursor app | `REC-04-workflow-builder.mp4` | you | ready: sample repo built, see run sheet |
| REC-05 | video | Fail, fix, pass on one PR | official #1509 | `REC-05-qa-loop.webm` | me | | done |
| REC-06 | video | Completed-row walkthrough: Controls, tooltip row (status, comment, issue link), Issues tab, GitHub issue #51 | shadow sheet | `REC-06-sheet-flow.webm` | me | done |
| REC-07 | none | Figma: mention only, no capture | n/a | | n/a | dropped |
| REC-08 | video | Human approves a row and a PR | sheet, GitHub | `REC-08-human-gate.mov` | you | optional: reuse the "Moving to QA" approval at the bottom of PR #1457 |
| SHOT-01 | still | QA evidence vs bare list | official #1457 | `SHOT-01-qa-evidence.png` | me | | done |
| SHOT-02 | still | `framework score` terminal, provenance | `data/l2-eng/score-pack.json` | `SHOT-02-score.png` | me | | done |
| SHOT-03 | still | validity-diagnose: weakest layer, before/after, intervention (pilot, formula v1.1) | `data/validity-report.json` | `SHOT-03-diagnose.png` | me | done |
| SHOT-04 | still | product-to-issue map | `dashboard/sheet-pilot-map.html` | `SHOT-04-sheet-map.png` | me | | done |
| MON-01 | video | Monitor lifeline | monitor agent | | monitor agent | fallback REC-05 |
| MON-02 | video | Monitor validity panel | monitor agent | | monitor agent | fallback SHOT-02 |
| MON-03 | video | Monitor product lane (optional) | monitor agent | | monitor agent | dropped |
| MON-04 | video | Monitor wall | monitor agent | | monitor agent | fallback REC-03 |
| CARD-01 to 06, 02a-e | cards | titles, stats, formula | this doc | | me | later |

Extra capture: `SHOT-00-pr-list.png` is the official PR list with the `author:cursor[bot]` filter, usable as the opening frame of `REC-02`.

Notes from the captures:
- `REC-05` is verified frame by frame: it shows QA PASSED, then QA FAILED (visual), then the Fix applied comment, then QA PASSED on #1509, with the qa-failed, qa-full and qa-rerun labels visible. No card is needed to state the verdicts.
- `REC-02` includes the `.cursor/rules/automation.mdc` diff in #1417, a real example of rules written for the agents. Use it in Phase 3 as the "rules" visual.
- The teammate's handle is blurred in the recordings that load GitHub pages. Check once more in the final frame check.
- `SHOT-02` is rendered from `data/l2-eng/score-pack.json` (PR #1544), values unmodified.

## REC-04 run sheet (you record, Cursor app)

Sample repo: `/Users/eprabhu/Desktop/Projects/product-notes-api` (local only, a small Node HTTP API for product notes). Tests and lint pass, CI runs on pull requests, and the starter kit is installed: skills and rules in `.cursor/`, templates in `starter-kit/`, and the `pdlc-validity` CLI in `.venv/`. It was dry-run in a throwaway copy: `init` and `inspect` work, CI is detected, and the remaining gaps (no hooks, no MCP, no QA or Fix agent) are the ones the builder is meant to fill.

**Before you hit record**
1. Open the folder in a fresh Cursor window, dark theme, editor font 18pt or larger, one new chat, no other chats in the sidebar.
2. Open the integrated terminal once and run `source .venv/bin/activate`, so `python -m framework` works. Then clear it and close the panel.
3. Start the screen recording. Keep the API key, settings pages and other repos out of frame.

**What to type and answer** (the builder asks for approval before every file it writes, so approve each one)
1. Type: `use workflow-builder`. It asks "What do you want to do?" Pick **Understand my repo and current process**.
2. Discover: approve `python -m framework init` when it asks to confirm paths. It then summarizes the stack (Node, `node --test`), commands, CI on pull requests, and the gaps. Pause 3 s on the summary. If it asks for `owner/name`, answer `product-notes-api`. It may note there is no GitHub remote, which is true.
3. Interview, four short rounds of 2 to 3 questions:
   - Intake: work starts from product tickets in GitHub Issues, written by a PM.
   - Build: I pick up issues. Ready means acceptance criteria are present. Agents may take bug fixes and small endpoints, and never auth changes.
   - Verify: CI runs lint and tests, plus a QA pass. Trust evidence is passing tests and a QA comment.
   - Control: I approve the start, the review and the merge. Channel is GitHub. Platform is Cursor Automations.
4. Design: pause 3 s on the mermaid flow it shows.
5. Setup: approve writing the filled Dev, QA and Fix files to `data/automations/`. Pause on the file list.
6. Stop there. Expect 3 to 4 minutes raw, sped up to about 40 s in the video.

Save as `raw/REC-04-workflow-builder.mp4`.

## Before you record

- Rotate the exposed `CURSOR_API_KEY` after recording. Keep terminal and settings views out of frame until then.
- For `REC-04`, use the local sample repo above, no secrets in it.
- For `REC-06`, add a fresh approvable row to the shadow sheet. Keep the shadow Approve automation inactive until the take.
- Frame check every file before it goes into `raw/`: tokens, emails, private names, the teammate's handle.

## Ready gate

Production starts when every `REC-*` and `SHOT-*` is in `raw/` or marked dropped, each `MON-*` is captured or on its fallback, audio is recorded for the chosen script, and the frame check is clean.

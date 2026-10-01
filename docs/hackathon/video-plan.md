# Hackathon video plan (5 minutes)

**Working title:** Who watches the agents? Build, monitor, measure, and improve
AI-native delivery.

**Format:** 1920×1080, screen recording plus voiceover. Use the dark theme and a
large editor font (18pt or more). Keep music low under narration. Keep Marvel IP out:
no names, logos, or clips. Say "TVA-inspired" at most once.

## Shot list and voiceover

### 0:00–0:30 — Hook

**Visual:** A fast montage of agent PRs opening in GitHub while a "review queue"
counter climbs, ending on a reviewer's cursor hovering over a big diff.

**Voiceover:**
> "AI can write a pull request in minutes. Writing code is not the bottleneck any
> more. Trusting it is. Each PR still lands on a person, and that person cannot
> tell whether the workflow behind it deserves trust."

### 0:30–1:20 — The problem with the AI PDLC

**Visual:**
1. Split screen of the five places the work lives today: meeting notes, a review
   sheet, GitHub issues, the Cursor Automations console, and PR threads.
2. Screen-record `dashboard/demo-story/dist/index.html`, where the ball moves through
   the delivery nodes and then stalls at QA.
3. Show the four trust killers as text cards.

**Voiceover:**
> "Product decisions start in meetings, become tickets, get picked up by Dev, QA, and
> Fix agents, and end as PRs. Each step lives in a different tool, so nobody sees the
> whole timeline. When something breaks, like a QA loop that never re-fires, it fails
> silently.
> Benchmarks score an agent once: pass or fail. A delivery workflow is a loop that
> runs for hours, and trust decays as it runs. Context drifts. Vague specs multiply
> guesses. Wide diffs raise the blast radius. Review overhead eats the time you saved."

**Text cards:** Context drift · Spec ambiguity · Blast radius · Review overhead

### 1:20–1:50 — The solution

**Visual:** An animated loop diagram, Build → Monitor → Measure → Improve, with three
role badges: "CLI owns the facts", "AI skills reason", "Humans approve".

**Voiceover:**
> "We treat trust as something you engineer around the model. You build the
> workflow with guardrails, watch every run on one screen, measure trust with a
> recovery and decay model, and fix the weakest layer. Then you run it again."

### 1:50–3:20 — Live demo: Timeline Monitor (centerpiece)

| Time | Action on screen | Voiceover cue |
| --- | --- | --- |
| 1:50 | Open `localhost:8600/monitor`. Show the monitor wall of lifelines and the LIVE badge. | "Every automation, one screen." |
| 2:00 | On a prepared issue, comment `/approve`. Switch back; a new lifeline appears. | "A human approves. Nothing starts without that." |
| 2:15 | Dev opens the PR; the `Routing: qa-full` node lights up. | "Dev ran the gate before opening the PR." |
| 2:30 | QA posts `## QA FAILED`. The lifeline branches into a nexus event, and the ticker flashes. | "Here's a deviation from the expected timeline, caught as it happens, not a week later." |
| 2:45 | Fix posts `Fix applied:` and `QA-rerun: add`; QA reruns and posts `## QA PASSED`. The lifeline rejoins. | "The loop closes by itself, capped at three tries." |
| 3:00 | Open the validity panel: R, D, V* with provenance badges (observed / heuristic / imputed), `weight_source=placeholder`. | "Every number comes from the CLI and shows where it came from." |
| 3:15 | Show the product→issue lane: a sprint-planning note classified as `repo-work`, reviewed on the sheet, approved, and linked to the same issue you just watched. | "Same view, upstream: from meeting to issue, with a human approving every step." |

**Backup:** If the live loop is slow, switch to `--replay` from the fixture recorded
the day before. The REPLAY badge stays visible, so be honest about it in the
voiceover.

### 3:20–4:10 — Build your own

**Visual:** Cursor chat on a fresh sample repo:
1. "use workflow-builder" brings up the routing question.
2. `workflow-discover` summarizes the stack and commands.
3. `workflow-interview` asks two process questions.
4. `workflow-design` shows a mermaid flow.
5. `workflow-setup-cursor` produces filled Dev/QA/Fix templates.

**Voiceover:**
> "You don't need our setup. Drop the starter kit into any repo. The builder reads the
> code, asks how your team works, designs the stages, and writes paste-ready
> automations, either generic or with a frontend profile for visual QA. Then it hands
> the workflow straight to measurement."

### 4:10–4:40 — Evidence and honesty

**Visual:** Side by side, PR #34 and PR #42 from the Modus pilot, with their loop
timelines.

**Voiceover:**
> "We ran this on a real design-system repo. Before the change, a medium PR opened as
> 'done', QA failed, and Fix never ran. Diagnosis pointed at the loop layer. After one
> intervention, a pre-open gate plus QA and Fix wiring, the next PR failed QA once,
> got fixed, and passed. The directional score went from 0.56 to 0.74. That number uses
> placeholder weights on intake records and is not a fitted estimate, and we say so on
> screen."

**On-screen caption:** `V* 0.5615 → 0.7377 · weight_source=placeholder ·
record_kind=intake_pseudo · simulation-calibrated`

### 4:40–5:00 — Close

**Visual:** The monitor wall at full screen, then a title card.

**Voiceover:**
> "Build it, watch it, measure it, improve it. Make AI delivery trustworthy by design."

**Title card:** `pip install pdlc-validity` · `starter-kit/` · repo URL · team names.

## Assets checklist

- [ ] Timeline Monitor running locally, live and replay ([prompt](dashboard-agent-prompt.md))
- [ ] Recorded replay fixture covering a full loop with one nexus event
- [ ] Two prepared issues on the fork (one clean, one that will fail lint once)
- [ ] Sheet ledger primed per [`docs/pilot/interactive-demo-runbook.md`](../pilot/interactive-demo-runbook.md) with one approvable `repo-work` row ([demo links](../pilot/demo-workflow-links.md))
- [ ] `dashboard/sheet-pilot-map.html` and `dashboard/pdlc-map.html` as backup visuals for the product→issue segment
- [ ] `dashboard/demo-story/dist` recording for the problem segment
- [ ] Loop diagram and text cards (Figma or slides)
- [ ] Fresh sample repo for the build-your-own segment
- [ ] Screenshots of PR #34 and PR #42 timelines
- [ ] Score pack from `python -m framework score` for the validity panel
- [ ] Voiceover recorded separately; captions burned in

## Rehearsal checklist

1. The day before, run the full loop live on the fork and record it with
   `python dashboard/server.py --record`.
2. Confirm that QA re-fires after Fix (remove-then-add `qa-rerun`) and that the label
   router is installed.
3. Do a timed dry run of 1:50–3:20 with a stopwatch. If the live loop takes longer
   than 90s, cut to replay.
4. Check that no secrets, tokens, or private repo names appear on screen.
5. Do a full 5:00 read-through of the voiceover and trim anything over time.

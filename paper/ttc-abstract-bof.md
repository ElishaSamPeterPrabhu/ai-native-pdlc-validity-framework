# TTC 2027 Abstract

## Title

**AI-Native PDLC Validity Framework: Measuring Trust in Autonomous Product Delivery**

Elisha Sam Peter Prabhu · Preethi Rangamma

## Abstract

### Strategic Context

Trimble's company-wide [AI PDLC](https://trimble-ai-pdlc.web.app/) [[4](#sources)] is an operating model that uses AI agents across discovery, planning, implementation, testing, review, and release to move work from an approved problem toward delivery. Teams are adopting that path, and it is already making development faster. Every team then faces the same next question: how do we convert faster AI output into higher merge throughput while keeping human review? This session offers a target operating model in which agents drive implementation, QA, and repair while developers approve ready issues and review pull requests, plus a framework for rating whether that setup is trustworthy.

### Problem: The Review Bottleneck

AI helps teams develop changes faster. Delivery still waits on human review: a change reaches done only after someone reviews and merges the PR. As ready PR volume grows, review capacity constrains merge throughput. Recent longitudinal research reports that AI-authored pull requests take approximately 20% longer from first human review to merge, even while review depth declines under increased workload [[1](#sources)].

That bottleneck suggested a different operating model: shift scarce developer attention from code production to the merge decision. Agents implement, test, and repair; developers approve development-ready issues and review the resulting PRs.

### Solution Part 1: Automate the Delivery Workflow

Under that operating model, we automate the issue-to-PR path while retaining human review. A development-ready issue has requirements and acceptance criteria ready for implementation. For our automations, offered as a briefing for the room, we use Cursor Cloud Automations (cloud agents on GitHub) [[5](#sources)]. Agents implement, hand off to QA, and on failure to repair, cycling until ready (capped at three repair rounds for this experiment) before human PR review. AI can still return incorrect work confidently, and the team remains responsible for what merges. Each handoff must therefore leave concrete acceptance criteria, test results, and QA findings. Teams can use Cursor APIs, custom orchestration, or other agent tooling; Part 2 rates the complete setup.

> **Cloud-only note:** An ongoing experiment treats a slice of work as fully cloud-operational (Cursor Cloud Automations only; no local terminal or local development). The iPad surface is intentional: no IDE coding on device, only automations and prompts when an experiment needs them, to probe how far teams can rely on the setup for certain work and where human review must remain. This workstream is independent of the Modus formula experiment.

### Trust Gap After Automation

Concrete evidence makes each handoff checkable, but teams still need to know whether the complete workflow repeatedly produces acceptable work. Current model benchmarks primarily score models on fixed tasks [[2](#sources)]; they do not measure the combined effect of agents, context, tests, QA, repair, handoffs, and human gates over time. We need a workflow-level rating that identifies the weak control and connects evidence and task risk to review depth.

### Solution Part 2: Rate and Improve the Workflow

To answer that need, we treat trust as a changing property of verified workflow evidence, not as a score for the model alone. Errors compound as multi-step agent runs get longer, while safeguards that catch and repair them add recovery. A recovery-versus-decay model puts a number on that balance:

    dV/dt = (1 - V) * R(t) - V * D(t)

System validity `V(t)` is the verified proportion of task requirements satisfied at a lifecycle checkpoint. Decay `D` rises with context saturation, specification ambiguity, large or complex diffs, and blast radius across dependents. Recovery `R` rises when safeguards are in place: specification refinement, MCP and repository context, CI, QA, repair loops, and review gates. At equilibrium:

    V* = R / (R + D)

`V*` is the trust level the setup tends toward when recovery and decay balance. If `R = D`, it is 0.5; if recovery is three times decay, it is 0.75. If recovery is weak relative to decay, trust stays low even when agents look productive. The **AI-Native PDLC Validity Framework** uses this measurement to locate weakness in the operating environment, implement→QA→repair cycle, or workflow handoffs, then connects measured trust and task risk to review depth. Deep review stays on major or high-risk work, high-level review covers trusted work, and small low-risk work can receive minimal but nonzero review. Human review is never removed.

### Applying the Framework

**Evidence and intervention.** Monte Carlo simulations first tested whether the two-rate structure behaved as predicted and, from that evidence, set a provisional trust threshold of `V* = 0.65`. A completion guard raised the share of hard tasks correct on the first delivery by about +2 to +17 percentage points without automated QA but had near-zero effect under the full pipeline, matching the predicted ceiling; these remain simulation results. We then applied the framework to **Modus Web Components**—Trimble's open-source UI component library. In the first medium run, the workflow shape was right, but the agent skipped an acceptance criterion and claimed done without the required evidence checks. The framework located the weak recovery sub-factor as `completion_guard_hook`. After adding the completion-guard hook, a comparable run enforced acceptance checks, failed QA once, was repaired, and passed the next QA round. Provisional `V*` moved from 0.56 (below the threshold) to 0.74 (above it) using initial, not repository-fitted, weights. This below-then-above-threshold case is the provocation for the room.

> **Note:** The framework is the formula plus packaged guides, skills, and rules that turn experiment values into setup changes. We used it to improve Modus automation; other teams can do the same on their setups. The framework is for periodic diagnose and improve; it is not part of the every-PR path. That path remains implement, QA, repair, and human review.

### What Teams Get

**Part 1** automates the issue-to-PR path through harness, loop, and graph controls so developer cognitive attention can focus on review and merge metrics can rise. **Part 2** grew from recovery-versus-decay experiments into the Validity Framework, so a team can improve the weak layer and then scale review depth with measured trust and task risk. Human review remains. The intended payoff is higher merge throughput once review depth follows measured trust and task risk, building on the speed gains AI PDLC already provides. Adoption is periodic calibration of the setup. **Level 0, Observe:** provisional signal from existing CI, diff, and event data. **Level 1, Instrument:** lifecycle handoffs, verifier outcomes, repair attempts, and review burden. **Level 2, Calibrate and improve:** run baseline and factor-off tasks, fit weights, change the setup, and remeasure. Try the research-preview CLI with `pip install pdlc-validity` (https://pypi.org/project/pdlc-validity/); schemas, skills, and templates are at https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework. Modus-fitted factory weights wait on the live campaign.

### How we will carry the conversation

We will open with a short briefing on Part 1 (automate so attention focuses on review), the Modus false-completion trust gap, the console loop-closure retest, and Part 2 (the trust metric), then move into a facilitated roundtable. Prompts for the room, in order: Where does review capacity constrain merge throughput once AI makes development faster? When a PR fails trust, is the weakness in the harness, the evidence loop, or the workflow graph? After adding a stop-boundary, what evidence would you require before raising review depth? How does your team decide an AI-authored PR is safe to merge, and how deep should that review be? What evidence would the framework need to earn for high-level or minimal but nonzero review on small low-risk work, and where must deep human review stay? How would you define "good enough quality" for your setup in numbers, and who should join a follow-up Guild or working group for AI-delivery trust? We will capture the room's trust criteria and review-depth policy so the conversation continues after the session.

**Key takeaways (what the group produces):**

1. **Part 1 language for the room.** A shared picture of automating issue-to-PR work so developer attention can focus on review and merge metrics can rise, whether teams use Cursor Cloud Automations, Cursor APIs, or other agent tooling.
2. **Part 2 vocabulary and each other's trust criteria.** Recovery versus decay, plus harness/loop/graph diagnosis, gives teams a common language for the trust metric and what is missing; the room surfaces what evidence supports deep, high-level, or minimal but nonzero review.
3. **A community to continue the work.** Scale review depth with measured trust and risk, keep deep review on major work, pursue higher merge throughput as an intended outcome, and form a Guild or working group to keep comparing notes.

## Sources

1. *AI Writes Faster Than Humans Can Review: A Longitudinal Study of an Enterprise
   “2×” Mandate*, arXiv:2607.01904, 2026. Reports approximately 20% longer time from
   first human review to merge for comparable AI-authored pull requests.
2. METR, *Measuring AI Ability to Complete Long Tasks*, arXiv:2503.14499, 2025.
   Basis for task-complexity stratification and the compounding-error motivation.
3. Sierra Research, *τ-bench: A Benchmark for Tool-Agent-User Interaction in
   Real-World Domains*, arXiv:2406.12045, 2024. Source of the pass-to-the-k
   consistency measure used in the extended methodology.
4. Trimble AI PDLC, https://trimble-ai-pdlc.web.app/. Company-wide initiative for
   AI-assisted delivery across the Product Development Lifecycle.
5. Cursor, Cloud Agents and Automations, https://cursor.com/docs/cloud-agent and
   https://cursor.com/docs/cloud-agent/automations. Official primitives for
   cloud-agent execution, triggers, tools, and MCP.
6. Cursor, PR Routing & Approval and Agent Review,
   https://cursor.com/docs/approval-agents and
   https://cursor.com/docs/agent/agent-review. Official risk-based routing,
   review-depth, and approval controls.
7. LangChain, LangGraph Graph API,
   https://docs.langchain.com/oss/python/langgraph/graph-api. Official documentation
   for state, nodes, edges, and persistence in agent workflows.
8. AI-Native PDLC Validity Framework,
   https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework and
   https://pypi.org/project/pdlc-validity/. Research-preview CLI, schemas, and full
   abstract.

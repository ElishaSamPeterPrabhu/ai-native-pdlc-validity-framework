# TTC 2027 Abstract (Short) - Birds-of-a-Feather

**AI-Native PDLC Validity Framework: Measuring Trust in Autonomous Product Delivery**

Elisha Sam Peter Prabhu · Preethi Rangamma · [Full abstract](https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework/blob/main/paper/ttc-abstract.md) · [Try the framework](https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework#quick-start)

### Background and Problem

Trimble's [AI PDLC](https://trimble-ai-pdlc.web.app/) [[3](#sources)] uses AI agents across discovery, planning, implementation, testing, and delivery to move work from an approved problem toward release. It can accelerate production, but faster output does not ensure faster delivery: human review still gates merge, and comparable AI-authored PRs take about 20% longer from first review to merge [[1](#sources)]. That bottleneck suggested letting agents implement, test, and repair while developers focus on approval and merge decisions.

### Solution Part 1: Automate the Workflow

Our reference implementation uses **Cursor Cloud Automations** [[4](#sources)] to take a development-ready issue through implementation, QA, and bounded repair to a PR. Agents execute; developers approve ready issues and review every PR.

### Trust Gap After Automation

Automation creates a second problem: AI can return incorrect work confidently, while the team remains responsible for what merges. Acceptance criteria, test results, and QA findings make each handoff checkable, but teams must also know whether the complete workflow repeatedly produces acceptable work. Benchmarks evaluate models on fixed tasks; they do not answer that question across agents, context, tests, handoffs, and gates [[2](#sources)].

### Solution Part 2: Rate and Improve the Workflow

That leaves a practical question: how can a team tell whether its setup deserves trust and where it is failing? Rather than score the model alone, we treat trust as a property of verified workflow evidence that can rise or fall as work advances. We track the share of requirements verified at each lifecycle checkpoint as `V(t)`. It changes as decay `D`—context loss, ambiguity, opaque changes, and blast radius—competes with recovery `R` from repository context, CI, QA, repair, and review:

`dV/dt = (1 - V)·R(t) - V·D(t)`

`V* = R / (R + D)`

`V*` is the trust level the setup tends toward when recovery and decay balance. The **AI-Native PDLC Validity Framework** uses these measurements to locate weakness in the environment, repair cycle, or handoffs; teams change one control and measure again.

### Evidence and Use

We tested the idea in two ways. First, computer simulations asked whether the model behaved as expected: a rule that blocks “done” until evidence is present helped hard tasks when automated QA was missing, but added little once the full pipeline was in place. Those results remain **simulation** only. Second, we applied the framework to **Modus Web Components**. The first medium run failed QA and never entered repair. After a pre-open check and repaired QA→repair handoff, a comparable run failed QA, was repaired, and passed. `V*` is the long-run trust level the setup tends toward; in this pilot its provisional estimate moved from 0.56 to 0.74 using initial weights, not weights fitted to that repository. This before/after case is our provocation.

Teams **Observe**, **Instrument**, then **Calibrate and improve** by task difficulty. Measured trust plus task risk sets review depth—deep, high-level, or minimal but nonzero [[5](#sources)]. Human review remains. Install `pip install pdlc-validity` and follow the [quick start](https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework#quick-start).

### How we will carry the conversation

We open with the Modus before/after case, then discuss: Where does review capacity bind today? Which part of the environment, repair cycle, or handoff failed? What evidence should each stage earn before review depth can fall? We capture shared trust criteria, a draft review policy, and interest in a follow-up working group.

**Takeaways (what the group produces):**

1. Shared language for rating workflow trust and naming weak controls.
2. Draft evidence thresholds for deep, high-level, or minimal review.
3. A path to try the framework on your own repository after the session.

## Sources

1. *AI Writes Faster Than Humans Can Review: A Longitudinal Study of an Enterprise “2×” Mandate*, arXiv:2607.01904, 2026. Reports approximately 20% longer time from first human review to merge for comparable AI-authored pull requests.
2. METR, *Measuring AI Ability to Complete Long Tasks*, arXiv:2503.14499, 2025. Basis for task-complexity stratification and the compounding-error motivation.
3. Trimble AI PDLC, https://trimble-ai-pdlc.web.app/. Company-wide initiative for AI-assisted delivery across the Product Development Lifecycle.
4. Cursor, Cloud Agents and Automations, https://cursor.com/docs/cloud-agent and https://cursor.com/docs/cloud-agent/automations. Official primitives for cloud-agent execution, triggers, tools, and MCP.
5. Cursor, PR Routing & Approval and Agent Review, https://cursor.com/docs/approval-agents and https://cursor.com/docs/agent/agent-review. Official risk-based routing, review-depth, and approval controls.

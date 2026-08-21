# TTC 2027 Abstract (Short) - Oral Presentation

**AI-Native PDLC Validity Framework: Measuring Trust in Autonomous Product Delivery**

Elisha Sam Peter Prabhu · Preethi Rangamma · [Full abstract](https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework/blob/main/paper/ttc-abstract.md) · [Try the framework](https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework#quick-start)

### Background and Problem

Trimble's [AI PDLC](https://trimble-ai-pdlc.web.app/) [[3](#sources)] is an operating model for AI-assisted delivery that organizes work through Discovery (T0), Viability (T1), and Build & Test (T2) and accelerates production. That faster production does not guarantee faster delivery: human review still gates merge, and comparable AI-authored PRs take about 20% longer from first review to merge [[1](#sources)]. That bottleneck suggested automating the development process so people can focus on review and merging, turning faster production into faster delivery.

### Solution Part 1: Automate the Workflow

For our automations, we use **Cursor Cloud Automations** to take a development-ready issue through implementation, QA, and bounded repair to a PR. Agents execute; developers approve ready issues and review every resulting PR.

### Trust Gap After Automation

Automation creates a second problem: AI can return incorrect work confidently, while the team remains responsible for what merges. Acceptance criteria, tests, and QA findings make handoffs checkable, but teams must also know whether the full workflow repeatedly produces acceptable work. Existing benchmarks help a bit, but they evaluate models, not whether the workflow setup repeatedly produces acceptable work [[2](#sources)]. So we built a framework to benchmark the setup.

### Solution Part 2: Rate and Improve the Workflow

How can a team tell whether its setup deserves trust and where it is failing? Rather than score the model alone, we treat trust as verified workflow evidence that rises or falls as work advances. `V(t)` is the share of requirements verified at each checkpoint. Decay `D` competes with recovery `R`:

`dV/dt = (1 - V)·R(t) - V·D(t)`

`V* = R / (R + D)`

`V*` is where trust settles when those forces balance (0.5 when R equals D; 0.75 when R is 3× D). `D(t)` is how fast trust erodes—lost context, unclear acceptance criteria, hard-to-review changes, or wide impact of a mistake. `R(t)` is how fast trust is restored—CI, QA, repair, review gates, and a completion guard. Full factor definitions: https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework/blob/main/theory/formula.py. The **AI-Native PDLC Validity Framework** uses this measurement to find weak controls and improve them.

### Validation and Adoption

We will explain validation with the framework using an example from one of the simulations we conducted. We ran that example on **Modus Web Components**—Trimble's open-source UI component library—on our Cursor Cloud Automations path from a development-ready issue through implementation, QA, and repair to a PR. From earlier simulation evidence we used a provisional trust threshold of `V* = 0.65`. Applying the framework, we scored the run and diagnosed where trust failed: the workflow shape was right, but the agent skipped an acceptance criterion and claimed done without required evidence. That helped us find the weak recovery sub-factor `completion_guard_hook`; provisional `V*` was 0.56, below the threshold. Our plan was to add the completion-guard hook so unfinished work cannot claim done without acceptance evidence, then re-run. After that change, acceptance checks were enforced, quality failed once, was repaired, then passed, and provisional `V*` reached 0.74, above the threshold (initial weights, not fitted). That left a more believable workflow: iterating with the framework produced a stronger AI path on Modus Web Components that improved not only production but the delivery of an issue.

Note: The framework can be accessed via `pip install pdlc-validity` [[4](#sources)].

**Takeaways:**

1. Automate the development path so people can focus on reviewing and merging, which is how faster production becomes faster delivery.
2. Rate whether the whole setup earns trust, find the weakest control with the framework, and improve that control before trusting outcomes.
3. Leave with a review policy that sets depth from measured trust and task risk—deep, high-level, or minimal but nonzero—with humans only involved in the review process, ensuring faster delivery with accurate production-quality results.

## Sources

1. *AI Writes Faster Than Humans Can Review: A Longitudinal Study of an Enterprise “2×” Mandate*, arXiv:2607.01904, 2026. Reports approximately 20% longer time from first human review to merge for comparable AI-authored pull requests.
2. METR, *Measuring AI Ability to Complete Long Tasks*, arXiv:2503.14499, 2025. Basis for task-complexity stratification and the compounding-error motivation.
3. Trimble AI PDLC, https://trimble-ai-pdlc.web.app/. Company-wide initiative for AI-assisted delivery across the Product Development Lifecycle.
4. AI-Native PDLC Validity Framework, https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework and https://pypi.org/project/pdlc-validity/. Research-preview CLI, schemas, and full abstract.

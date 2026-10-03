# AI-Native PDLC Validity Framework

Research preview for measuring whether an AI-assisted delivery workflow—from approved
issue through implementation, QA, repair, and human PR review—deserves trust.

**Status:** research preview `0.3.0` · formula `v1.4` · evidence
`simulation-calibrated` (live pilot documented; repo-fitted weights pending)

**Maintainers:** [Elisha Sam Peter Prabhu](https://github.com/ElishaSamPeterPrabhu) · [Preethi Rangamma](https://github.com/preethi-rangamma-7)

- [Quick start](#quick-start)
- [Full abstract](paper/ttc-abstract.md)
- [Framework contract](framework/CONTRACT.md)
- [Claim boundaries](RESEARCH-PREVIEW.md)

## Quick start

Install the CLI:

```bash
pip install pdlc-validity
```

Or run from this repository:

```bash
pip install -e .
```

Inspect your repository (read-only; writes `validity.layout.json` on first run):

```bash
pdlc-validity init --repo .
pdlc-validity inspect --repo .
pdlc-validity evidence --repo .
```

Equivalent module form:

```bash
python -m framework init --repo .
python -m framework inspect --repo .
```

Install the workflow builder into your repo, then check what it generates:

```bash
pdlc-validity init-kit --repo .      # copies skills, rules and templates; never overwrites unless --force
# in Cursor: "use workflow-builder"
pdlc-validity check-kit --repo .     # checks the generated Dev/QA/Fix files for known unsafe patterns
```

### What you get

| Artifact | Purpose |
| --- | --- |
| [`framework/`](framework/) | CLI, schemas, templates, intervention catalog, bundled workflow-builder kit |
| [`paper/`](paper/) | TTC abstracts and pilot summary |
| [`theory/formula.py`](theory/formula.py) | Canonical recovery/decay model |
| [`.cursor/skills/validity-*`](.cursor/skills/) | Optional Cursor skills for diagnose/improve |

### Role split

- **CLI** emits facts: inspect, evidence, score, delta, report.
- **AI skills** (optional) reason about harness, loop, and graph weaknesses.
- **Humans** approve setup changes and every merge.

Read [`framework/CONTRACT.md`](framework/CONTRACT.md) before citing numeric results. Do not
treat placeholder-weight `V*` values as fitted causal estimates.

## Try it in your workflow

1. Run `pdlc-validity init --repo .` in a repository that uses agent automations.
2. Run `pdlc-validity inspect --repo .` to see measurement gaps.
3. Paste automation/PR evidence with `pdlc-validity intake --repo . --intake path/to/intake.json`
   (see [`framework/templates/intake/user-intake.example.json`](framework/templates/intake/user-intake.example.json)).
4. Use `pdlc-validity score` for CLI-owned R/D/V* with provenance labels.

More detail: [`framework/README.md`](framework/README.md) and
[`framework/AGENT-HANDOFF.md`](framework/AGENT-HANDOFF.md).

PyPI releases use [trusted publishing](docs/PYPI_TRUSTED_PUBLISHING.md). Until that
one-time setup is complete, install from GitHub:

```bash
pip install git+https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework.git@v0.2.0
```

## Build, Monitor, Measure, Improve

The framework does more than measure. It also helps you build the workflow you measure:

1. **Build.** Run `pdlc-validity init-kit --repo .` (or copy [`starter-kit/`](starter-kit/)
   by hand) and ask Cursor to "use workflow-builder". It reads your repo, asks how your team works, designs
   product→issue and issue→PR stages, and fills Cursor Automation (or GitHub
   Actions) templates. These follow a shared [signal contract](starter-kit/signal-contract.md).
2. **Monitor.** A local timeline monitor for automation runs is in development. Today,
   `python dashboard/server.py` serves the validity dashboard from a repository checkout.
3. **Measure.** Use `pdlc-validity evidence` / `score` for R/D/V* with provenance.
4. **Improve.** Apply `validity-diagnose` → `validity-improve`, then feed changes back
   into `workflow-design`.

## Evidence so far

**Do the builder skills help? A controlled replay.** We replayed three scenarios with a
fixed interview persona and scored the generated files with deterministic checks (no
model grading). Each scenario ran 3 times with the skills installed and 3 times with a
bare agent, using the same model.

![Overall score per run, with skills and bare agent](https://raw.githubusercontent.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework/main/data/figures/skill-eval-l1.png)

| Scenario | With skills (mean) | Bare agent (mean) | Safety violations: skills / bare |
| --- | --- | --- | --- |
| Engineering, production web app | 0.99 | 0.64 | 0 / 0 |
| Product to ticket | 0.98 | 0.47 | 0 / 4 |
| Generic control | 1.00 | 0.61 | 0 / 2 |

Both gated scenarios passed all four pre-registered criteria (critical-check rate,
pass^k, no safety violations, beats the bare agent).

**What this does and does not show.** All three runs passed with skills in every
scenario, but with only three runs the true per-run pass rate could be as low as 29%
at 95% confidence. Backing a claim of at least 90% would take 29 consecutive passing
runs per scenario. A replayed persona is not a live team, one model was used, and two
non-critical checks (`route.capability_skills`, `sig.label_pulse`) still failed in the
skills arm. Treat this as directional evidence. Full report:
[`data/skill-evals/final/report.md`](data/skill-evals/final/report.md).

**Does the measurement move in the right direction? A pilot.** On a production web
app's design-system repo, one change to the Dev/QA/Fix loop took the directional score
from 0.56 to 0.74. That used placeholder weights and intake pseudo-records, so it is a
direction, not a fitted estimate. See the [pilot summary](paper/modus-pilot-abstract-summary.md).

**Check your own output.** `pdlc-validity check-kit` applies the safety and signal rules
the evals scored to the files your builder run wrote: no "Anyone" comment trigger, a
"humans merge" line, no agent merge instruction, QA woken by a label (not by a PR
opening), exact verdict headings, and an iteration cap on the Fix loop. It reads file
text; it cannot prove an automation behaves correctly.

## License

Apache-2.0. See [LICENSE](LICENSE).

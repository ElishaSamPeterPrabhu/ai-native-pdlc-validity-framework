# AI-Native PDLC Validity Framework

Research preview for measuring whether an AI-assisted delivery workflow—from approved
issue through implementation, QA, repair, and human PR review—deserves trust.

**Status:** research preview `0.1.0` · formula `v1.1` · evidence
`simulation-calibrated` (live Modus pilot documented; repo-fitted weights pending)

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

### What you get

| Artifact | Purpose |
| --- | --- |
| [`framework/`](framework/) | CLI, schemas, templates, intervention catalog |
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
pip install git+https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework.git@v0.1.0
```

## Research evidence

- Structural simulations tested the recovery/decay model before live use.
- Modus Web Components console pilot: open QA/repair cycle → one intervention → closed cycle.
- See [`paper/modus-pilot-abstract-summary.md`](paper/modus-pilot-abstract-summary.md).

## License

Apache-2.0. See [LICENSE](LICENSE).

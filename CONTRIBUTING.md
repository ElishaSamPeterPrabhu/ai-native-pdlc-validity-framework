# Contributing

Thank you for interest in the AI-Native PDLC Validity Framework research preview.

## Before you open a PR

1. Read [`framework/CONTRACT.md`](framework/CONTRACT.md) and [`RESEARCH-PREVIEW.md`](RESEARCH-PREVIEW.md).
2. Keep CLI-owned numbers in the CLI; do not move formula evaluation into docs or skills.
3. Label synthetic or placeholder evidence clearly.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[validate]"
python -m framework validate --repo . --out data/validation
```

## Pull requests

- One logical change per PR when possible.
- Include a short note on claim boundaries if you touch scoring, schemas, or abstracts.

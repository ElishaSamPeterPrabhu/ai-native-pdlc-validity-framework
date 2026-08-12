# PyPI trusted publishing (one-time setup)

The `Publish to PyPI` workflow runs when a GitHub release is published. Complete
this one-time setup on [pypi.org](https://pypi.org) before the first upload succeeds.

## Pending publisher

1. Sign in to PyPI and open **Account settings → Publishing**.
2. Add a **pending publisher** with:
   - **PyPI project name:** `pdlc-validity`
   - **Owner:** `ElishaSamPeterPrabhu`
   - **Repository:** `ai-native-pdlc-validity-framework`
   - **Workflow filename:** `publish.yml` (under `.github/workflows/`)
   - **Environment name:** `pypi`
3. In GitHub, open **Settings → Environments → New environment** named `pypi` (no secrets required for trusted publishing).

## Re-run after approval

```bash
gh release create v0.1.0 --title "v0.1.0 — research preview" --notes "Research preview"
```

Or re-run the failed **Publish to PyPI** workflow from the Actions tab.

## Local install before PyPI

```bash
pip install git+https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework.git@v0.1.0
```

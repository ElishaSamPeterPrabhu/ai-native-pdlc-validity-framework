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
gh release create v0.2.0 --title "v0.2.0 — research preview" --notes "Research preview"
```

Or re-run the failed **Publish to PyPI** workflow from the Actions tab.

## Local install before PyPI

```bash
pip install git+https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework.git@v0.2.0
```

## Add a co-owner on PyPI

After the first successful upload of `pdlc-validity`:

1. Sign in to PyPI as the publishing account owner.
2. Open **Your projects → pdlc-validity → Collaborators**.
3. Invite **Preethi Rangamma** using her PyPI username (create a PyPI account first if needed).
4. Set role to **Owner** so she can manage releases and trusted publishing.

If you use a PyPI **organization** instead of a personal account, add her as an
organization owner there before linking the project.

## GitHub access

Repository co-maintainer: **[@preethi-rangamma-7](https://github.com/preethi-rangamma-7)**  
Invited with **Admin** access (highest level on a personal repository). She must accept the invitation email or the [pending invite](https://github.com/ElishaSamPeterPrabhu/ai-native-pdlc-validity-framework/invitations).

For true shared ownership of the GitHub repository, transfer it to a GitHub
Organization and add both accounts as org owners.

---
name: modus-generate-states
description: Inspect existing Figma variants and generate missing states with rationale — Default, Hover, Focus, Error, Loading, Open, Selected, and more. Uses Modus Storybook naming and web standards. Invoke with /modus-generate-states.
---

# Modus generate states

You help **Modus library designers** complete their **variant/state coverage** in Figma. Read what they already have, compare to the Modus state contract and web standards, then list **missing states** with clear design direction for each.

## When to use

- Component has some variants but designer is unsure what's missing
- Starting a new Modus component and needs a full state matrix
- Designer asks to "generate states" or "what states should this have?"
- Before Storybook parity review

## Mandatory intake (if not clear)

Ask only what you cannot infer from the selection:

1. **Which component?** (name / Modus tag if known)
2. **What states do you already have?** (or read from variant names)
3. **Anything to exclude?** (e.g. no RTL yet, no loading)

## How to work

### Step 1 — Read current variants

Inspect the selection's component set or variant property names. List what exists:

- Default, Hover, Focus, Active, Disabled, Loading, Error, Empty, Selected, Open, Indeterminate, ReadOnly, WithErrorFeedback, etc.

### Step 2 — Map to Modus state contract

Compare against the standard set (include only what applies to this component type):

| State | Typical trigger | Visual expectation |
| --- | --- | --- |
| Default | Rest | Base tokens, no emphasis |
| Hover | Pointer over | Subtle fill or border change |
| Focus / FocusVisible | Keyboard tab | Visible focus ring (WCAG 2.4.11) |
| Active / Pressed | Mouse/touch down | Darker fill or inset |
| Disabled | `disabled` | Muted, non-interactive appearance |
| Loading | Async wait | Spinner or skeleton; preserve label space |
| Error / WithErrorFeedback | Invalid input | Error border + message area |
| Empty | No value / no data | Placeholder or empty message |
| Selected | Value chosen / row selected | Selected background or checkmark |
| Open | Dropdown/popover expanded | Panel visible, chevron rotated |
| Indeterminate | Partial checkbox selection | Dash or mixed icon |
| ReadOnly | Non-editable value | Looks static but not disabled |
| RTL | Right-to-left locale | Mirrored layout |

Not every component needs every state. Omit what does not apply (e.g. Open only for dropdowns).

### Step 3 — Check web standards

Use **web search** when needed:

- Form controls: required error association, label visibility
- Listbox/combobox: keyboard selection states
- Checkbox: indeterminate semantics
- WCAG 2.4.11 focus visible, 1.4.3 contrast for error states

### Step 4 — Generate missing states

For each missing state provide:

- **Name** — PascalCase, match Storybook story names when known (e.g. `WithErrorFeedback`, `ShadowDomParent`)
- **Trigger** — when this state appears
- **Visual change** — color, icon, text, layout (reference Modus tokens when sensible: `--modus-wc-color-alert-danger`, input height tokens, etc.)
- **Source** — Storybook existing | new-api-candidate | web standard requirement

### Step 5 — Offer naming help

Suggest variant property names consistent with Modus (PascalCase state names in Figma matching Storybook).

## Output format

```markdown
## State coverage for [Component name]

**Modus tag:** [tag or unknown]
**Already have:** [list existing variants]
**Missing:** [count]

### Missing states

#### [StateName]
- **When:** [trigger]
- **Look like:** [visual direction]
- **Why:** [Storybook / standard / sibling precedent]
- **Status:** existing in Storybook | new-api-candidate

[repeat per state]

### Suggested order to build in Figma
1. [priority order — Focus and Error before edge cases]

### Next step
- Run `/modus-accessibility-check` on Focus and Error states
- Cursor `design-capability-check` to confirm Storybook story list
```

## Example (Select with only Default + Disabled)

**Missing states for Select:**

- **Focused** — keyboard tab; visible outline, no fill swap (WCAG 2.4.11)
- **WithErrorFeedback** — validation failed; error text + danger border token
- **Loading** — options fetching; spinner replaces chevron
- **Open** — menu expanded; chevron up, listbox visible
- **Selected** — value chosen; label shows current selection (not placeholder)

## Rules

- Read variants from the selection — do not assume Default only.
- Do not invent Storybook story names; say **new-api-candidate** if unverified.
- Prioritize Focus, Error, Disabled, Loading before cosmetic states.
- Keep language designer-friendly — no schema kind labels in the main list.
- After generating, offer `/modus-accessibility-check` for Focus, Error, Disabled.

## Example triggers

- "Generate all missing states for this dropdown"
- "What variants am I missing on modus-wc-checkbox?"
- "I only have Default — what else do I need?"

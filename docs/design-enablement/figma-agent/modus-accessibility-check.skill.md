---
name: modus-accessibility-check
description: Accessibility and WCAG review for Modus components — ARIA patterns, keyboard, focus, contrast, form semantics. Works for any component type, not only select/readonly. Use web search for APG and WCAG. Invoke with /modus-accessibility-check.
---

# Modus accessibility check

You help **Modus library designers** design accessible components in Figma — keyboard, focus, screen reader semantics, color contrast, and valid HTML/ARIA patterns — for **any** component type.

## When to use

- Adding or reviewing states: disabled, readonly, error, loading, focus, selected
- Designing lists, menus, trees, dialogs, tabs, tooltips, or custom widgets
- Before sign-off on form controls or navigation patterns
- When `/modus-capability-check` flagged a standards **warning** or **unsupported**

## Mandatory intake (if not clear)

1. **What outcome do you need?** (prevent edit, show value only, announce errors, keyboard navigate, etc.)
2. **Which state or interaction** are you checking? (or all variants on selection)

## How to behave

1. **Inspect the selection** — variants, labels, error text, focus rings, icon-only buttons, touch targets.
2. **Identify the ARIA pattern** — use [WAI-ARIA APG](https://www.w3.org/WAI/ARIA/apg/) (search web when unsure).
3. **Check WCAG** — use web search for current criteria; cite success criterion numbers.
4. **Give Figma-specific fixes** — what to add or change in variants and annotations.
5. **Separate** Modus API gaps from HTML/ARIA constraints.

## ARIA pattern map

| Designer intent | APG pattern | Key keyboard | Required semantics |
| --- | --- | --- | --- |
| Pick one from list | Listbox | Arrow keys, Enter | option selected, label |
| Dropdown + typeahead | Combobox | Arrow, type, Escape | expanded, controls, activedescendant |
| Action list | Menu / Menu button | Arrow, Escape | menuitem, expanded |
| Hierarchy navigation | Tree | Arrow, Expand/Collapse | treeitem, expanded, level |
| Modal task | Dialog | Tab trap, Escape | focus trap, labelledby |
| On/off | Switch / Checkbox | Space | checked, disabled |
| Single-line input | Textbox | Standard tab | label, describedby for errors |
| Pick from options | Select (native) | Space/Enter open | no native readonly |

Use web search to confirm pattern details for the specific component.

## WCAG checks (apply when relevant)

| Criterion | Check in Figma |
| --- | --- |
| **1.4.3 Contrast (AA)** | Text vs background ≥ 4.5:1 (3:1 large text) |
| **1.4.11 Non-text contrast** | Icons, borders, focus ring ≥ 3:1 |
| **2.4.7 Focus visible** | Focus variant clearly distinct (prefer **2.4.11** focus appearance) |
| **2.5.8 Target size** | Interactive targets ≥ 24×24 CSS px where possible |
| **3.3.1 Error identification** | Error state + visible error text, not color alone |
| **4.1.2 Name, role, value** | Label visible or documented for dev; state reflected in design |

Use web search if you need exact threshold or exception wording.

## Known guardrails (always apply)

### Native select + readonly

HTML `select` does **not** support `readonly`. Alternatives:

- Controlled select (enabled, app prevents change)
- Read-only display + hidden submitted value
- Disabled (only if no focus + excluded from submit is acceptable)

### Disabled vs read-only

- **Disabled:** typically no tab focus, excluded from form submit, different SR announcement
- **Read-only** (text input): still focusable; different from disabled visually and semantically

### Error states

- Error message text visible in design (not icon-only)
- Associate error with field (annotation for dev: `aria-describedby` or visible text below)
- Do not rely on color alone (WCAG 1.4.1)

### Icon-only controls

- Require visible tooltip or text alternative in design spec
- Document accessible name for dev

## State-specific review

For each variant the designer asks about:

| State | Accessibility question |
| --- | --- |
| Focus | Is focus indicator visible at 3:1 against adjacent colors? |
| Disabled | Is it clearly non-interactive? Document if it stays in tab order (usually no) |
| Error | Is error text present and linked to the field? |
| Loading | Is loading announced? Is content still labeled? |
| Selected | Is selection visible beyond color alone? |

## Output format

```markdown
## Accessibility check

**Selection:** [name]
**Pattern:** [APG pattern name]
**Goal:** [designer outcome]
**Compatibility:** compatible | warning | unsupported

### Constraints
- [plain-language rules]

### Keyboard and focus
- [expected behavior for this pattern]

### Options (if unsupported)
| Option | Focus | Submission | Screen reader | Notes |
| --- | --- | --- | --- | --- |

### Figma changes
- [specific variant, label, focus ring, error placement fixes]

### WCAG / standards
- [criterion numbers + links from search]

### Modus API note (separate)
- [only if Modus manifest is relevant — do not merge with HTML rules]
```

## Rules

- Lead with **what to change in Figma**.
- Use web search for APG and WCAG when the pattern is not in the guardrails above.
- Never approve readonly-on-select as native HTML.
- Never conflate Modus manifest gaps with web standards failures.
- After review, offer `/modus-generate-states` if variants are missing.

## Example triggers

- "Is readonly OK on this select?"
- "Check keyboard for this tree menu"
- "Does this error state meet WCAG?"
- "Review focus visible on all button variants"

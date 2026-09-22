/**
 * One-time: replace pilot demo Gemini notes Doc body (plain text).
 * Doc: https://docs.google.com/document/d/1kAzZm9NxdWsvCKuGvai_HZbM9eiuH7dWRZp2Tt0XmAQ/edit
 * Source: docs/pilot/demo-sprint-planning-notes-doc-body.txt (keep in sync).
 */
function applyPilotDemoNotesToDoc() {
  const docId = '1kAzZm9NxdWsvCKuGvai_HZbM9eiuH7dWRZp2Tt0XmAQ';
  const text = getPilotDemoNotesPlainText();
  const body = DocumentApp.openById(docId).getBody();
  body.clear();
  body.appendParagraph(text);
  Logger.log('Applied pilot demo notes body to ' + docId);
}

function getPilotDemoNotesPlainText() {
  return `# **✍️ Quick notes**

## **Sprint Planning**

Sep 15, 2026

[Sunderrajan Thiruvengadathan](mailto:sunderrajan_thiruvengadathan@trimble.com) [Mitch Ray](mailto:mitch_ray@trimble.com) [James Tran](mailto:james_tran@trimble.com) [Elisha Sam Peter Prabhu](mailto:elisha_sampeterprabhu@trimble.com) [Jewel Shajan](mailto:jewel_shajan@trimble.com) [Kavin S](mailto:kavin_s@trimble.com) [Martin Espericueta](mailto:martin_espericueta@trimble.com) [~~Jared Bloch~~](mailto:jared_bloch@trimble.com)

Sprint prioritization for Modus web components — sheet-led review demo with one primary repo-work item.

## **Sprint Planning and Releases**

- Team agreed to prioritize a **disabled state** on **modus-wc-button** for the current pilot slice.
- Release planning for unrelated components deferred; this cycle focuses on review ledger → approve → pilot scaffolding.
- Carry-over items stay sized as small when only polish remains.

## **Component Development**

- **modus-wc-button:** add boolean **disabled** prop — default \`false\`; block activation when true; set **\`aria-disabled="true"\`**; use Modus disabled visual tokens (opacity / not-allowed cursor).
- **modus-wc-loader:** team mentioned spinner sizing but did **not** agree numeric targets (clarification candidate only).
- Status, stacked alert, and batch variants discussed — tracked separately, **not** the pilot demo row.

## **Planning Processes**

- Human gate on **Review ledger Controls B1**: \`review\` then \`approve\` after reviewer comment and acceptance criteria.
- Meeting Intake classifies Gemini notes; **pilot Issue Scaffolding only** creates GitHub issues after approve.

## **Next steps**

- [Elisha Sam Peter Prabhu] **Add disabled prop to button:** Implement boolean \`disabled\` on \`modus-wc-button\` with accessible disabled behavior (repo-work).
- [Mitch Ray] **Review ledger:** Confirm acceptance criteria on the disabled-button row before approve.
- [James Tran] **Design check:** Confirm token-based disabled styling; no new Figma spec required.
- [Kavin S] **Maybe fix spinner sizes:** Capture loader sizing ask without AC — clarification path only.
- [Elisha Sam Peter Prabhu] **Sheet approve:** Run approve on Controls B1 after review write-back for the disabled-button row.

# **📝 Full notes**

Sep 15, 2026

## **Sprint Planning**

Invited [Sunderrajan Thiruvengadathan](mailto:sunderrajan_thiruvengadathan@trimble.com) [Mitch Ray](mailto:mitch_ray@trimble.com) [James Tran](mailto:james_tran@trimble.com) [Elisha Sam Peter Prabhu](mailto:elisha_sampeterprabhu@trimble.com) [Jewel Shajan](mailto:jewel_shajan@trimble.com) [Kavin S](mailto:kavin_s@trimble.com) [Martin Espericueta](mailto:martin_espericueta@trimble.com) [~~Jared Bloch~~](mailto:jared_bloch@trimble.com)

Attachments [Sprint Planning](https://calendar.google.com/calendar/event?eid=pilot-demo-placeholder)

### **Summary**

Sprint prioritization for sheet-led pilot demo. One primary engineering item: **disabled button prop**.

**Button disabled state**
Expose \`disabled\` on \`modus-wc-button\`. When true: suppress click activation, expose \`aria-disabled\`, apply disabled styling consistent with Modus tokens.

**Loader sizing (deferred detail)**
Team mentioned spinner / loader dimensions without agreed numbers — not ready for scaffolding without clarification.

### **Decisions**

## **Aligned**

- **Disabled prop in scope this sprint** The team agreed to treat **modus-wc-button disabled** as repo-work on the pilot fork with explicit acceptance criteria before approve.
- **Loader sizing stays fuzzy** The team decided not to open a GitHub issue for loader sizing until numeric AC exists.
- **Sheet human gate** The team agreed review → approve on the ledger is required before pilot Issue Scaffolding runs.

### **Next steps**

- [Elisha Sam Peter Prabhu] Add disabled prop to button: Implement boolean disabled on modus-wc-button (repo-work).
- [Mitch Ray] Review ledger: Reviewer comment + AC on disabled row; then approve on B1.
- [Kavin S] Maybe fix spinner sizes: Log as needs-clarification only.

### **Details**

- **Disabled prop (\`modus-wc-button\`):** Elisha Sam Peter Prabhu confirmed Modus button patterns need a first-class disabled prop. Mitch Ray listed acceptance criteria: default \`disabled=false\`; click handlers do not fire when disabled; host sets \`aria-disabled=true\`; visual matches Modus disabled tokens. Classification: **repo-work**; design not required.
- **Loader sizing (\`modus-wc-loader\`):** Kavin S raised inconsistent loader sizes; team did not agree target pixels — route to **clarification** until AC exists.
- **Planning Processes:** Gemini notes → Meeting Intake → review ledger → Controls B1 approve → pilot scaffolding → issue URL write-back.

*You should review Gemini's notes to make sure they're accurate.*`;
}

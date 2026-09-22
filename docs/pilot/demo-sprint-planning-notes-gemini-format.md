# Demo Sprint Planning notes (Gemini-style)

**Google Doc:** https://docs.google.com/document/d/1kAzZm9NxdWsvCKuGvai_HZbM9eiuH7dWRZp2Tt0XmAQ/edit  
**Doc id:** `1kAzZm9NxdWsvCKuGvai_HZbM9eiuH7dWRZp2Tt0XmAQ`

Same **schema** as real Gemini exports (Quick notes + Full notes). Content targets **modus-wc-button disabled** (pilot / #49 story), not the Sep 1 status-component meeting.

## Sync body into Google Doc

The agent cannot overwrite an existing Doc body via Drive MCP (metadata only). Use either:

1. **Manual (keeps Doc headings):** In the Doc, replace text under **Quick notes** and **Full notes** from [`demo-sprint-planning-notes-doc-body.txt`](demo-sprint-planning-notes-doc-body.txt) — keep Gemini footers / survey lines if already present.
2. **Apps Script (one run):** In any Apps Script project → Run `applyPilotDemoNotesToDoc()` from [`demo-sprint-planning-notes-sync.gs`](demo-sprint-planning-notes-sync.gs) (plain-text body; re-apply heading styles in Doc if needed).

**Live intake:**

```javascript
testDispatchDocId('1kAzZm9NxdWsvCKuGvai_HZbM9eiuH7dWRZp2Tt0XmAQ');
```

See [`pilot-test-runbook.md`](../chat-bots/pilot-test-runbook.md).

---

Canonical body: [`demo-sprint-planning-notes-doc-body.txt`](demo-sprint-planning-notes-doc-body.txt)

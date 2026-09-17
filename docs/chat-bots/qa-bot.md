# Modus Q&A Google Chat bot

**Workflow template:** [`workflows/qa-bot.template.json`](workflows/qa-bot.template.json)  
**Primary job:** answer questions from the shared Modus context  
**Secondary job:** offer a confirmed draft issue when the answer reveals real work

## Behavior

The Q&A bot is invoked by mentioning the Google Chat app in a thread. It
captures the question and enough recent thread context to resolve references
such as “this state” or “the component above.” It then answers with evidence
from the target repository:

1. `src/custom-elements.json`;
2. Modus component-docs MCP;
3. component readmes and Storybook stories;
4. `AGENTS.md` and applicable `.cursor/rules/*`;
5. the component graph;
6. GitHub issues and PRs.

The answer states what is known, what is not found, and what source supports
each capability claim. It does not use a generic model memory as a source.

In the private pilot, the bot must call the `context-resolver` n8n sub-workflow
before answering capability questions. The resolver returns exact manifest
evidence or `notFound`; the model must not answer from the Chat text alone.

## Answer / escalation policy

| Result | Response |
| --- | --- |
| Known repository answer | Cite and answer in the thread; no issue |
| Existing issue/PR answers it | Link the issue/PR and summarize status; no issue |
| Question needs human/product decision | Ask one focused question; no issue |
| Repository gap implies concrete work | Explain the gap and offer `Draft an issue` |
| User confirms draft | Call the shared issue service with `autoApprove: false` |
| Request is process/meta | Explain the appropriate human workflow; no issue |

The bot never creates an issue merely because a capability is absent. Absence
must be connected to a requested outcome, and the user must confirm the draft.
The resulting issue goes through Issue Scaffolding v2, which may ask more
questions before it is implementation-ready.

## Response contract

The model returns:

```json
{
  "answer": "The answer in plain language.",
  "confidence": "high|medium|low",
  "evidence": [
    {
      "claim": "modus-wc-text-input exposes readOnly.",
      "source": "src/custom-elements.json#/modules/modus-wc-text-input"
    }
  ],
  "status": "answered|needs_clarification|work_implied|not_found",
  "followUpQuestion": null,
  "issueDraft": null
}
```

For `work_implied`, `issueDraft` is a preview only:

```json
{
  "title": "Add a documented read-only state for select",
  "summary": "The team needs a non-editable selected value...",
  "type": "feature",
  "components": ["modus-wc-select"],
  "labels": ["needs-scaffolding", "design-research"],
  "acceptanceCriteria": [
    "The selected value remains visible.",
    "Keyboard and pointer interaction follow the approved behavior."
  ],
  "designNeeded": true
}
```

## Thread context and state

The workflow keeps only the minimum state required for an escalation:

```json
{
  "threadName": "spaces/AAA/threads/BBB",
  "lastAnswer": "...",
  "evidence": [],
  "issueDraft": {},
  "confirmationToken": "...",
  "updatedAt": 1760000000000
}
```

State is stored in `$getWorkflowStaticData('global')`, keyed by thread name,
and expires after 24 hours. A confirmation token is single-use. The raw thread
is sent to the issue service only after confirmation and is bounded to the
latest 100 messages.

## Source and citation rules

- A manifest/MCP citation is required for every “supports” or “does not
  support” claim.
- A component graph citation is required for a blast-radius claim.
- A Storybook/readme citation is required for usage or visual behavior.
- If the source is unavailable, say “the framework does not have the necessary
  source to answer this” and list the missing source. Do not turn low
  confidence into a ticket automatically.
- Link to the target repo, issue, PR, or staged design artifact where possible.

## n8n workflow

The sanitized export follows the existing release-notes bot structure:

- Google Chat app Webhook with a Respond-to-Webhook response;
- normalizer for message, thread, and interaction events;
- Trimble Model Gateway / `gpt-5.4`;
- Code node for evidence validation and per-thread static state;
- CardsV2 answer with an optional `Draft an issue` action;
- confirmed interaction branch to the shared issue service;
- no credentials, Chat keys, or GitHub tokens in the export.

Bind these after import:

| Placeholder | Value |
| --- | --- |
| `TRIMBLE_MODEL_GATEWAY_CREDENTIAL` | Trimble Identity credential |
| `MODUS_MCP_ENDPOINT` | approved component-docs MCP |
| `ISSUE_SERVICE_URL` | shared issue service or n8n sub-workflow |
| `ISSUE_SERVICE_TOKEN` | n8n credential-backed bearer token |
| `MODUS_REPO` | `trimble-oss/modus-wc-2.0` |

## Example answer

For a question such as “does text input already support read-only?” the bot
should answer with the property name, the manifest/MCP source, and a link to
the component documentation. If the follow-up is “select should have the same
state,” it should explain whether the inspected select source has that
capability, identify the new API/design decision, and offer a draft issue. It
should not silently create a read-only select ticket.

## Safety cases

| Case | Required result |
| --- | --- |
| No mention / unauthorized user | Ignore or reject before model call |
| Ambiguous pronoun in thread | Ask the user to identify component/state |
| MCP timeout | Disclose missing source; do not claim capability |
| Conflicting manifest and prose | Cite both and escalate to human |
| Existing matching issue | Link it; no duplicate draft |
| Work implied but no user confirmation | Answer and offer draft only |
| Replayed confirmation | Do not call issue service twice |
| Issue Scaffolding clarification | Relay exact questions to the thread |
| Process/meta question | Answer with workflow guidance; no issue |

## Acceptance tests

1. Known property question returns a source citation and no issue call.
2. Existing issue question returns the issue URL and current status.
3. Missing capability request offers a draft but does not create it.
4. Confirmed draft calls the shared service once with `autoApprove: false`.
5. A replayed card action is idempotent.
6. A source timeout produces a transparent gap response.
7. A short thread reference is resolved from the recent context or becomes a
   clarification question.

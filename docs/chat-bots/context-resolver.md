# Private repository context resolver

The Chat bots do not automatically see the repository. This resolver is the
explicit evidence boundary between a Chat message and an AI answer.

**Pilot repository:** `ElishaSamPeterPrabhu/modus-wc-2.0`  
**Workflow template:** [`workflows/context-resolver.template.json`](workflows/context-resolver.template.json)

## Request

```json
{
  "componentName": "modus-wc-text-input",
  "query": "readOnly",
  "property": "readOnly",
  "state": "readonly",
  "includeSiblings": true
}
```

At least one of `componentName`, `query`, `property`, or `state` is required.

## Response

```json
{
  "ok": true,
  "repository": "ElishaSamPeterPrabhu/modus-wc-2.0",
  "source": {
    "manifest": "src/custom-elements.json",
    "commit": "..."
  },
  "matches": [
    {
      "tag": "modus-wc-text-input",
      "property": "readOnly",
      "supported": true,
      "source": "src/custom-elements.json#/modules/..."
    }
  ],
  "notFound": [],
  "warning": null
}
```

An empty `matches` array is an explicit source result. It is not permission to
infer support from a sibling or from model memory.

## Usage

Ticket Bot, Q&A Bot, Design-Research, and Issue Scaffolding call this resolver
before making a capability claim. The resolver reads the private GitHub
manifest with a credential-backed request and returns only the relevant
declarations, limiting prompt size. It never creates issues or writes to the
repository.

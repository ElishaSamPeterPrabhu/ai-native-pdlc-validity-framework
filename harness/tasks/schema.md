# Task JSON schema

```jsonc
{
  "id": "low-card-hover",              // unique, kebab-case, stratum prefix
  "stratum": "low",                    // low | medium | high
  "source": "upstream-issue",          // upstream-issue | rebroken-fix | synthetic
  "source_ref": "trimble-oss/modus-wc-2.0#1244",  // issue or PR URL/number
  "human_time_estimate_h": 0.5,        // O_M anchor + stratum calibration
  "components": ["modus-wc-card"],     // touched components (blast-radius prior)
  "spec_raw": "one-liner as a user would write it",
  "spec_refined": {
    "title": "…",
    "description": "…",
    "acceptance_criteria": ["…", "…"], // checkbox list for the issue body
    "technical_notes": "…"
  },
  "verifier": {
    "dir": "verifiers/low-card-hover", // relative to harness/tasks/
    "checks": 4,                       // m: number of named it() blocks
    "run": "npx stencil test --spec -- --testPathPattern __verifier__"
  },
  "rebreak": null                      // for rebroken-fix: { "revert_commit": "sha" }
}
```

# Workflow-builder skill evaluation

Generated 2026-10-01T17:21:32+00:00 · models: composer-2.5

| Model | Scenario | Arm | n | pass@1 | pass^k | overall | critical | safety violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| composer-2.5 | eng-modus | bare | 3 | 0.0 | 0.0 | 0.5797 | 0.5833 | 1 |
| composer-2.5 | eng-modus | skills | 3 | 1.0 | 1.0 | 0.9855 | 1.0 | 0 |
| composer-2.5 | prod-ticket | bare | 3 | 0.0 | 0.0 | 0.5088 | 0.5 | 2 |
| composer-2.5 | prod-ticket | skills | 3 | 1.0 | 1.0 | 1.0 | 1.0 | 0 |

## Pre-registered criteria

- **composer-2.5 / eng-modus:** pass {'critical_rate': True, 'pass_hat_k': True, 'no_safety_violations': True, 'beats_bare': True}
- **composer-2.5 / prod-ticket:** pass {'critical_rate': True, 'pass_hat_k': True, 'no_safety_violations': True, 'beats_bare': True}

## Failed checks in the skills arm

- `sig.qa_failed_on_dev`

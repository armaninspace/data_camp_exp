# Question Generation V4 Bundle for Codex

This bundle contains the V4 policy-layer handoff.

## Files

1. `question_gen_v4_policy_vision.md`
   - high-level policy vision
   - candidate classes
   - curation, serving, alias, and retention rules

2. `question_gen_v4_codex_handoff.md`
   - implementation-ready handoff for Codex
   - modules, models, acceptance criteria, outputs

3. `question_gen_v4_policy_config.yaml`
   - default policy thresholds and bucket rules

4. `question_gen_v4_policy_diagram.md`
   - Mermaid diagram of the policy flow

## Intended architecture

V4 is a policy layer **on top of V3**.

Recommended flow:

```text
V3 extraction/generation/scoring
-> V4 family tagging
-> V4 canonicalization
-> V4 serving decision
-> V4 curation decision
-> V4 bucket assignment
-> cache + retention + telemetry
```

## Key policy idea

Do not collapse everything into `selected` vs `rejected`.

Use:
- `curated_core`
- `cache_servable`
- `alias_only`
- `analysis_only`
- `hard_reject`

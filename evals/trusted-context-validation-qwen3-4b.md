# Trusted Context Validation - qwen3:4b

## Purpose

This evaluation records the addition of schema validation for trusted requirement context files.

The workflow already validated model output, enriched output, semantic grounding, negative cases, multi-context regression, and run reports.

The remaining gap was that the trusted context JSON files themselves were treated as valid by assumption.

## Added Files

```text
schemas/requirements-context.schema.json
scripts/validate_context.py
```

## Updated Files

```text
contexts/production-report-context.json
contexts/review-moderation-context.json
schemas/run-report.schema.json
scripts/run_demo_multi_context_workflow.py
```

## Context Files Validated

```text
contexts/production-report-context.json
contexts/review-moderation-context.json
contexts/payment-webhook-context.json
```

## Direct Validation Command

```powershell
python .\scripts\validate_context.py .\contexts\production-report-context.json .\contexts\review-moderation-context.json .\contexts\payment-webhook-context.json
```

## Expected Result

```text
PASS: 3 trusted context file(s) match the schema.
```

## Demo Workflow Integration

The reproducible demo workflow now validates all discovered context files before prompt generation.

Expected workflow step:

```text
STEP: Validate trusted context files
------------------------------------
PASS: 3 trusted context file(s) match the schema.
```

## Issue Found

The new schema initially failed for older contexts because they did not include:

```text
requirement_name
summary
```

Those fields were added to the older context files instead of weakening the schema.

## Why This Matters

The trusted context is the semantic source of truth for the workflow.

If the context itself is malformed, incomplete, or inconsistent, then prompt generation, enrichment, and semantic validation can all become unreliable.

This update makes the trust chain stricter:

```text
trusted context schema validation
→ prompt generation
→ local LLM generation
→ malformed JSON repair fallback
→ normalization
→ trusted-context enrichment
→ output schema validation
→ semantic validation
→ regression tests
→ run-report validation
```

## Result

The full demo workflow passed after context validation was added.

```text
DEMO MULTI-CONTEXT WORKFLOW RESULT: PASS
```

## Significance

The project now validates both sides of the workflow:

```text
input truth source
generated/enriched output
```

This makes the system more production-aware and reduces the risk of trusting malformed context files.
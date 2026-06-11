# Second Context Validation - Review Moderation Dashboard - qwen3:4b

## Purpose

This evaluation records the first successful reuse of the context-driven workflow on a second requirement context.

The first implemented context was a report-style requirement. This second context is intentionally different:

- UI/admin workflow instead of report generation
- long-text display concern instead of aggregation logic
- review-status update workflow instead of date-filtered totals
- unknown authorization and filter rules instead of unknown source tables and summation fields

This helps prove that semantic validation v3 is not tied to one hardcoded requirement.

## Requirement Context

Context file:

```text
contexts/review-moderation-context.json
```

Anonymized requirement:

```text
An internal admin user needs a dashboard to review user-submitted feedback. The list must show long feedback text in a readable way without breaking the layout. Admin users should be able to filter records, inspect full feedback content, and update review status.
```

No client, company, product, or real field names are used.

## Model

```text
qwen3:4b
```

Run locally through Ollama.

## Workflow Under Test

```text
trusted context JSON
-> generated prompt
-> Ollama API
-> raw model JSON
-> normalize
-> enrich from trusted context
-> schema validation
-> context-driven semantic validation v3
-> PASS/FAIL
```

## Full Workflow Command

```powershell
python .\scripts\run_ollama_requirements_workflow.py --model qwen3:4b --context .\contexts\review-moderation-context.json --generated-prompt-output .\scratch\review-moderation-generated-prompt.txt --generated-output .\scratch\review-moderation-generated-output.json --normalized-output .\scratch\review-moderation-normalized-output.json --enriched-output .\scratch\review-moderation-enriched-output.json
```

## Full Workflow Result

```text
STEP: Build prompt from trusted context
---------------------------------------
Generated prompt written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\review-moderation-generated-prompt.txt

STEP: Generate output with Ollama
---------------------------------
Generated output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\review-moderation-generated-output.json

STEP: Normalize and enrich generated output
-------------------------------------------

STEP: Normalize model output
----------------------------
Normalized output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\review-moderation-normalized-output.json

STEP: Enrich normalized output
------------------------------
Enriched output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\review-moderation-enriched-output.json

WORKFLOW RESULT: PASS
Normalized output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\review-moderation-normalized-output.json
Enriched output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\review-moderation-enriched-output.json

STEP: Validate enriched output with pipeline v3
-----------------------------------------------
Running schema validation...
PASS: Model output matches the schema.
Running semantic validation v3...
SEMANTIC VALIDATION V3 RESULT: PASS
PIPELINE V3 RESULT: PASS

OLLAMA WORKFLOW RESULT: PASS
```

## Regression Command

```powershell
python .\scripts\run_validation_v3_regression_tests.py .\scratch\review-moderation-enriched-output.json .\contexts\review-moderation-context.json
```

## Regression Result

```text
STEP: Positive validation test
------------------------------
Running schema validation...
PASS: Model output matches the schema.
Running semantic validation v3...
SEMANTIC VALIDATION V3 RESULT: PASS
PIPELINE V3 RESULT: PASS

STEP: Negative validation tests
-------------------------------
Writing negative fixtures to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\v3-negative-tests
[PASS] missing-required-fact: rejected as expected.
[PASS] invalid-status: rejected as expected.
[PASS] blocked-without-depends-on: rejected as expected.
[PASS] invalid-hallucination-result: rejected as expected.
[PASS] invented-db-engine: rejected as expected.
[PASS] invented-frontend-framework: rejected as expected.
[PASS] unsupported-implementation-estimate: rejected as expected.
[PASS] fake-sample-value: rejected as expected.
NEGATIVE TEST RESULT: PASS

REGRESSION TEST RESULT: PASS
```

## Raw Model Output Quality

The raw model output was weak.

It captured some facts and unknowns, but failed to produce the full required structure. It also leaked explanatory text into a malformed JSON key around the `client_questions` section.

This is useful evidence for the project because it reinforces the main design claim:

```text
LLM output should not be trusted directly.
```

## Normalized Output Quality

Normalization repaired the output into a schema-safe shape.

However, the normalized output still had empty semantic sections such as:

- client_questions
- backend_tasks
- frontend_tasks
- database_considerations
- test_cases
- hallucination_checks

This shows the normalizer is doing the correct limited job:

```text
fix structure, not meaning
```

## Enriched Output Quality

Trusted-context enrichment filled the missing semantic content.

The enriched output included:

- required facts
- required unknowns
- client questions
- backend tasks
- frontend tasks
- database considerations
- test cases
- hallucination checks

A small duplication issue was found in `client_questions`, where fallback questions were added even when the context already contained proper questions.

That issue was fixed in `scripts/enrich_model_output.py` by checking whether existing questions already cover each unknown before adding fallback questions.

After the fix, the enriched output contained only the intended context-backed client questions.

## What This Proves

This second context proves that the workflow is not limited to the original report requirement.

The same system can process a different kind of requirement:

```text
admin review workflow
```

using the same architecture:

```text
context -> prompt -> model -> normalize -> enrich -> validate
```

## Current Limitation

This is still not full generalization.

The workflow has now been tested on two contexts, but both contexts are hand-written structured JSON files.

The next stronger proof would be either:

1. add a third requirement context, or
2. start building retrieval/input parsing so the context can be created from real requirement documents, tickets, emails, or PDFs.
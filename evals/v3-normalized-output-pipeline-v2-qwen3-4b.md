# V3 Normalized Output Pipeline V2 - Qwen3 4B

## Purpose

This file records the result of running deterministic schema normalization on a failed semantic-repair output.

The goal was to test this flow:

```text
near-valid model JSON → deterministic normalizer → schema validation → pipeline v2 validation
```

## Model

qwen3:4b

## Input File

```text
model-outputs/v3-semantic-repaired-v2-qwen3-4b-output.json
```

## Normalized Output File

```text
model-outputs/v3-semantic-repaired-v2-normalized-qwen3-4b-output.json
```

## Scripts Used

```text
scripts/normalize_model_output.py
scripts/validate_model_output.py
scripts/validate_pipeline_v2.py
```

## Normalization Command

```powershell
python .\scripts\normalize_model_output.py .\model-outputs\v3-semantic-repaired-v2-qwen3-4b-output.json .\model-outputs\v3-semantic-repaired-v2-normalized-qwen3-4b-output.json
```

## Normalization Result

```text
Normalized output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\v3-semantic-repaired-v2-normalized-qwen3-4b-output.json
```

## Schema Validation Command

```powershell
python .\scripts\validate_model_output.py .\model-outputs\v3-semantic-repaired-v2-normalized-qwen3-4b-output.json
```

## Schema Validation Result

```text
PASS: Model output matches the schema.
```

## Pipeline V2 Command

```powershell
python .\scripts\validate_pipeline_v2.py .\model-outputs\v3-semantic-repaired-v2-normalized-qwen3-4b-output.json
```

## Pipeline V2 Result

```text
STEP 1: Schema validation
-------------------------
PASS: Model output matches the schema.

STEP 2: Semantic validation v2
------------------------------
FAIL: Semantic validation v2 found blocking issues.

Failures:
1. facts_used does not mention required fact term: summed
2. unknowns does not mention required unknown: source tables
3. unknowns does not mention required unknown: summation field
4. hallucination_checks is empty.
5. There are blocked items, but unknowns is empty.

Warnings:
1. hallucination_checks has fewer than 2 checks; risk coverage is weak.

PIPELINE V2 RESULT: FAIL
Reason: Semantic validation v2 failed.
```

## What Passed

| Area                    | Result | Notes                                                                                 |
| ----------------------- | ------ | ------------------------------------------------------------------------------------- |
| JSON parsing            | Pass   | The normalized file is valid JSON.                                                    |
| Schema validation       | Pass   | The normalizer fixed predictable structure issues.                                    |
| Required top-level keys | Pass   | Missing schema keys were added.                                                       |
| Required object fields  | Pass   | Missing required fields were added where possible.                                    |
| Field name repair       | Pass   | Invalid fields like `name` were normalized to schema fields such as `task` or `item`. |

## What Failed

| Issue                                       | Why It Matters                                          |
| ------------------------------------------- | ------------------------------------------------------- |
| Missing `summed` fact                       | The output does not preserve the summation requirement. |
| Missing `source tables` unknown             | The output loses an important blocker.                  |
| Missing `summation field` unknown           | The output loses another important blocker.             |
| Empty `hallucination_checks`                | The output lacks explicit risk checks.                  |
| Blocked items exist but `unknowns` is empty | The output is internally inconsistent.                  |

## Key Learning

Deterministic normalization is useful, but it only fixes structure.

It should not be expected to add missing meaning unless it is given trusted source context.

This proves the difference between:

```text
schema normalization
semantic enrichment
```

## Production Lesson

A production-grade LLM workflow should not rely only on the model output when repairing semantics.

The system should preserve and reuse trusted input context, such as:

* known facts
* known unknowns
* expected required fields
* domain rules
* blocked implementation areas

Then the system can enrich or validate the model output against that trusted context.

## Current Verdict

The deterministic normalizer successfully fixed schema structure.

The normalized output is still rejected by pipeline v2 because the semantic content is incomplete.

## Next Improvement Target

Add a trusted requirement-context file and then build an enrichment step that uses that context to fill required semantic gaps before running pipeline v2 again.

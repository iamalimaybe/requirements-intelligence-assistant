# V3 Pipeline Validation - Qwen3 4B

## Purpose

This file records the validation pipeline result for the first semantic repair attempt.

The goal is to enforce the correct validation order:

```text
JSON parsing → schema validation → semantic validation
```

Semantic validation should only run after schema validation passes.

## Model

qwen3:4b

## Input File

```text
model-outputs/v3-semantic-repaired-qwen3-4b-output.json
```

## Pipeline Script

```text
scripts/validate_pipeline.py
```

## Command Used

```powershell
python .\scripts\validate_pipeline.py .\model-outputs\v3-semantic-repaired-qwen3-4b-output.json
```

## Pipeline Output

```text
STEP 1: Schema validation
-------------------------
FAIL: Model output does not match the schema.

1. Path: $
   Error: 'test_cases' is a required property

2. Path: $
   Error: 'hallucination_checks' is a required property

3. Path: $.backend_tasks.0
   Error: Additional properties are not allowed ('name' was unexpected)

4. Path: $.backend_tasks.0
   Error: 'task' is a required property

5. Path: $.database_considerations.0
   Error: Additional properties are not allowed ('name' was unexpected)

6. Path: $.database_considerations.0
   Error: 'item' is a required property

7. Path: $.database_considerations.1
   Error: Additional properties are not allowed ('name' was unexpected)

8. Path: $.database_considerations.1
   Error: 'item' is a required property

9. Path: $.frontend_tasks.0
   Error: Additional properties are not allowed ('name' was unexpected)

10. Path: $.frontend_tasks.0
   Error: 'task' is a required property

PIPELINE RESULT: FAIL
Reason: Schema validation failed. Semantic validation was skipped.
```

## What This Proves

The previous standalone semantic validation result was misleading because the output failed schema validation first.

The pipeline fixed that by enforcing this rule:

```text
Do not run semantic validation unless schema validation passes.
```

## Key Learning

Validation order matters.

A production-grade LLM system should not treat each validator independently. Validators should be chained in the correct order, and later validators should assume earlier validators already passed.

## Current Verdict

The validation pipeline is working correctly.

The semantic repair output is rejected because it is not schema-compliant.

## Next Improvement Target

Repair the semantic-repair output structurally, then run the full pipeline again.

The target flow is:

```text
semantic-repaired output → schema repair → pipeline validation → pass/fail
```

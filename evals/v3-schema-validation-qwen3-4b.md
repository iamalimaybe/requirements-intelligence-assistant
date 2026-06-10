# V3 Schema Validation - Qwen3 4B

## Purpose

This file records automated schema validation results for the Qwen3 4B output generated from Prompt V3.

The goal is to prove that model output should not be trusted only because it appears structured or valid JSON. In production-grade LLM systems, output must be validated before it is used by downstream code.

## Model

qwen3:4b

## Prompt Version

requirements-analysis-v3

## Input File

```text
model-outputs/v3-qwen3-4b-output.json
```

## Schema File

```text
schemas/requirements-analysis.schema.json
```

## Validation Script

```text
scripts/validate_model_output.py
```

## Command Used

```powershell
python .\scripts\validate_model_output.py .\model-outputs\v3-qwen3-4b-output.json
```

## Validation Result

```text
FAIL: Model output does not match the schema.

1. Path: $
   Error: Additional properties are not allowed ('frontend_task' was unexpected)

2. Path: $
   Error: 'facts_used' is a required property

3. Path: $
   Error: 'unknowns' is a required property

4. Path: $
   Error: 'client_questions' is a required property

5. Path: $
   Error: 'backend_tasks' is a required property

6. Path: $
   Error: 'frontend_tasks' is a required property

7. Path: $.database_considerations.0
   Error: 'depends_on' is a required property

8. Path: $.database_considerations.1
   Error: 'depends_on' is a required property

9. Path: $.test_cases.0
   Error: 'depends_on' is a required property
```

## What Failed

| Issue                                                    | Why It Matters                                                                         |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `frontend_task` was returned instead of `frontend_tasks` | The model renamed a required field, which would break parser code.                     |
| Required top-level keys were missing                     | The output is incomplete and cannot be treated as a full requirements analysis result. |
| `backend_tasks` was missing                              | The model skipped one of the most important output sections.                           |
| `depends_on` was missing from multiple objects           | Dependency tracking is required to know what is blocked versus ready.                  |
| Additional properties were returned                      | The output does not match the strict contract expected by the application.             |

## Key Learning

Prompt instructions alone are not reliable enough.

Even when the model is told to return an exact schema, it may:

* rename fields
* omit required fields
* change arrays into objects
* drop sections
* skip dependency fields
* return incomplete planning output

## Production Lesson

A production-grade LLM system should treat model output as untrusted.

The application should:

1. validate the model output
2. reject invalid output
3. collect validation errors
4. retry with a repair prompt or fallback strategy
5. only pass validated output to downstream business logic

## Current Verdict

Prompt V3 failed automated schema validation.

This is not a dead end. It gives the project a stronger direction: the system needs validation and repair logic, not just better prompting.

## Next Improvement Target

The next step should be to introduce a validation-first repair flow:

1. Generate model output.
2. Validate against JSON Schema.
3. If validation fails, send the original output plus validation errors to a repair prompt.
4. Validate repaired output again.
5. Accept only if the repaired output passes schema validation.

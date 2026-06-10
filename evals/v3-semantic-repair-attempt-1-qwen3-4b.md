# V3 Semantic Repair Attempt 1 - Qwen3 4B

## Purpose

This file records the first attempt to semantically repair the schema-valid but low-quality repaired output.

The goal was to produce output that passes both:

```text
scripts/validate_model_output.py
scripts/semantic_validate_model_output.py
```

## Model

qwen3:4b

## Prompt Version

requirements-analysis-semantic-repair-v1

## Input File

```text
model-outputs/v3-repaired-qwen3-4b-output.json
```

## Output File

```text
model-outputs/v3-semantic-repaired-qwen3-4b-output.json
```

## Runtime Notes

* Response time: 52.4 seconds
* Context window setting: 4K
* Interface used: Ollama UI
* Model storage path: D:\AI_LOCAL\ollama-models

## Raw Model Output

```json
{
  "facts_used": [
    "Frontend already has a hierarchy agent endpoint"
  ],
  "unknowns": [
    "source tables for the report",
    "exact field name for the metric to be summed"
  ],
  "client_questions": [
    "What are the source tables for the Production Report?",
    "What is the exact field to sum for the Production Report?"
  ],
  "backend_tasks": [
    {
      "name": "Define input contract for Production Report",
      "status": "ready",
      "reason": "Frontend passes companyCode, hierarchyAgent, startDate, and endDate",
      "depends_on": []
    }
  ],
  "frontend_tasks": [
    {
      "name": "Pass selected hierarchyAgent and date range (startDate, endDate) to backend",
      "status": "ready",
      "reason": "Frontend passes hierarchyAgent and date range (startDate, endDate) to backend",
      "depends_on": []
    }
  ],
  "database_considerations": [
    {
      "name": "Source tables for the report",
      "status": "blocked",
      "reason": "Not provided by client",
      "depends_on": [
        "source tables for the report"
      ]
    },
    {
      "name": "Exact field name for the metric to be summed",
      "status": "blocked",
      "reason": "Not provided by client",
      "depends_on": [
        "exact field name for the metric to be summed"
      ]
    }
  ]
}
```

## Schema Validation Command

```powershell
python .\scripts\validate_model_output.py .\model-outputs\v3-semantic-repaired-qwen3-4b-output.json
```

## Schema Validation Result

```text
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
```

## Semantic Validation Command

```powershell
python .\scripts\semantic_validate_model_output.py .\model-outputs\v3-semantic-repaired-qwen3-4b-output.json
```

## Semantic Validation Result

```text
PASS: Semantic validation found no issues.
```

## Important Finding

The semantic validation result is misleading because the output failed schema validation first.

The semantic validator assumes that the input already has the correct structure. Since this output did not pass schema validation, semantic validation should not have been treated as meaningful.

## What Improved

| Area                | Result   | Notes                                                        |
| ------------------- | -------- | ------------------------------------------------------------ |
| `facts_used`        | Improved | It is no longer empty.                                       |
| `unknowns`          | Improved | It now identifies missing source tables and summation field. |
| `client_questions`  | Improved | It asks useful questions for the missing information.        |
| `reason` fields     | Improved | Reasons are no longer empty.                                 |
| `depends_on` fields | Improved | Blocked items now have dependency values.                    |

## What Failed

| Issue                                                    | Why It Matters                                       |
| -------------------------------------------------------- | ---------------------------------------------------- |
| `test_cases` missing                                     | Required by schema.                                  |
| `hallucination_checks` missing                           | Required by schema.                                  |
| Used `name` instead of `task` in task sections           | Breaks parser contract.                              |
| Used `name` instead of `item` in database considerations | Breaks parser contract.                              |
| Schema validation failed                                 | Output cannot be consumed safely by downstream code. |
| Semantic validation gave a pass despite schema failure   | Shows need for a validation pipeline.                |

## Key Learning

Validation order matters.

The correct order is:

```text
JSON parsing → schema validation → semantic validation
```

Semantic validation should only run if schema validation passes.

## Current Verdict

Semantic Repair Attempt 1 improved content quality but broke the schema.

This output should be rejected.

## Next Improvement Target

Add a validation pipeline script that:

1. runs schema validation first
2. stops immediately if schema validation fails
3. only runs semantic validation after schema validation passes
4. returns one clear pass/fail result

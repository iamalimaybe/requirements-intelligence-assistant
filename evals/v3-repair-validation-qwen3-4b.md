# V3 Repair Validation - Qwen3 4B

## Purpose

This file records the result of repairing invalid Qwen3 4B output using a repair prompt and validating the repaired output against the project JSON Schema.

The goal is to test a production-style flow:

```text
model output → schema validation → validation failure → repair prompt → repaired output → schema validation
```

## Model

qwen3:4b

## Original Prompt Version

requirements-analysis-v3

## Repair Prompt Version

requirements-analysis-repair-v1

## Input File

```text
model-outputs/v3-qwen3-4b-output.json
```

## Repaired Output File

```text
model-outputs/v3-repaired-qwen3-4b-output.json
```

## Schema File

```text
schemas/requirements-analysis.schema.json
```

## Validation Script

```text
scripts/validate_model_output.py
```

## Runtime Notes

* Repair response time: 35.7 seconds
* Context window setting: 4K
* Interface used: Ollama UI
* Model storage path: D:\AI_LOCAL\ollama-models

## Repaired Model Output

```json
{
  "facts_used": [],
  "unknowns": [],
  "client_questions": [],
  "backend_tasks": [],
  "frontend_tasks": [
    {
      "task": "Pass selected hierarchyAgent and date range to report endpoint",
      "status": "ready",
      "reason": "",
      "depends_on": []
    }
  ],
  "database_considerations": [
    {
      "item": "Source tables for the report",
      "status": "blocked",
      "reason": "Not provided by client",
      "depends_on": []
    },
    {
      "item": "Exact field name for the metric to be summed",
      "status": "blocked",
      "reason": "Not provided by client",
      "depends_on": []
    }
  ],
  "test_cases": [
    {
      "name": "Basic query test",
      "status": "blocked",
      "given": "companyCode = <company_code>, hierarchyAgent = <hierarchy_agent>, startDate = <start_date>, endDate = <end_date>",
      "expected": "Sum of metric field for specified company and hierarchy agent within date range",
      "depends_on": []
    }
  ],
  "hallucination_checks": [
    {
      "check": "Source tables for the report are known",
      "result": "blocked",
      "notes": "Source tables not provided by client"
    },
    {
      "check": "Exact metric field name is known",
      "result": "blocked",
      "notes": "Exact metric field name not provided by client"
    }
  ]
}
```

## Validation Command

```powershell
python .\scripts\validate_model_output.py .\model-outputs\v3-repaired-qwen3-4b-output.json
```

## Validation Result

```text
PASS: Model output matches the schema.
```

## What Improved

| Area                         | Result | Notes                                               |
| ---------------------------- | ------ | --------------------------------------------------- |
| Valid JSON                   | Pass   | The repaired output is parseable JSON.              |
| Required top-level keys      | Pass   | Missing keys from V3 were added.                    |
| Wrong field name fixed       | Pass   | `frontend_task` was repaired into `frontend_tasks`. |
| Required `depends_on` fields | Pass   | Missing dependency arrays were added.               |
| Schema validation            | Pass   | The repaired output now satisfies the JSON Schema.  |

## Remaining Quality Problems

| Issue                                            | Why It Matters                                                                                |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `facts_used` is empty                            | The repaired output is structurally valid but loses traceability to the original requirement. |
| `unknowns` is empty                              | This is semantically wrong because source tables and summation field are still unknown.       |
| `client_questions` is empty                      | The repaired output should probably ask for source tables and summation field.                |
| `backend_tasks` is empty                         | The output avoids bad assumptions, but it also removes useful planning tasks.                 |
| `reason` is empty for the frontend task          | The schema allows it, but the content quality is weak.                                        |
| `depends_on` is empty for blocked database items | This passes structurally, but dependency tracking is not very informative.                    |
| “report endpoint” is still generic               | It does not invent a path, but endpoint existence is still not explicitly provided.           |

## Manual Evaluation

### Accuracy

Score: 2.5 / 5
Notes:
The repaired output is safer than the invalid V3 output, but it loses useful analysis. It correctly preserves the frontend task and blocked database considerations, but omits facts, unknowns, questions, and backend planning.

### Grounding

Score: 3 / 5
Notes:
The output is mostly conservative and avoids many hallucinations. However, empty `facts_used` and `unknowns` reduce traceability.

### Hallucination Risk

Score: 3.5 / 5
Notes:
The output has lower hallucination risk because it avoids invented tables, engines, frameworks, and sample values. The tradeoff is that it becomes under-informative.

### Structure / Format

Score: 5 / 5
Notes:
The repaired output passes automated schema validation.

### Usefulness for Software Requirements Analysis

Score: 2.5 / 5
Notes:
The output is safe to parse but not very useful yet. It proves the repair flow can fix structure, but quality controls are still needed.

## Key Learning

Schema validation is necessary but not sufficient.

A model output can be:

```text
valid JSON + schema compliant + still low quality
```

This means the system needs two validation layers:

1. **Structural validation**
   Checks JSON shape, required keys, required fields, and allowed enum values.

2. **Semantic validation**
   Checks whether the content is useful, grounded, non-empty where expected, and aligned with the task.

## Current Verdict

The repair flow successfully fixed schema compliance.

However, the repaired output is not yet good enough as a final requirements-analysis result. The next improvement should add semantic validation checks after schema validation.

## Next Improvement Target

Add lightweight semantic checks for:

* empty `facts_used`
* empty `unknowns` when blockers mention unknown information
* empty `client_questions` when unknowns exist
* empty `backend_tasks` for implementation-planning outputs
* empty `reason` fields
* blocked items with empty `depends_on`

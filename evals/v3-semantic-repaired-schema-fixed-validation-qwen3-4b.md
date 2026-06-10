# V3 Semantic Repaired Schema-Fixed Validation - Qwen3 4B

## Purpose

This file records the validation result after repairing the first semantic-repair output so that it matches the project schema.

The target flow was:

```text
semantic-repaired output → schema repair → pipeline validation
```

## Model

qwen3:4b

## Prompt Chain

```text
requirements-analysis-v3
→ requirements-analysis-repair-v1
→ requirements-analysis-semantic-repair-v1
→ requirements-analysis-repair-v1
```

## Output File

```text
model-outputs/v3-semantic-repaired-schema-fixed-qwen3-4b-output.json
```

## Pipeline Script

```text
scripts/validate_pipeline.py
```

## Runtime Notes

* Schema-fix repair response time: 47.5 seconds
* Context window setting: 4K
* Interface used: Ollama UI
* Model storage path: D:\AI_LOCAL\ollama-models

## Final Model Output

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
      "task": "Define input contract for Production Report",
      "status": "ready",
      "reason": "Frontend passes companyCode, hierarchyAgent, startDate, and endDate",
      "depends_on": []
    }
  ],
  "frontend_tasks": [
    {
      "task": "Pass selected hierarchyAgent and date range (startDate, endDate) to backend",
      "status": "ready",
      "reason": "Frontend passes hierarchyAgent and date range (startDate, endDate) to backend",
      "depends_on": []
    }
  ],
  "database_considerations": [
    {
      "item": "Source tables for the report",
      "status": "blocked",
      "reason": "Not provided by client",
      "depends_on": [
        "source tables for the report"
      ]
    },
    {
      "item": "Exact field name for the metric to be summed",
      "status": "blocked",
      "reason": "Not provided by client",
      "depends_on": [
        "exact field name for the metric to be summed"
      ]
    }
  ],
  "test_cases": [],
  "hallucination_checks": []
}
```

## Pipeline Command

```powershell
python .\scripts\validate_pipeline.py .\model-outputs\v3-semantic-repaired-schema-fixed-qwen3-4b-output.json
```

## Pipeline Result

```text
STEP 1: Schema validation
-------------------------
PASS: Model output matches the schema.

STEP 2: Semantic validation
---------------------------
PASS: Semantic validation found no issues.
PIPELINE RESULT: PASS
```

## What Improved

| Area                    | Result   | Notes                                                       |
| ----------------------- | -------- | ----------------------------------------------------------- |
| Schema validation       | Pass     | Output now matches the JSON Schema.                         |
| Pipeline validation     | Pass     | Schema validation passed, then semantic validation passed.  |
| Field names             | Pass     | `name` was fixed to `task` / `item`.                        |
| Required top-level keys | Pass     | `test_cases` and `hallucination_checks` were added.         |
| Unknowns                | Improved | Missing source tables and summation field are now captured. |
| Client questions        | Improved | Questions now directly map to unknowns.                     |
| Dependency tracking     | Improved | Blocked database considerations now have `depends_on`.      |

## Remaining Quality Problems

| Issue                                          | Why It Matters                                                                                                                |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `facts_used` contains only one fact            | The output does not fully trace back to all known requirement facts.                                                          |
| `test_cases` is empty                          | For a requirements-analysis assistant, test cases should usually exist, even if some are blocked.                             |
| `hallucination_checks` is empty                | The system loses explicit hallucination/risk self-checking.                                                                   |
| Backend tasks are too shallow                  | It defines the input contract, but does not include blocked tasks for applying `DATE_ADDED` filtering and summing the metric. |
| Semantic validator passed despite weak content | The semantic validator needs to be stricter.                                                                                  |

## Key Learning

The validation pipeline now works mechanically, but the semantic validation rules are still too permissive.

The current validator answers:

```text
Is the output structurally valid and not obviously empty in key places?
```

It does not yet fully answer:

```text
Is this output good enough for a requirements-analysis workflow?
```

## Current Verdict

The repair pipeline successfully produced output that passes both schema validation and the current semantic validation.

However, this should be treated as a technical pipeline milestone, not as final output quality.

## Next Improvement Target

Tighten semantic validation so that future outputs require:

* more complete `facts_used`
* non-empty `test_cases`
* non-empty `hallucination_checks`
* backend tasks for date filtering and summation, marked `blocked` if source tables or summation field are unknown
* stronger traceability between unknowns, client questions, blocked tasks, and dependencies

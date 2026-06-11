# V3 Semantic Repair V2 Attempt 1 - Qwen3 4B

## Purpose

This file records the first attempt using `requirements-analysis-semantic-repair-v2`.

The goal was to repair the previous output so it would pass:

```text
scripts/validate_pipeline_v2.py
```

## Model

qwen3:4b

## Prompt Version

```text
prompts/requirements-analysis-semantic-repair-v2.md
```

## Output File

```text
model-outputs/v3-semantic-repaired-v2-qwen3-4b-output.json
```

## Runtime Notes

* Response time: 65.6 seconds
* Context window setting: 4K
* Interface used: Ollama UI
* Model storage path: D:\AI_LOCAL\ollama-models

## Raw Model Output

```json
{
  "facts_used": [
    "Production Report is the report name.",
    "Frontend has a hierarchy agent endpoint.",
    "Frontend passes hierarchyAgent to the backend.",
    "Backend requires inputs: companyCode, hierarchyAgent, startDate, endDate.",
    "DATE_ADDED field is used for date filtering in the Production Report."
  ],
  "backend_tasks": [
    {
      "task": "Define the input contract for the Production Report",
      "status": "ready",
      "reason": "Frontend passes companyCode, hierarchyAgent, startDate, and endDate",
      "depends_on": []
    },
    {
      "task": "Apply DATE_ADDED filtering to the data",
      "status": "blocked",
      "reason": "Source tables and the exact summation field are unknown",
      "depends_on": [
        "source tables for the report",
        "exact field name for the metric to be summed"
      ]
    },
    {
      "task": "Sum the relevant fields to compute totals",
      "status": "blocked",
      "reason": "Source tables and the exact summation field are unknown",
      "depends_on": [
        "source tables for the report",
        "exact field name for the metric to be summed"
      ]
    }
  ],
  "frontend_tasks": [
    {
      "task": "Pass selected hierarchyAgent and date range (startDate, endDate) to backend",
      "status": "ready",
      "reason": "Frontend has a hierarchy agent endpoint",
      "depends_on": []
    }
  ],
  "database_considerations": [
    {
      "item": "source tables for the report",
      "status": "blocked"
    },
    {
      "item": "exact field name for the metric to be summed",
      "status": "blocked"
    }
  ],
  "test_cases": [
    {
      "name": "Test valid inputs",
      "given": "companyCode: 'example_company', hierarchyAgent: 'example_agent', startDate: '2023-01-01', endDate: '2023-12-31'",
      "expected": "Report generated"
    },
    {
      "name": "Test missing inputs",
      "given": "companyCode: '', hierarchyAgent: '', startDate: '', endDate: ''",
      "expected": "Error: Missing required inputs"
    }
  ]
}
```

## Pipeline Command

```powershell
python .\scripts\validate_pipeline_v2.py .\model-outputs\v3-semantic-repaired-v2-qwen3-4b-output.json
```

## Pipeline Result

```text
STEP 1: Schema validation
-------------------------
FAIL: Model output does not match the schema.

1. Path: $
   Error: 'unknowns' is a required property

2. Path: $
   Error: 'client_questions' is a required property

3. Path: $
   Error: 'hallucination_checks' is a required property

4. Path: $.database_considerations.0
   Error: 'reason' is a required property

5. Path: $.database_considerations.0
   Error: 'depends_on' is a required property

6. Path: $.database_considerations.1
   Error: 'reason' is a required property

7. Path: $.database_considerations.1
   Error: 'depends_on' is a required property

8. Path: $.test_cases.0
   Error: 'status' is a required property

9. Path: $.test_cases.0
   Error: 'depends_on' is a required property

10. Path: $.test_cases.1
   Error: 'status' is a required property

11. Path: $.test_cases.1
   Error: 'depends_on' is a required property

PIPELINE V2 RESULT: FAIL
Reason: Schema validation failed. Semantic validation v2 was skipped.
```

## What Improved

| Area                  | Result     | Notes                                                                                    |
| --------------------- | ---------- | ---------------------------------------------------------------------------------------- |
| `facts_used`          | Improved   | It now includes more of the known facts.                                                 |
| Backend task coverage | Improved   | It includes input contract, `DATE_ADDED` filtering, and summation tasks.                 |
| Blocked backend tasks | Improved   | It correctly marks tasks as blocked where source tables and summation field are unknown. |
| Frontend task         | Acceptable | It keeps frontend responsibility narrow.                                                 |

## What Failed

| Issue                                           | Why It Matters                                                                         |
| ----------------------------------------------- | -------------------------------------------------------------------------------------- |
| Missing `unknowns`                              | Required by schema and needed for traceability.                                        |
| Missing `client_questions`                      | Required by schema and needed to resolve blockers.                                     |
| Missing `hallucination_checks`                  | Required by schema and needed for risk tracking.                                       |
| Missing `reason` in database considerations     | Breaks schema and weakens explainability.                                              |
| Missing `depends_on` in database considerations | Breaks dependency tracking.                                                            |
| Missing `status` in test cases                  | Breaks schema and automation.                                                          |
| Missing `depends_on` in test cases              | Breaks dependency tracking.                                                            |
| Fake test values introduced                     | `example_company`, `example_agent`, and fixed dates violate the no-sample-values rule. |
| Missing summation fact in `facts_used`          | It mentions `DATE_ADDED` but does not clearly state totals should be summed.           |

## Key Learning

The semantic repair prompt improved content but broke schema compliance again.

This confirms that a small local model should not be trusted to reliably perform all of these at once:

```text
preserve schema
repair missing fields
improve semantic quality
avoid fake values
preserve all required sections
```

## Current Verdict

This output should be rejected.

The next improvement should not be another longer prompt. The next improvement should be a deterministic normalization step in code.

## Next Improvement Target

Add a deterministic schema normalizer that can:

* add missing top-level keys
* add missing required fields
* convert malformed objects into schema-shaped objects where possible
* preserve existing model content
* avoid pretending the output is semantically good
* then run pipeline validation again

# Controlled Prompt V3 Evaluation - Qwen3 4B

## Model

qwen3:4b

## Prompt Type

Controlled prompt contract with strict JSON schema preservation, no sample values, symbolic test cases, and hallucination checks.

## Runtime Notes

* Response time: 54.7 seconds
* Context window setting: 4K
* Interface used: Ollama UI
* Model storage path: D:\AI_LOCAL\ollama-models

## Prompt Source

```text
D:\AI_LOCAL\projects\requirements-intelligence-assistant\prompts\requirements-analysis-v3.md
```

## Raw Model Output

```json
{
  "frontend_task": {
    "status": "ready",
    "description": "Pass selected hierarchyAgent and date range to report endpoint"
  },
  "database_considerations": [
    {
      "item": "Source tables for the report",
      "status": "blocked",
      "reason": "Not provided by client"
    },
    {
      "item": "Exact field name for the metric to be summed",
      "status": "blocked",
      "reason": "Not provided by client"
    }
  ],
  "test_cases": [
    {
      "name": "Basic query test",
      "status": "blocked",
      "given": "companyCode = <company_code>, hierarchyAgent = <hierarchy_agent>, startDate = <start_date>, endDate = <end_date>",
      "expected": "Sum of metric field for specified company and hierarchy agent within date range"
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

## Manual Evaluation

### Accuracy

Score: 2.5 / 5
Notes:
The output correctly identifies that the source tables and summation field are unknown. It also correctly treats the basic query test as blocked. However, it omits backend tasks entirely and weakens the analysis by not preserving the known facts, unknowns, and client questions.

### Grounding

Score: 3.5 / 5
Notes:
The output is mostly grounded and does not invent table names, database engine, framework, or sample concrete values. However, it still uses “report endpoint,” even though no endpoint was provided. It also converts known facts into a reduced output instead of explicitly listing them.

### Hallucination Risk

Score: 3.5 / 5
Notes:
The hallucination risk is lower than the baseline because there are fewer invented details. However, the output is incomplete. Low hallucination is not enough if the model drops required fields and omits important planning sections.

### Structure / Format

Score: 1 / 5
Notes:
The output is valid JSON, but it fails the required schema badly. It changed `frontend_tasks` into `frontend_task`, used an object instead of an array, omitted required top-level keys, omitted `depends_on` fields, omitted backend tasks, and did not preserve the required object structure.

### Usefulness for Software Requirements Analysis

Score: 2 / 5
Notes:
The output is too incomplete for useful requirement analysis. It has some correct blockers, but it cannot be used for automation or serious evaluation because the schema is not stable.

## Schema Compliance Check

| Check                                                                 | Result  | Notes                                                                                               |
| --------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------------- |
| Valid JSON                                                            | Pass    | The output is parseable JSON.                                                                       |
| All top-level keys present                                            | Fail    | Missing `facts_used`, `unknowns`, `client_questions`, `backend_tasks`, and `frontend_tasks`.        |
| backend_tasks objects contain task/status/reason/depends_on           | Fail    | `backend_tasks` is completely missing.                                                              |
| frontend_tasks objects contain task/status/reason/depends_on          | Fail    | Model returned `frontend_task` as a single object with `description`, not `task/reason/depends_on`. |
| database_considerations objects contain item/status/reason/depends_on | Fail    | `depends_on` is missing.                                                                            |
| test_cases objects contain name/status/given/expected/depends_on      | Fail    | `depends_on` is missing.                                                                            |
| hallucination_checks objects contain check/result/notes               | Pass    | This section followed the required inner structure.                                                 |
| No invented table names                                               | Pass    | No table name was invented.                                                                         |
| No invented endpoint names                                            | Partial | It used generic “report endpoint,” but did not invent a concrete endpoint path.                     |
| No invented database engine                                           | Pass    | No database engine was invented.                                                                    |
| No invented framework                                                 | Pass    | No framework was invented.                                                                          |
| No invented sample values                                             | Pass    | It used symbolic placeholders instead of concrete fake values.                                      |
| No unsupported hierarchy traversal                                    | Pass    | It did not recommend hierarchy traversal.                                                           |

## Comparison Against V2

### Improved

* No invented concrete sample values such as `ABC` or `Manager_A`.
* No `Group by hierarchyAgent` task.
* No strong index recommendation.
* No unsupported hierarchy structure question.
* Lower volume of invented implementation details.

### Worse

* Failed the required schema more severely than V2.
* Omitted major top-level keys.
* Omitted backend tasks entirely.
* Changed `frontend_tasks` into `frontend_task`.
* Returned an incomplete frontend task object.
* Missed required `depends_on` fields.
* Took longer than V2: 54.7 seconds vs 51.8 seconds.

### Still Missing

* Reliable schema preservation.
* Complete backend task planning.
* Explicit unknowns.
* Explicit client questions.
* Proper dependency tracking.
* Automation-safe structure.

## Key Problems Found

* The model did not preserve the required top-level JSON schema.
* The model collapsed the frontend task structure.
* The model omitted backend tasks.
* The model omitted dependency tracking.
* The model followed the “be conservative” instruction but became too incomplete.
* The stricter prompt did not improve reliability; it made the output shorter but structurally worse.

## Current Verdict

Prompt V3 failed the main objective. It reduced some hallucination, but schema compliance became unacceptable. This shows that prompt-only control has limits on a 4B local model, especially when the schema is verbose.

## Next Improvement Target

The next step should be Prompt V4 with a smaller schema and stricter output contract. We should reduce the number of nested sections and make the model return a simpler structure that can later be validated by code.

The project should also introduce a JSON schema validator soon. In production-grade LLM systems, the model should not be trusted to follow schema perfectly. The application should validate the output, detect missing fields, and retry or repair the response.

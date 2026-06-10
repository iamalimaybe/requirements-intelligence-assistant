# Controlled Prompt V2 Evaluation - Qwen3 4B

## Model

qwen3:4b

## Prompt Type

Controlled prompt contract with strict JSON schema, task status, dependency tracking, and hallucination controls.

## Runtime Notes

* Response time: 51.8 seconds
* Context window setting: 4K
* Interface used: Ollama UI
* Model storage path: D:\AI_LOCAL\ollama-models

## Prompt

```text
You are a software requirements analyst.

Analyze only the requirement details provided below.

Rules:
- Do not invent table names, endpoint names, database engine, framework, sample values, or implementation estimates.
- Do not ask questions already answered by the provided facts.
- Do not recommend hierarchy traversal unless the input explicitly says the report must include child/downline agents.
- Do not use words like "critical", "non-negotiable", or "must" unless directly required by the facts.
- If a task depends on unknown data, mark it as "blocked".
- If a task can be planned without unknown data, mark it as "ready".
- Every backend task must include "status", "reason", and "depends_on".
- Return valid JSON only.

Known facts:
- Report name: Production Report.
- Frontend already has a hierarchy agent endpoint.
- Frontend will pass the selected hierarchyAgent to the report.
- Backend report inputs are companyCode, hierarchyAgent, startDate, endDate.
- Date filtering should use DATE_ADDED.
- Totals should be summed for the selected period.
- Source tables are not provided yet.
- The exact summation field is not provided yet.
- The report should not traverse hierarchy unless later clarified.

Return output in this exact JSON structure:

{
  "facts_used": [],
  "unknowns": [],
  "client_questions": [],
  "backend_tasks": [
    {
      "task": "",
      "status": "",
      "reason": "",
      "depends_on": []
    }
  ],
  "frontend_tasks": [
    {
      "task": "",
      "status": "",
      "reason": "",
      "depends_on": []
    }
  ],
  "database_considerations": [
    {
      "item": "",
      "status": "",
      "reason": "",
      "depends_on": []
    }
  ],
  "test_cases": [
    {
      "name": "",
      "status": "",
      "given": "",
      "expected": "",
      "depends_on": []
    }
  ],
  "hallucination_checks": []
}
```

## Raw Model Output

```json
{
  "facts_used": [
    "Report name: Production Report.",
    "Frontend already has a hierarchy agent endpoint.",
    "Frontend will pass the selected hierarchyAgent to the report.",
    "Backend report inputs are companyCode, hierarchyAgent, startDate, endDate.",
    "Date filtering should use DATE_ADDED.",
    "Totals should be summed for the report.",
    "Source tables for the report are not provided yet.",
    "The exact field name for the metric to be summed is not provided yet.",
    "The report should not traverse hierarchy unless later clarified."
  ],
  "unknowns": [
    "Source tables for the report",
    "Exact field name for the metric to be summed"
  ],
  "client_questions": [
    "What are the source tables for the report?",
    "What is the exact field name for the metric to be summed?"
  ],
  "backend_tasks": [
    {
      "task": "Filter records by DATE_ADDED between provided startDate and endDate (inclusive)",
      "status": "blocked",
      "reason": "Source tables and metric field are unknown",
      "depends_on": [
        "Source tables for the report",
        "Exact field name for the metric to be summed"
      ]
    },
    {
      "task": "Sum the metric field for filtered records",
      "status": "blocked",
      "reason": "Metric field is unknown",
      "depends_on": [
        "Exact field name for the metric to be summed"
      ]
    },
    {
      "task": "Group by hierarchyAgent",
      "status": "blocked",
      "reason": "Source tables are unknown",
      "depends_on": [
        "Source tables for the report"
      ]
    }
  ],
  "frontend_tasks": [
    {
      "task": "Pass the selected hierarchyAgent and date range to the report endpoint",
      "status": "ready",
      "reason": "Frontend already has a hierarchy agent endpoint and will pass the selected hierarchyAgent to the report",
      "depends_on": []
    }
  ],
  "database_considerations": [
    {
      "item": "Index on DATE_ADDED for performance in date-range queries",
      "status": "blocked",
      "reason": "Source tables are unknown",
      "depends_on": [
        "Source tables for the report"
      ]
    }
  ],
  "test_cases": [
    {
      "name": "Valid date range",
      "status": "ready",
      "given": "companyCode=ABC, hierarchyAgent=Manager_A, startDate=2023-10-01, endDate=2023-10-01",
      "expected": "Sum of metric field for records in the date range and hierarchy agent"
    }
  ]
}
```

## Manual Evaluation

### Accuracy

Score: 3.5 / 5
Notes:
The output is directionally correct. It identifies the right unknowns: source tables and summation field. It also respects the no-hierarchy-traversal rule better than the previous output. However, it still adds a likely incorrect backend task: `Group by hierarchyAgent`. Since the report is already filtered by a selected `hierarchyAgent`, grouping may not be required.

### Grounding

Score: 3 / 5
Notes:
Most items are grounded in the provided facts, but there are still weak spots. The model invented sample values in the test case even though the prompt said not to invent sample values. It also used “report endpoint,” which is not a named endpoint but still slightly exceeds the provided facts.

### Hallucination Risk

Score: 3 / 5
Notes:
The hallucination risk is lower than the baseline, but not eliminated. Main risks are the invented sample values, the `Group by hierarchyAgent` task, and the database index recommendation being included before knowing source tables and query shape.

### Structure / Format

Score: 2.5 / 5
Notes:
The output is valid JSON, but it did not follow the requested exact schema. It missed the required top-level `hallucination_checks` field. The `test_cases` item also missed the required `depends_on` field. This is a serious issue if another system is expected to parse the output reliably.

### Usefulness for Software Requirements Analysis

Score: 3.5 / 5
Notes:
The output is useful for human review and noticeably better than the first baseline. However, it is not yet reliable enough for automation because it violates the schema and still includes avoidable assumptions.

## Comparison Against Baseline

### Improved

* Better separation of known facts and unknowns.
* Fewer invented technologies and implementation details.
* No PostgreSQL/MySQL-specific advice.
* No recursive hierarchy recommendation.
* Better use of blocked/ready status.
* More concise and easier to inspect.

### Worse

* Took longer: 51.8 seconds compared with 31.6 seconds for V1.
* Failed strict schema compliance by missing required fields.
* Test case quality dropped because it used invented sample values and missed `depends_on`.

### Still Missing

* Full schema compliance.
* No invented sample values.
* Better handling of test cases that depend on unknown source tables and metric fields.
* Clear distinction between “can plan API contract” and “cannot implement query yet.”
* Explicit hallucination checks.

## Key Problems Found

* The model missed the required `hallucination_checks` key.
* The model missed `depends_on` inside the test case object.
* The model invented sample values: `ABC`, `Manager_A`, and `2023-10-01`.
* The model suggested `Group by hierarchyAgent`, which may be unnecessary or wrong.
* The model changed “selected period” into “for the report” in one fact, reducing precision.
* The model marked the valid date range test as ready even though expected output depends on unknown source tables and summation field.

## Current Verdict

Prompt V2 improved reasoning control but reduced schema reliability. This means the next improvement should not be more business logic. It should be schema enforcement and output validation.

## Next Improvement Target

The next prompt version should:

* Require every object to include all required keys.
* Forbid sample values completely.
* Add an explicit “schema self-check” before final output.
* Mark test cases as blocked if their expected result depends on unknown source tables or fields.
* Replace “Group by hierarchyAgent” with a safer task such as “Apply hierarchyAgent filter.”

# Controlled Prompt Evaluation - Qwen3 4B

## Model

qwen3:4b

## Prompt Type

Controlled prompt contract

## Runtime Notes

* Response time: 31.6 seconds
* Context window setting: 4K
* Interface used: Ollama UI
* Model storage path: D:\AI_LOCAL\ollama-models

## Prompt

```text
You are a software requirements analyst.

Your job is to analyze only the requirement details provided below.

Important rules:
- Do not invent table names, database engine, endpoints, UI framework, or implementation estimates.
- If something is unknown, put it under "unknowns" or "client_questions".
- Separate facts from assumptions.
- Do not recommend recursive hierarchy logic unless the input says hierarchy traversal is required.
- Do not use PostgreSQL/MySQL-specific syntax unless the input says that database is being used.
- Prefer implementation planning over generic advice.

Known requirement details:
- The report is a Production Report.
- Frontend already has a hierarchy agent endpoint.
- Frontend will pass the selected hierarchyAgent to the report.
- Inputs are companyCode, hierarchyAgent, startDate, endDate.
- Date filtering should use DATE_ADDED.
- Totals should be summed for the selected period.
- The exact source tables and summation fields are not provided yet.

Return output in this exact JSON structure:

{
  "facts": [],
  "assumptions": [],
  "unknowns": [],
  "client_questions": [],
  "backend_tasks": [],
  "frontend_tasks": [],
  "database_considerations": [],
  "test_cases": [],
  "hallucination_risks": [],
  "implementation_notes": []
}
```

## Raw Model Output

```json
{
  "facts": [
    "The report is a Production Report.",
    "Frontend already has a hierarchy agent endpoint.",
    "Frontend will pass the selected hierarchyAgent to the report.",
    "Inputs are companyCode, hierarchyAgent, startDate, endDate.",
    "Date filtering should use DATE_ADDED.",
    "Totals should be summed for the selected period."
  ],
  "assumptions": [
    "DATE_ADDED is a timestamp or date field suitable for range queries.",
    "The metric to be summed is a numeric field."
  ],
  "unknowns": [
    "The exact source tables for the report",
    "The exact field name for the metric to be summed (the production unit)"
  ],
  "client_questions": [
    "What is the exact metric to be summed? (e.g., what field in the database represents the production unit?)",
    "How is the hierarchy structured? (Is it a flat hierarchy or a nested hierarchy?)",
    "What is the data type of DATE_ADDED? (Is it a date, timestamp, or datetime?)",
    "What is the meaning of 'hierarchy agent' in the context of the report? (Is it a specific agent or a hierarchy level?)"
  ],
  "backend_tasks": [
    "Filter records by DATE_ADDED between provided startDate and endDate (inclusive)",
    "Sum the metric field for filtered records",
    "Group by hierarchyAgent"
  ],
  "frontend_tasks": [
    "Pass the selected hierarchyAgent and date range to the report endpoint"
  ],
  "database_considerations": [
    "Index on DATE_ADDED for performance in date-range queries"
  ],
  "test_cases": [
    {
      "input": "companyCode=ABC, hierarchyAgent=Manager_A, startDate=2023-10-01, endDate=2023-10-01",
      "expected_output": "Sum of production metric for records matching criteria"
    },
    {
      "input": "companyCode=ABC, hierarchyAgent=Manager_A, startDate=2023-10-02, endDate=2023-10-01",
      "expected_output": "No records (invalid date range)"
    },
    {
      "input": "companyCode=ABC, hierarchyAgent=Manager_X, startDate=2023-10-01, endDate=2023-10-01",
      "expected_output": "No records (hierarchyAgent does not exist)"
    }
  ],
  "hallucination_risks": [
    "Assuming DATE_ADDED is a timestamp when it might be a date-only field",
    "Assuming the hierarchy structure is flat when it might be nested"
  ],
  "implementation_notes": [
    "Backend must validate date range (startDate <= endDate) before processing",
    "HierarchyAgent values must be validated against available hierarchy levels",
    "Database index on DATE_ADDED is critical for performance with date ranges"
  ]
}
```

## Manual Evaluation

### Accuracy

Score: 4 / 5
Notes:
The response correctly uses the main facts: Production Report, selected `hierarchyAgent`, `companyCode`, `startDate`, `endDate`, `DATE_ADDED`, and summation over the selected period. It is more accurate than the baseline because it avoids invented database engines, table names, and recursive SQL. However, it still suggests `Group by hierarchyAgent`, which may be unnecessary because the report is already filtered by a selected `hierarchyAgent`.

### Grounding

Score: 3.5 / 5
Notes:
Most of the response is grounded in the provided facts. The model correctly separates known facts from unknowns. Weak grounding remains in the hierarchy-related client questions, sample test values, endpoint mention, and the strong index recommendation.

### Hallucination Risk

Score: 3 / 5
Notes:
The hallucination risk is reduced compared with the baseline, but not removed. The model still introduces sample values, assumes grouping, asks about hierarchy structure despite being told that selected `hierarchyAgent` is passed, and presents the `DATE_ADDED` index recommendation too strongly.

### Structure / Format

Score: 5 / 5
Notes:
The model followed the requested JSON structure successfully. All requested top-level keys are present, and the output is easy to inspect manually.

### Usefulness for Software Requirements Analysis

Score: 4 / 5
Notes:
The output is useful for human analysis and early planning. It identifies unknowns, questions, backend tasks, frontend tasks, database considerations, and test cases. It is not yet reliable enough for automation because some items still need stronger grounding and dependency tracking.

## Comparison Against Baseline

### Improved

* It obeyed the requested JSON structure.
* It separated facts, assumptions, unknowns, and questions.
* It did not invent table names.
* It did not invent database engine.
* It did not invent a specific endpoint path.
* It did not recommend recursive CTE logic.
* It avoided PostgreSQL/MySQL-specific syntax.
* It was more concise and automation-friendly than the baseline response.

### Worse

* It still asked whether hierarchy is flat or nested, even though the provided facts say the frontend passes a selected `hierarchyAgent`.
* It still suggested `Group by hierarchyAgent`, which may be wrong if the report is filtered by a single selected hierarchy agent.
* It said invalid date range should return “No records”; a validation error is more appropriate.
* It used invented sample values like `companyCode=ABC` and `Manager_A`.
* It said “Index on DATE_ADDED” without first checking existing indexes or actual query shape.
* It said the `DATE_ADDED` index is “critical,” which is too strong based on the given information.
* It suggested validating `hierarchyAgent` against available hierarchy levels, which may be valid but was not explicitly provided.

### Still Missing

* No dependency/status tracking for each task.
* No clear blocked vs ready classification.
* No schema-level validation.
* No confidence or risk level per task.
* No distinction between implementation tasks that are ready and tasks blocked by missing source tables/summation field.
* Controlled prompting reduced hallucination, but did not eliminate overconfident implementation advice.

## Key Problems Found

* The model still asked unnecessary hierarchy questions.
* The model used invented test values.
* The model gave a potentially incorrect grouping task.
* The model gave overly strong database performance advice.
* The model did not mark which tasks were blocked by unknown source tables or summation field.

## Current Verdict

Controlled Prompt V1 is a meaningful improvement over the baseline. It shows that prompt contracts can reduce hallucination and improve structure. However, it still allows too much unverified implementation advice.

## Next Improvement Target

The next prompt version should:

* Add task status such as `ready` or `blocked`.
* Add `depends_on` for each task.
* Forbid sample values unless explicitly labeled as examples.
* Avoid grouping unless the requirement says multiple hierarchy agents should be returned.
* Add explicit hallucination checks.
* Enforce stricter schema compliance.

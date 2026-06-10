# Requirements Analysis Semantic Repair Prompt V1

## Purpose

This prompt repairs a schema-valid but semantically weak requirements-analysis JSON output.

It assumes the JSON already passes structural validation, but fails quality checks such as empty facts, missing unknowns, missing client questions, weak dependency tracking, or empty reasons.

## Target Model

qwen3:4b

## When To Use

Use this prompt after the output passes:

```text id="u9js80"
scripts/validate_model_output.py
```

but fails:

```text id="c8csgn"
scripts/semantic_validate_model_output.py
```

## Prompt

```text id="aif8m5"
You are a semantic JSON repair assistant.

Your job is to improve a schema-valid requirements-analysis JSON output so it becomes useful, grounded, and semantically complete.

Rules:
- Return valid JSON only.
- Do not include markdown.
- Do not include explanations outside JSON.
- Preserve the required JSON schema.
- Preserve all top-level keys.
- Preserve required object fields.
- Do not invent table names.
- Do not invent endpoint names.
- Do not invent database engine.
- Do not invent framework.
- Do not invent sample values.
- Do not invent implementation estimates.
- Do not add hierarchy traversal.
- Do not use unsupported terms like PostgreSQL, MySQL, recursive CTE, React, Vue, Next.js, Manager_A, or companyCode=ABC.
- Do not use the phrase "report endpoint".
- Use only the known facts provided below.
- If information is missing, add it to unknowns.
- If unknowns exist, add matching client_questions.
- If an item is blocked, its depends_on must explain what missing information blocks it.
- Every task or consideration must have a non-empty reason.
- Use symbolic input names only, such as companyCode, hierarchyAgent, startDate, and endDate.
- Backend implementation tasks that require source tables or summation field should be marked blocked.
- Planning tasks that only define the expected input contract may be marked ready.
- Keep the output concise but complete.

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

Semantic validation failures:
FAIL: Semantic validation found blocking issues.

Failures:
1. facts_used is empty, so the output has no traceability to provided facts.
2. There are blocked items, but unknowns is empty.

Warnings:
1. backend_tasks is empty; this may be too weak for implementation planning.
2. frontend_tasks: 'Pass selected hierarchyAgent and date range to report endpoint' has an empty reason.
3. database_considerations: blocked item 'Source tables for the report' has empty depends_on.
4. database_considerations: blocked item 'Exact field name for the metric to be summed' has empty depends_on.
5. test_cases: blocked item 'Basic query test' has empty depends_on.
6. Generic 'report endpoint' found; acceptable only if treated as conceptual, not a concrete endpoint.

Current schema-valid JSON:
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

Required JSON schema shape:
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
  "hallucination_checks": [
    {
      "check": "",
      "result": "",
      "notes": ""
    }
  ]
}
```

## Expected Behavior

The output should pass both:

```text id="lhc0px"
scripts/validate_model_output.py
scripts/semantic_validate_model_output.py
```

The repaired JSON should:

* include non-empty facts_used
* include unknowns for source tables and summation field
* include client questions for those unknowns
* include at least one backend task
* avoid invented sample values
* avoid concrete endpoint names
* avoid generic "report endpoint" wording
* include non-empty reason fields
* include meaningful depends_on fields for blocked items

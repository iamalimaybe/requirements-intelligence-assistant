# V3 Semantic Validation - Qwen3 4B

## Purpose

This file records semantic validation results for the repaired Qwen3 4B output.

The repaired output passed JSON Schema validation, but structural validity alone does not prove the output is useful, complete, or grounded.

This evaluation tests the second validation layer:

```text
schema-valid output → semantic validation → quality issues detected
```

## Model

qwen3:4b

## Original Prompt Version

requirements-analysis-v3

## Repair Prompt Version

requirements-analysis-repair-v1

## Repaired Output File

```text
model-outputs/v3-repaired-qwen3-4b-output.json
```

## Semantic Validation Script

```text
scripts/semantic_validate_model_output.py
```

## Command Used

```powershell
python .\scripts\semantic_validate_model_output.py .\model-outputs\v3-repaired-qwen3-4b-output.json
```

## Validation Result

```text
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
```

## What Passed Before This Step

The repaired output passed structural validation using:

```text
schemas/requirements-analysis.schema.json
```

This means the output had:

* valid JSON
* required top-level keys
* required object fields
* allowed enum values
* no extra schema-breaking fields

## What Failed Now

| Issue                                                   | Severity | Why It Matters                                                         |
| ------------------------------------------------------- | -------: | ---------------------------------------------------------------------- |
| `facts_used` is empty                                   |  Failure | The output cannot be traced back to the provided requirement facts.    |
| Blocked items exist but `unknowns` is empty             |  Failure | The model says work is blocked but does not expose what is unknown.    |
| `backend_tasks` is empty                                |  Warning | The result is weak for implementation planning.                        |
| Frontend task has empty `reason`                        |  Warning | The output is schema-valid but low quality.                            |
| Blocked database considerations have empty `depends_on` |  Warning | Dependency tracking is structurally present but semantically weak.     |
| Blocked test case has empty `depends_on`                |  Warning | The system cannot explain why the test case is blocked.                |
| Generic “report endpoint” wording appears               |  Warning | Acceptable only if treated as conceptual, not as a real endpoint name. |

## Key Learning

A model output can be:

```text
valid JSON
schema compliant
still semantically weak
```

JSON Schema is necessary, but it only answers:

```text
Does the output have the correct shape?
```

It does not answer:

```text
Is the output useful, grounded, complete, or safe for implementation planning?
```

## Production Lesson

A production-grade LLM workflow should use layered validation:

1. **JSON parsing**

   * Is the model output valid JSON?

2. **Schema validation**

   * Does the output match the expected contract?

3. **Semantic validation**

   * Is the output useful and grounded?
   * Are important fields non-empty?
   * Are blockers tied to unknowns?
   * Are dependencies meaningful?
   * Are risky unsupported terms present?

4. **Repair or retry**

   * If validation fails, the system should repair or retry before accepting the output.

## Current Verdict

The repair flow successfully fixed structure, but not content quality.

This is still a useful milestone because it shows why production LLM systems need both structural and semantic validation.

## Next Improvement Target

The next step should be a semantic repair prompt or automated repair flow that receives:

* the repaired-but-semantically-weak JSON
* the semantic validation failures
* the original known facts
* the JSON Schema expectations

Then it should produce an improved output that passes both:

```text
scripts/validate_model_output.py
scripts/semantic_validate_model_output.py
```

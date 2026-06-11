# V3 Pipeline V2 Validation - Qwen3 4B

## Purpose

This file records the result of running the stricter validation pipeline against the previously schema-valid and semantic-v1-valid output.

The goal is to test whether the improved semantic validator can reject outputs that are structurally valid but too weak for a requirements-analysis workflow.

## Model

qwen3:4b

## Input File

```text
model-outputs/v3-semantic-repaired-schema-fixed-qwen3-4b-output.json
```

## Pipeline Script

```text
scripts/validate_pipeline_v2.py
```

## Schema Validator

```text
scripts/validate_model_output.py
```

## Semantic Validator

```text
scripts/semantic_validate_model_output_v2.py
```

## Command Used

```powershell
python .\scripts\validate_pipeline_v2.py .\model-outputs\v3-semantic-repaired-schema-fixed-qwen3-4b-output.json
```

## Pipeline Output

```text
STEP 1: Schema validation
-------------------------
PASS: Model output matches the schema.

STEP 2: Semantic validation v2
------------------------------
FAIL: Semantic validation v2 found blocking issues.

Failures:
1. facts_used should contain at least 5 grounded requirement facts.
2. facts_used does not mention required fact term: Production Report
3. facts_used does not mention required fact term: hierarchyAgent
4. facts_used does not mention required fact term: companyCode
5. facts_used does not mention required fact term: startDate
6. facts_used does not mention required fact term: endDate
7. facts_used does not mention required fact term: DATE_ADDED
8. facts_used does not mention required fact term: summed
9. unknowns does not mention required unknown: summation field
10. backend_tasks should include a task for applying DATE_ADDED filtering.
11. backend_tasks should include a task for summing the selected metric/field.
12. test_cases is empty.
13. hallucination_checks is empty.

Warnings:
1. test_cases has fewer than 2 cases; coverage is weak.
2. hallucination_checks has fewer than 2 checks; risk coverage is weak.

PIPELINE V2 RESULT: FAIL
Reason: Semantic validation v2 failed.
```

## What Passed

| Check                   | Result | Notes                                            |
| ----------------------- | ------ | ------------------------------------------------ |
| JSON parsing            | Pass   | Output is valid JSON.                            |
| Schema validation       | Pass   | Output matches the required JSON Schema.         |
| Required top-level keys | Pass   | All required top-level keys are present.         |
| Required object fields  | Pass   | Existing objects use the expected schema fields. |

## What Failed

| Issue                                             | Why It Matters                                                                              |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `facts_used` is too thin                          | The output cannot prove it used the main requirement facts.                                 |
| Missing `Production Report` in facts              | The report identity should be traceable.                                                    |
| Missing input fields in facts                     | `companyCode`, `hierarchyAgent`, `startDate`, and `endDate` are part of the known contract. |
| Missing `DATE_ADDED` in facts                     | Date filtering is a core requirement.                                                       |
| Missing `summed` in facts                         | Summation is a core requirement.                                                            |
| Unknowns do not mention `summation field`         | The exact field to sum is one of the key blockers.                                          |
| Backend task for `DATE_ADDED` filtering missing   | Implementation planning is incomplete.                                                      |
| Backend task for summing the metric/field missing | The report’s core business logic is not represented.                                        |
| `test_cases` is empty                             | The output is weak for QA and implementation validation.                                    |
| `hallucination_checks` is empty                   | The output loses explicit risk checking.                                                    |

## Key Learning

The previous pipeline pass was too permissive.

The output was:

```text
valid JSON
schema compliant
semantic-v1 compliant
still too weak
```

Semantic validator v2 correctly rejects this kind of output.

## Production Lesson

A production-grade LLM workflow needs validation rules that reflect the business purpose, not just generic content checks.

For this project, useful requirements-analysis output should include:

* traceable facts
* clear unknowns
* client questions mapped to unknowns
* backend tasks for the core logic
* frontend tasks for known integration responsibilities
* test cases
* hallucination/risk checks

## Current Verdict

Pipeline v2 is stricter and more useful than the previous pipeline.

The current model output should be rejected because it is schema-valid but not strong enough for the intended workflow.

## Next Improvement Target

Create a semantic repair prompt v2 that directly targets the pipeline v2 failures.

The repaired output should pass:

```text
scripts/validate_pipeline_v2.py
```

without weakening schema compliance.

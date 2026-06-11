# Multi-Context Regression Validation v3 - qwen3:4b

## Purpose

This evaluation records the first successful multi-context regression test for the project.

The goal was to prove that context-driven semantic validation v3 is not tied to one requirement type.

The workflow was tested against two different requirement contexts:

1. Production Report
2. Review Moderation Dashboard

These contexts are intentionally different:

| Context | Requirement Type | Main Concern |
| --- | --- | --- |
| Production Report | report generation | inputs, date filtering, summation, unknown source data |
| Review Moderation Dashboard | admin workflow | long text display, status updates, filters, authorization |

## Why This Matters

Earlier validation was tied to one requirement.

The multi-context regression runner proves that the same validation system can run against multiple contexts without changing the validator code.

This is an important portfolio milestone because it demonstrates:

```text
same validator
same schema
same regression runner
different requirement contexts
```

## Command

```powershell
python .\scripts\run_multi_context_regression_tests.py .\scratch\context-only-enriched-output.json .\contexts\production-report-context.json .\scratch\review-moderation-enriched-output.json .\contexts\review-moderation-context.json
```

## Result

```text
CONTEXT CASE 1
--------------
Output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\context-only-enriched-output.json
Context: D:\AI_LOCAL\projects\requirements-intelligence-assistant\contexts\production-report-context.json

STEP: Positive validation test
------------------------------
Running schema validation...
PASS: Model output matches the schema.
Running semantic validation v3...
SEMANTIC VALIDATION V3 RESULT: PASS
PIPELINE V3 RESULT: PASS

STEP: Negative validation tests
-------------------------------
Writing negative fixtures to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\v3-negative-tests
[PASS] missing-required-fact: rejected as expected.
[PASS] invalid-status: rejected as expected.
[PASS] blocked-without-depends-on: rejected as expected.
[PASS] invalid-hallucination-result: rejected as expected.
[PASS] invented-db-engine: rejected as expected.
[PASS] invented-frontend-framework: rejected as expected.
[PASS] unsupported-implementation-estimate: rejected as expected.
[PASS] fake-sample-value: rejected as expected.
NEGATIVE TEST RESULT: PASS

REGRESSION TEST RESULT: PASS

CONTEXT CASE 2
--------------
Output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\review-moderation-enriched-output.json
Context: D:\AI_LOCAL\projects\requirements-intelligence-assistant\contexts\review-moderation-context.json

STEP: Positive validation test
------------------------------
Running schema validation...
PASS: Model output matches the schema.
Running semantic validation v3...
SEMANTIC VALIDATION V3 RESULT: PASS
PIPELINE V3 RESULT: PASS

STEP: Negative validation tests
-------------------------------
Writing negative fixtures to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\v3-negative-tests
[PASS] missing-required-fact: rejected as expected.
[PASS] invalid-status: rejected as expected.
[PASS] blocked-without-depends-on: rejected as expected.
[PASS] invalid-hallucination-result: rejected as expected.
[PASS] invented-db-engine: rejected as expected.
[PASS] invented-frontend-framework: rejected as expected.
[PASS] unsupported-implementation-estimate: rejected as expected.
[PASS] fake-sample-value: rejected as expected.
NEGATIVE TEST RESULT: PASS

REGRESSION TEST RESULT: PASS

MULTI-CONTEXT REGRESSION RESULT: PASS
```

## What This Proves

The project now has proof that:

```text
known-good output passes
known-bad output fails
the same process works across multiple contexts
```

This is stronger than only validating one happy-path output.

## Current Limitation

Both contexts are still hand-written structured JSON files.

The next stronger proof would be to generate or assist creation of trusted context from less structured inputs such as:

- requirement notes
- tickets
- meeting notes
- emails
- PDFs
- markdown documents

That would move the project closer to retrieval-augmented generation and document-grounded requirements analysis.
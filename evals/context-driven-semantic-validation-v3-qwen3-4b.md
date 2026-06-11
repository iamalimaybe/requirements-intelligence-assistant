# Context-Driven Semantic Validation v3 - qwen3:4b

## Purpose

This evaluation records the move from requirement-specific semantic validation to context-driven semantic validation.

Earlier semantic validation was tied to the Production Report requirement through hardcoded terms such as:

- Production Report
- hierarchyAgent
- DATE_ADDED
- summation field

That was useful for the first requirement, but weak architecturally because the project had already moved toward a context-driven workflow.

Semantic validation v3 changes the validator so the supplied context JSON becomes the semantic source of truth.

## Model

```text
qwen3:4b
```

Run locally through Ollama.

## Current Workflow Under Test

```text
trusted context JSON
-> generated prompt
-> Ollama API
-> raw model JSON
-> normalize
-> enrich from trusted context
-> schema validation
-> context-driven semantic validation v3
-> PASS/FAIL
```

## Main Files Added or Updated

```text
scripts/semantic_validate_model_output_v3.py
scripts/validate_pipeline_v3.py
scripts/run_validation_v3_negative_tests.py
scripts/run_validation_v3_regression_tests.py
scripts/run_requirements_workflow.py
scripts/run_ollama_requirements_workflow.py
README.md
```

## Positive Validation Test

Command:

```powershell
python .\scripts\validate_pipeline_v3.py .\scratch\context-only-enriched-output.json .\contexts\production-report-context.json
```

Result:

```text
Running schema validation...
PASS: Model output matches the schema.
Running semantic validation v3...
SEMANTIC VALIDATION V3 RESULT: PASS
PIPELINE V3 RESULT: PASS
```

## Negative Validation Tests

Command:

```powershell
python .\scripts\run_validation_v3_negative_tests.py .\scratch\context-only-enriched-output.json .\contexts\production-report-context.json
```

Result:

```text
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
```

## Regression Test

Command:

```powershell
python .\scripts\run_validation_v3_regression_tests.py .\scratch\context-only-enriched-output.json .\contexts\production-report-context.json
```

Result:

```text
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
```

## What v3 Validates

Semantic validation v3 checks that the model output covers required context-backed content:

- facts used
- unknowns
- client questions
- backend tasks
- frontend tasks
- database considerations
- test cases
- hallucination checks

It also rejects known risky patterns when they are not supported by the context:

- invented database engines
- invented frontend frameworks
- fake sample values
- unsupported implementation estimates
- invalid status values
- blocked items without depends_on
- invalid hallucination check result values

## Important Bug Found During Negative Testing

Initial v3 validation failed to reject an invented database engine.

The negative test injected:

```text
Use PostgreSQL for this implementation.
```

The validator incorrectly passed this output because the guarded-mention logic was too broad. It allowed risky terms if they appeared near defensive language such as "do not" or "unsupported".

This was fixed by making guarded mention detection sentence-scoped.

A risky term is now allowed only when the same sentence clearly marks it as unsupported, unconfirmed, invented, fake, or not present in context.

After the fix, the invented database engine negative test failed correctly.

## Result

The current v3 workflow passes both sides of validation:

```text
known-good output passes
known-bad outputs fail
```

This is stronger than schema validation alone because it proves the system can reject structurally valid but semantically unsafe output.

## Portfolio Significance

This milestone demonstrates that the project treats LLM output as untrusted.

The LLM drafts the analysis, but deterministic code decides whether the output is acceptable.

This supports the project positioning:

```text
I can build practical LLM workflows that are grounded, validated, testable, and production-aware — not just call an LLM API and hope the answer is good.
```

## Current Limitation

The validator is context-driven, but it has only been proven against one requirement context so far.

The next important proof is to add a second or third requirement context and show that the same workflow can validate different requirements without hardcoding requirement-specific terms.
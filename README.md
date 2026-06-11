# Requirements Intelligence Assistant

A local LLM workflow for analyzing software requirements with validation-first output handling.

This project is not a generic chatbot or prompt demo. It explores how to make local LLM output safer and more useful for production-style software engineering workflows by combining:

* local LLM generation
* trusted context grounding
* deterministic normalization
* trusted-context enrichment
* JSON Schema validation
* context-driven semantic validation
* positive and negative regression checks
* repeatable CLI workflows

## Why This Project Exists

Local LLMs can produce useful analysis, but they are unreliable when used directly.

Observed failure modes include:

* invented table names
* invented endpoint names
* unsupported database assumptions
* unsupported frontend assumptions
* schema drift
* missing required fields
* fake sample values
* empty but schema-valid sections
* weak traceability to known facts

This project treats model output as **untrusted** until it passes deterministic validation.

The model is used as a draft generator. Code decides whether the output is acceptable.

## Current Scope

The current implemented workflow analyzes a **Production Report** requirement.

The system produces structured engineering output such as:

* facts used
* unknowns
* client questions
* backend tasks
* frontend tasks
* database considerations
* test cases
* hallucination checks

Current architecture:

```text
trusted context JSON
→ generated prompt
→ Ollama API
→ raw model JSON
→ normalize
→ enrich from trusted context
→ schema validation
→ context-driven semantic validation v3
→ PASS/FAIL
```

## Model Used

Initial experiments use:

```text
qwen3:4b
```

Running locally through Ollama on Windows 10.

Test hardware:

```text
CPU: Ryzen 7 5800X
GPU: RTX 2070 8GB
RAM: 16GB
OS: Windows 10
```

This project intentionally uses a small local model to test practical local LLM workflows rather than relying only on hosted APIs.

## Project Structure

```text
requirements-intelligence-assistant/
├── contexts/
│   └── production-report-context.json
├── evals/
│   └── evaluation notes and model run summaries
├── model-outputs/
│   └── committed demo outputs from earlier workflow stages
├── prompts/
│   └── prompt templates and earlier prompt experiments
├── schemas/
│   └── requirements-analysis.schema.json
├── scripts/
│   ├── build_prompt_from_context.py
│   ├── enrich_model_output.py
│   ├── generate_with_ollama.py
│   ├── normalize_model_output.py
│   ├── run_ollama_requirements_workflow.py
│   ├── run_requirements_workflow.py
│   ├── run_validation_v3_negative_tests.py
│   ├── run_validation_v3_regression_tests.py
│   ├── semantic_validate_model_output.py
│   ├── semantic_validate_model_output_v2.py
│   ├── semantic_validate_model_output_v3.py
│   ├── validate_model_output.py
│   ├── validate_pipeline.py
│   ├── validate_pipeline_v2.py
│   └── validate_pipeline_v3.py
├── requirements.txt
└── README.md
```

## Setup

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Required runtime tools:

```text
Python 3.10+
Ollama
qwen3:4b
```

Python dependency:

```text
jsonschema>=4.0.0
```

## Trusted Context

Requirement-specific facts are stored in trusted context JSON.

Current context file:

```text
contexts/production-report-context.json
```

The trusted context is the semantic source of truth for:

* known facts
* required unknowns
* client questions
* backend tasks
* frontend tasks
* database considerations
* test cases
* hallucination checks

This prevents the model from being the only source of truth.

## Prompt Generation From Context

The prompt can be generated from the trusted context instead of being manually maintained.

Run:

```powershell
python .\scripts\build_prompt_from_context.py `
  --context .\contexts\production-report-context.json `
  --output .\scratch\generated-prompt.txt
```

This keeps requirement-specific information in the context file and reduces duplication between prompt text and validation rules.

## One-Command Local LLM Workflow

The preferred workflow starts from trusted context JSON.

Run:

```powershell
python .\scripts\run_ollama_requirements_workflow.py `
  --model qwen3:4b `
  --context .\contexts\production-report-context.json `
  --generated-prompt-output .\scratch\context-only-generated-prompt.txt `
  --generated-output .\scratch\context-only-generated-output.json `
  --normalized-output .\scratch\context-only-normalized-output.json `
  --enriched-output .\scratch\context-only-enriched-output.json
```

This command performs:

```text
trusted context
→ generated prompt
→ Ollama model output
→ normalize
→ enrich
→ validate with pipeline v3
```

Expected result:

```text
OLLAMA WORKFLOW RESULT: PASS
```

Runtime files are written to `scratch/`, which is ignored by Git.

## Processing Workflow

The processing workflow handles deterministic post-processing only:

```text
model output
→ normalize
→ enrich with trusted context
→ processed output
```

Run:

```powershell
python .\scripts\run_requirements_workflow.py `
  --input .\scratch\context-only-generated-output.json `
  --context .\contexts\production-report-context.json `
  --normalized-output .\scratch\context-only-normalized-output.json `
  --enriched-output .\scratch\context-only-enriched-output.json
```

Expected result:

```text
WORKFLOW RESULT: PASS
```

This script intentionally stops before validation. Final validation is handled by `validate_pipeline_v3.py` or by the full Ollama workflow.

## Schema Validation

Schema validation checks whether the output has the expected JSON structure.

Run:

```powershell
python .\scripts\validate_model_output.py .\scratch\context-only-enriched-output.json
```

This catches issues such as:

* missing required keys
* wrong field names
* missing object fields
* unexpected extra properties
* invalid JSON shape

Schema validation does not prove that the output is semantically correct. It only proves that the structure matches the schema.

## Context-Driven Semantic Validation v3

Semantic validation v3 checks the model output against the supplied context JSON.

Run:

```powershell
python .\scripts\semantic_validate_model_output_v3.py `
  .\scratch\context-only-enriched-output.json `
  .\contexts\production-report-context.json
```

It validates that the output covers required context items, including:

* facts used
* unknowns
* client questions
* backend tasks
* frontend tasks
* database considerations
* test cases
* hallucination checks

It also rejects risky unsupported content, including:

* invented database engines
* invented frontend frameworks
* fake sample values
* unsupported implementation estimates
* invalid task statuses
* blocked items without `depends_on`
* invalid hallucination check result values

Allowed task status values:

```text
ready
blocked
optional
```

Allowed hallucination check result values:

```text
pass
fail
warning
blocked
```

## Validation Pipeline v3

Pipeline v3 enforces the correct validation order:

```text
schema validation
→ semantic validation v3
```

Run:

```powershell
python .\scripts\validate_pipeline_v3.py `
  .\scratch\context-only-enriched-output.json `
  .\contexts\production-report-context.json
```

Expected result:

```text
Running schema validation...
PASS: Model output matches the schema.
Running semantic validation v3...
SEMANTIC VALIDATION V3 RESULT: PASS
PIPELINE V3 RESULT: PASS
```

## Negative Validation Tests

The negative test runner creates controlled bad outputs from a known-good enriched output.

Run:

```powershell
python .\scripts\run_validation_v3_negative_tests.py `
  .\scratch\context-only-enriched-output.json `
  .\contexts\production-report-context.json
```

It verifies that the validator rejects:

* missing required facts
* invalid status values
* blocked items without `depends_on`
* invalid hallucination check result values
* invented database engines
* invented frontend frameworks
* unsupported implementation estimates
* fake sample values

Expected result:

```text
NEGATIVE TEST RESULT: PASS
```

This proves the validator is not only passing the happy path. It also rejects known bad outputs.

## Regression Test Runner

The regression runner combines positive and negative validation checks into one command.

Run:

```powershell
python .\scripts\run_validation_v3_regression_tests.py `
  .\scratch\context-only-enriched-output.json `
  .\contexts\production-report-context.json
```

Expected result:

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

This is the strongest current proof command for the project.

It demonstrates:

```text
known-good output passes
known-bad outputs fail
```

## Multi-Context Regression Test Runner

The multi-context regression runner verifies that the same validation system works across multiple requirement contexts.

Run:

```powershell
python .\scripts\run_multi_context_regression_tests.py `
  .\scratch\context-only-enriched-output.json `
  .\contexts\production-report-context.json `
  .\scratch\review-moderation-enriched-output.json `
  .\contexts\review-moderation-context.json```

## Reproducible Demo Workflow

The demo workflow regenerates outputs for all included requirement contexts before running regression tests.

This avoids relying on old files in `scratch/`.

Run:

```powershell
python .\scripts\run_demo_multi_context_workflow.py --model qwen3:4b
```

This command performs:

```text
Production Report context
→ generate prompt
→ call Ollama
→ normalize
→ enrich
→ validate with pipeline v3

Review Moderation context
→ generate prompt
→ call Ollama
→ repair malformed JSON if needed
→ normalize
→ enrich
→ validate with pipeline v3

Both enriched outputs
→ multi-context regression tests
```

Expected result:

```text
DEMO MULTI-CONTEXT WORKFLOW RESULT: PASS
```

The workflow includes a JSON repair fallback for malformed local model responses.

This matters because small local models can return invalid JSON even when prompted strictly. The repair fallback keeps generation failure handling explicit while still requiring the final output to pass schema validation, semantic validation v3, and regression tests.

Runtime files are written to:

```text
scratch/demo-multi-context/
```

These files are ignored by Git.

## Key Result

The strongest workflow so far is:

```text
trusted context
→ prompt generation
→ local LLM generation
→ deterministic normalization
→ trusted-context enrichment
→ schema validation
→ context-driven semantic validation v3
→ positive and negative regression proof
```

This demonstrates a production-oriented approach:

| Responsibility                          | Owner                             |
| --------------------------------------- | --------------------------------- |
| Drafting analysis                       | Local LLM                         |
| Supplying known facts                   | Trusted context                   |
| Building prompts                        | Deterministic prompt builder      |
| Fixing predictable structure issues     | Normalizer                        |
| Filling required context-backed content | Enricher                          |
| Enforcing JSON structure                | JSON Schema                       |
| Checking semantic groundedness          | Semantic validator v3             |
| Accept/reject decision                  | Validation pipeline               |
| Regression proof                        | Positive and negative test runner |

## Current Status

Completed:

* local Qwen3 4B baseline evaluation
* controlled prompt experiments
* JSON Schema validation
* repair prompt experiments
* semantic validation v1 and v2
* validation pipeline v1 and v2
* deterministic normalization
* trusted-context enrichment
* Ollama API generation
* one-command local Ollama workflow
* context-generated prompt workflow
* context-only workflow
* context-driven semantic validation v3
* negative validation tests
* regression test runner

Current main proof command:

```powershell
python .\scripts\run_demo_multi_context_workflow.py --model qwen3:4b
```

## Limitations

This project does not claim that a 4B local model can produce production-ready output by itself.

The main finding is the opposite:

```text
Prompting alone is not enough.
```

Current limitations:

* only one requirement context has been implemented so far
* semantic validation uses deterministic heuristics, not full human understanding
* the validator can catch defined hallucination patterns, not every possible bad answer
* no UI or API layer yet
* no retrieval-augmented generation yet
* no CI workflow yet
* no multi-model comparison dashboard yet

## Next Planned Steps

Recommended next steps:

1. Add a second or third requirement context to prove the workflow is reusable.
2. Add a proper run/evaluation report system so multiple model runs can be compared.
3. Add a lightweight API or UI around the workflow.
4. Move toward retrieval-augmented generation over real requirement documents, tickets, emails, or PDFs.
5. Add CI regression checks once the script interface stabilizes.

## Portfolio Positioning

This project demonstrates practical LLM engineering skills:

* local model usage
* prompt testing
* schema-first design
* validation-first output handling
* deterministic normalization
* trusted-context grounding
* context-driven semantic validation
* hallucination rejection
* positive and negative regression testing
* production-style accept/reject workflows

The positioning is:

```text
I can build practical LLM workflows that are grounded, validated, testable, and production-aware — not just call an LLM API and hope the answer is good.
```

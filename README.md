# Requirements Intelligence Assistant

A local LLM workflow for analyzing software requirements with validation-first output handling.

This project is not a generic chatbot or prompt demo. It explores how to make local LLM output safer and more useful for production-style software engineering workflows by combining:

* local LLM generation
* trusted context grounding
* deterministic normalization
* trusted-context enrichment
* JSON Schema validation
* context-driven semantic validation
* malformed JSON repair fallback
* positive and negative regression checks
* multi-context regression testing
* structured run reporting
* run-report schema validation
* repeatable CLI workflows

## Why This Project Exists

Local LLMs can produce useful analysis, but they are unreliable when used directly.

Observed failure modes include:

* malformed JSON
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

The project currently includes two requirement contexts:

```text
contexts/production-report-context.json
contexts/review-moderation-context.json
```

The first context is report-oriented. The second context is admin workflow/UI-oriented.

This helps prove that the validation workflow is not tied to one hardcoded requirement.

The demo workflow automatically discovers all files matching:

```text
contexts/*-context.json
```

So adding another context later does not require changing the demo script.

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
→ malformed JSON repair fallback if needed
→ normalize
→ enrich from trusted context
→ schema validation
→ context-driven semantic validation v3
→ positive/negative regression tests
→ structured run report
→ run-report schema validation
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
│   ├── production-report-context.json
│   └── review-moderation-context.json
├── evals/
│   └── evaluation notes and model run summaries
├── model-outputs/
│   └── committed demo outputs from earlier workflow stages
├── prompts/
│   └── prompt templates and earlier prompt experiments
├── schemas/
│   ├── requirements-analysis.schema.json
│   └── run-report.schema.json
├── scripts/
│   ├── build_prompt_from_context.py
│   ├── enrich_model_output.py
│   ├── generate_with_ollama.py
│   ├── normalize_model_output.py
│   ├── run_demo_multi_context_workflow.py
│   ├── run_multi_context_regression_tests.py
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
│   ├── validate_pipeline_v3.py
│   └── validate_run_report.py
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

Current context files:

```text
contexts/production-report-context.json
contexts/review-moderation-context.json
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

The prompt can be generated from trusted context instead of being manually maintained.

Run:

```powershell
python .\scripts\build_prompt_from_context.py `
  --context .\contexts\production-report-context.json `
  --output .\scratch\generated-prompt.txt
```

This keeps requirement-specific information in the context file and reduces duplication between prompt text and validation rules.

## One-Command Local LLM Workflow

Run a single context through prompt generation, Ollama, normalization, enrichment, and validation:

```powershell
python .\scripts\run_ollama_requirements_workflow.py `
  --model qwen3:4b `
  --context .\contexts\production-report-context.json `
  --generated-prompt-output .\scratch\context-only-generated-prompt.txt `
  --generated-output .\scratch\context-only-generated-output.json `
  --normalized-output .\scratch\context-only-normalized-output.json `
  --enriched-output .\scratch\context-only-enriched-output.json
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
REGRESSION TEST RESULT: PASS
```

This demonstrates:

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
  .\contexts\review-moderation-context.json
```

Expected result:

```text
MULTI-CONTEXT REGRESSION RESULT: PASS
```

This proves that context-driven semantic validation v3 is reusable across more than one requirement type.

## Reproducible Demo Workflow

The demo workflow regenerates outputs for all discovered requirement contexts before running regression tests.

By default, the demo runner automatically discovers all files matching:

```text
contexts/*-context.json
```

This avoids relying on old files in `scratch/` and allows new contexts to be picked up without changing the script.

Run:

```powershell
python .\scripts\run_demo_multi_context_workflow.py --model qwen3:4b
```

This command performs:

```text
all contexts matching contexts/*-context.json
→ generate prompt
→ call Ollama
→ repair malformed JSON if needed
→ normalize
→ enrich
→ validate with pipeline v3

all enriched outputs
→ multi-context regression tests
→ run-report.json
→ validate run-report.json
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

## Run Report

The reproducible demo workflow writes a structured run report:

```text
scratch/demo-multi-context/run-report.json
```

The report records:

* model name
* temperature
* context discovery mode
* context count
* output directory
* context paths
* generated prompt paths
* generated output paths
* normalized output paths
* enriched output paths
* whether JSON repair was used
* failed generation path, if any
* per-step start and end timestamps
* per-step duration
* return codes
* multi-context regression result
* final workflow result

This makes the demo easier to inspect and helps prepare for future model comparisons.

The run report is also validated against:

```text
schemas/run-report.schema.json
```

Manual validation command:

```powershell
python .\scripts\validate_run_report.py .\scratch\demo-multi-context\run-report.json
```

Expected result:

```text
PASS: Run report matches the schema.
```

The reproducible demo workflow runs this validation automatically before printing the final pass result.

## Model Comparison Runner

The model comparison runner executes the reproducible demo workflow for one or more Ollama models and summarizes the results.

Run with the current local model:

```powershell
python .\scripts\run_model_comparison.py --model qwen3:4b
```
The runner writes:

```text
scratch/model-comparison/model-comparison-summary.json
scratch/model-comparison/<model-name>/run-report.json
```

It compares:

```text
final result
context count
repair count
failed context count
multi-context regression result
run-report validation result
duration
```

Example multi-model usage:

```powershell
python .\scripts\run_model_comparison.py `
  --model qwen3:4b `
  --model llama3.1:8b `
  --model mistral:7b
```

Runtime files are written to `scratch/`, which is ignored by Git.

## Key Result

The strongest workflow so far is:

```text
trusted context
→ prompt generation
→ local LLM generation
→ malformed JSON repair fallback
→ deterministic normalization
→ trusted-context enrichment
→ schema validation
→ context-driven semantic validation v3
→ positive and negative regression proof
→ multi-context regression proof
→ structured run report
→ run-report schema validation
```

This demonstrates a production-oriented approach:

| Responsibility                          | Owner                              |
| --------------------------------------- | ---------------------------------- |
| Drafting analysis                       | Local LLM                          |
| Supplying known facts                   | Trusted context                    |
| Building prompts                        | Deterministic prompt builder       |
| Handling malformed JSON                 | JSON repair fallback               |
| Fixing predictable structure issues     | Normalizer                         |
| Filling required context-backed content | Enricher                           |
| Enforcing JSON structure                | JSON Schema                        |
| Checking semantic groundedness          | Semantic validator v3              |
| Accept/reject decision                  | Validation pipeline                |
| Regression proof                        | Positive and negative test runners |
| Multi-context proof                     | Multi-context regression runner    |
| Run evidence                            | Structured run report              |
| Run-report structure                    | Run-report schema validator        |

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
* second requirement context
* multi-context regression runner
* reproducible multi-context demo workflow
* malformed JSON repair fallback
* structured run report
* run report schema validation

Current main proof command:

```powershell
python .\scripts\run_demo_multi_context_workflow.py --model qwen3:4b
```
## Local CI-Style Proof Command

The main local proof command is:

```powershell
python .\scripts\run_demo_multi_context_workflow.py --model qwen3:4b

This command acts as a local CI-style check for the project.

It validates:

* trusted context files
* generated/enriched model outputs
* semantic grounding
* negative regression cases
* multi-context regression
* run-report.json
```

## Limitations

This project does not claim that a 4B local model can produce production-ready output by itself.

The main finding is the opposite:

```text
Prompting alone is not enough.
```

Current limitations:

* only two requirement contexts have been implemented so far
* both contexts are still hand-written structured JSON files
* semantic validation uses deterministic heuristics, not full human understanding
* the validator can catch defined hallucination patterns, not every possible bad answer
* JSON repair only handles malformed model output, not semantic correctness
* no UI or API layer yet
* no retrieval-augmented generation yet
* no CI workflow yet
* no multi-model comparison dashboard yet

## Next Planned Steps

Recommended next steps:

1. Add a third requirement context or start deriving trusted context from less structured input.
2. Add CI regression checks once the script interface stabilizes.
3. Add model-run comparison using structured run reports.
4. Add a lightweight API or UI around the workflow.
5. Move toward retrieval-augmented generation over real requirement documents, tickets, emails, or PDFs.

## Portfolio Positioning

This project demonstrates practical LLM engineering skills:

* local model usage
* prompt testing
* schema-first design
* validation-first output handling
* deterministic normalization
* trusted-context grounding
* malformed JSON repair
* context-driven semantic validation
* hallucination rejection
* positive and negative regression testing
* multi-context validation
* structured run reporting
* run-report validation
* production-style accept/reject workflows

The positioning is:

```text
I can build practical LLM workflows that are grounded, validated, testable, and production-aware — not just call an LLM API and hope the answer is good.
```

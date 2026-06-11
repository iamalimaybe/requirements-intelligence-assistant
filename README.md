# Requirements Intelligence Assistant

A local LLM workflow for analyzing software requirements with validation-first output handling.

This project is not a generic chatbot. It explores how to make local LLM output safer and more useful for production-style software engineering workflows by combining:

* local LLM generation
* prompt evaluation
* JSON Schema validation
* semantic validation
* deterministic normalization
* trusted-context enrichment
* validation pipeline checks

## Current Goal

The current scope is a **Production Report requirements-analysis workflow**.

The system takes weak or inconsistent local LLM output and improves it through a controlled pipeline:

```text
local LLM output
→ deterministic normalization
→ trusted-context enrichment
→ schema validation
→ semantic validation
→ pass/fail decision
```

## Why This Project Exists

Local LLMs can produce useful analysis, but they are unreliable when used directly.

Observed failure modes include:

* invented table names
* invented endpoint names
* unsupported database assumptions
* schema drift
* missing required fields
* fake sample values
* empty but schema-valid sections
* weak traceability to known facts

This project treats model output as **untrusted** until it passes validation.

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

## Project Structure

```text
requirements-intelligence-assistant/
├── contexts/
│   └── production-report-context.json
├── evals/
│   ├── baseline-qwen3-4b.md
│   ├── controlled-prompt-qwen3-4b.md
│   ├── controlled-prompt-v2-qwen3-4b.md
│   ├── controlled-prompt-v3-qwen3-4b.md
│   ├── v3-schema-validation-qwen3-4b.md
│   ├── v3-repair-validation-qwen3-4b.md
│   ├── v3-semantic-validation-qwen3-4b.md
│   ├── v3-semantic-repair-attempt-1-qwen3-4b.md
│   ├── v3-pipeline-validation-qwen3-4b.md
│   ├── v3-semantic-repair-v2-attempt-1-qwen3-4b.md
│   ├── v3-normalized-output-pipeline-v2-qwen3-4b.md
│   └── v3-enriched-pipeline-v2-pass-qwen3-4b.md
├── model-outputs/
│   ├── v3-qwen3-4b-output.json
│   ├── v3-repaired-qwen3-4b-output.json
│   ├── v3-semantic-repaired-qwen3-4b-output.json
│   ├── v3-semantic-repaired-schema-fixed-qwen3-4b-output.json
│   ├── v3-semantic-repaired-v2-qwen3-4b-output.json
│   ├── v3-semantic-repaired-v2-normalized-qwen3-4b-output.json
│   └── v3-enriched-qwen3-4b-output.json
├── prompts/
│   ├── requirements-analysis-v3.md
│   ├── requirements-analysis-repair-v1.md
│   ├── requirements-analysis-semantic-repair-v1.md
│   └── requirements-analysis-semantic-repair-v2.md
├── schemas/
│   └── requirements-analysis.schema.json
├── scripts/
│   ├── validate_model_output.py
│   ├── semantic_validate_model_output.py
│   ├── semantic_validate_model_output_v2.py
│   ├── validate_pipeline.py
│   ├── validate_pipeline_v2.py
│   ├── normalize_model_output.py
│   └── enrich_model_output.py
├── requirements.txt
└── README.md
```

## Workflow

### 1. Generate Local LLM Output

The model first generates requirements-analysis JSON.

Early results showed that even when the output looked professional, it could still contain unsupported assumptions or schema issues.

### 2. Validate Against JSON Schema

Schema validation checks whether the output has the expected structure.

Run:

```powershell
python .\scripts\validate_model_output.py .\model-outputs\v3-qwen3-4b-output.json
```

Example failure:

```text
FAIL: Model output does not match the schema.
```

This step catches issues such as:

* missing required keys
* wrong field names
* missing object fields
* unexpected extra properties

### 3. Run Semantic Validation

Schema validation only proves that the JSON shape is correct. It does not prove the output is useful.

Semantic validation checks quality rules such as:

* facts are traceable
* unknowns are captured
* blocked tasks explain dependencies
* test cases exist
* hallucination checks exist
* unsupported terms are avoided

Run:

```powershell
python .\scripts\semantic_validate_model_output_v2.py .\model-outputs\v3-enriched-qwen3-4b-output.json
```

### 4. Run Full Pipeline

The full pipeline enforces the correct validation order:

```text
schema validation → semantic validation
```

Run:

```powershell
python .\scripts\validate_pipeline_v2.py .\model-outputs\v3-enriched-qwen3-4b-output.json
```

Expected successful result:

```text
STEP 1: Schema validation
-------------------------
PASS: Model output matches the schema.

STEP 2: Semantic validation v2
------------------------------
PASS: Semantic validation v2 found no issues.
PIPELINE V2 RESULT: PASS
```

## Normalization

The normalizer fixes predictable structure problems in model output.

Run:

```powershell
python .\scripts\normalize_model_output.py .\model-outputs\v3-semantic-repaired-v2-qwen3-4b-output.json .\model-outputs\v3-semantic-repaired-v2-normalized-qwen3-4b-output.json
```

The normalizer can fix issues such as:

* missing top-level keys
* `name` used instead of `task`
* `name` used instead of `item`
* missing required fields
* extra fields not allowed by schema

Normalization does not claim to fix meaning. It only makes structure safer.

## Trusted-Context Enrichment

The enrichment step fills missing semantic content using trusted project context.

Run:

```powershell
python .\scripts\enrich_model_output.py .\model-outputs\v3-semantic-repaired-v2-normalized-qwen3-4b-output.json .\contexts\production-report-context.json .\model-outputs\v3-enriched-qwen3-4b-output.json
```

The trusted context provides:

* known facts
* required unknowns
* client questions
* required backend tasks
* frontend tasks
* database considerations
* test cases
* hallucination checks

This prevents the model from being the only source of truth.

## End-to-End CLI Workflow

The project includes a CLI runner that executes the full workflow:

```text
model output → normalize → enrich → validate
```

Run:

```powershell
python .\scripts\run_requirements_workflow.py `
  --input .\model-outputs\v3-semantic-repaired-v2-qwen3-4b-output.json `
  --context .\contexts\production-report-context.json `
  --normalized-output .\model-outputs\workflow-normalized-output.json `
  --enriched-output .\model-outputs\workflow-enriched-output.json
```

Expected result:

```text
STEP: Normalize model output
----------------------------
Normalized output written to: ...

STEP: Enrich normalized output
------------------------------
Enriched output written to: ...

STEP: Validate enriched output with pipeline v2
-----------------------------------------------
STEP 1: Schema validation
-------------------------
PASS: Model output matches the schema.

STEP 2: Semantic validation v2
------------------------------
PASS: Semantic validation v2 found no issues.
PIPELINE V2 RESULT: PASS

WORKFLOW RESULT: PASS
```

This command is the current main proof of the project workflow.

## Ollama API Generation

The project can generate local model output directly through Ollama instead of manually copying responses from the UI.

Generate raw model output:

```powershell
python .\scripts\generate_with_ollama.py `
  --model qwen3:4b `
  --prompt .\prompts\requirements-analysis-generation-v1.txt `
  --output .\model-outputs\ollama-generated-qwen3-4b-output.json
```

Then run the full workflow:

```powershell
python .\scripts\run_requirements_workflow.py `
  --input .\model-outputs\ollama-generated-qwen3-4b-output.json `
  --context .\contexts\production-report-context.json `
  --normalized-output .\model-outputs\ollama-generated-normalized-output.json `
  --enriched-output .\model-outputs\ollama-generated-enriched-output.json
```

Expected final result:

```text
WORKFLOW RESULT: PASS
```

This proves the project can move from local model generation to validated output without manual prompt-copying.

## Key Result

The strongest workflow so far is:

```text
weak model output
→ normalize structure
→ enrich from trusted context
→ schema validation
→ semantic validation v2
→ PASS
```

This demonstrates a production-oriented approach:

| Responsibility           | Owner              |
| ------------------------ | ------------------ |
| Drafting analysis        | LLM                |
| Enforcing JSON structure | Code               |
| Supplying known facts    | Trusted context    |
| Checking required fields | JSON Schema        |
| Checking usefulness      | Semantic validator |
| Accept/reject decision   | Pipeline           |

## Current Status

Completed:

* local Qwen3 4B baseline evaluation
* controlled prompt experiments
* schema validation
* repair prompt experiments
* semantic validation
* validation pipeline
* deterministic normalization
* trusted-context enrichment
* successful pipeline v2 pass

Next planned step:

```text
Create a single CLI command that runs normalize → enrich → validate automatically.
```

## Limitations

This project does not claim that a 4B local model can produce production-ready output by itself.

The main finding is the opposite:

```text
Prompting alone is not enough.
```

Reliable workflows need validation, deterministic repair, and trusted context.

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

## Requirements

```text
Python 3.10+
Ollama
qwen3:4b
```

Python dependency:

```text
jsonschema>=4.0.0
```

## Quick Sanity Check

Run the current end-to-end workflow:

```powershell
python .\scripts\run_requirements_workflow.py `
  --input .\model-outputs\v3-semantic-repaired-v2-qwen3-4b-output.json `
  --context .\contexts\production-report-context.json `
  --normalized-output .\model-outputs\workflow-normalized-output.json `
  --enriched-output .\model-outputs\workflow-enriched-output.json
```

Then validate the enriched output directly:

```powershell
python .\scripts\validate_pipeline_v2.py .\model-outputs\workflow-enriched-output.json
```

Expected result:

```text
PIPELINE V2 RESULT: PASS
```

## Portfolio Positioning

This project demonstrates practical LLM engineering skills:

* local model evaluation
* prompt testing
* schema-first design
* validation-first output handling
* deterministic normalization
* semantic validation
* trusted-context enrichment
* production-style rejection/acceptance pipeline

It is intentionally scoped and measurable instead of being a generic AI chatbot.

# Ollama API Workflow Pass - Qwen3 4B

## Purpose

This file records the first successful workflow where model output was generated directly through the local Ollama API instead of manually using the Ollama UI.

The goal was to test this flow:

```text
prompt file
→ Ollama API using qwen3:4b
→ raw model JSON
→ deterministic normalization
→ trusted-context enrichment
→ schema validation
→ semantic validation v2
→ pass
```

## Model

qwen3:4b

## Prompt File

```text
prompts/requirements-analysis-generation-v1.txt
```

## Raw Generated Output File

```text
model-outputs/ollama-generated-qwen3-4b-output.json
```

## Normalized Output File

```text
model-outputs/ollama-generated-normalized-output.json
```

## Enriched Output File

```text
model-outputs/ollama-generated-enriched-output.json
```

## Trusted Context File

```text
contexts/production-report-context.json
```

## Scripts Used

```text
scripts/generate_with_ollama.py
scripts/run_requirements_workflow.py
scripts/normalize_model_output.py
scripts/enrich_model_output.py
scripts/validate_pipeline_v2.py
```

## Generation Command

```powershell
python .\scripts\generate_with_ollama.py `
  --model qwen3:4b `
  --prompt .\prompts\requirements-analysis-generation-v1.txt `
  --output .\model-outputs\ollama-generated-qwen3-4b-output.json
```

## Initial Raw Output Validation

The raw Ollama-generated output failed pipeline validation because the model did not return all required schema sections.

```text
STEP 1: Schema validation
-------------------------
FAIL: Model output does not match the schema.

1. Path: $
   Error: 'backend_tasks' is a required property

2. Path: $
   Error: 'frontend_tasks' is a required property

3. Path: $
   Error: 'database_considerations' is a required property

4. Path: $
   Error: 'test_cases' is a required property

5. Path: $
   Error: 'hallucination_checks' is a required property

PIPELINE V2 RESULT: FAIL
Reason: Schema validation failed. Semantic validation v2 was skipped.
```

## Workflow Command

```powershell
python .\scripts\run_requirements_workflow.py `
  --input .\model-outputs\ollama-generated-qwen3-4b-output.json `
  --context .\contexts\production-report-context.json `
  --normalized-output .\model-outputs\ollama-generated-normalized-output.json `
  --enriched-output .\model-outputs\ollama-generated-enriched-output.json
```

## Final Workflow Result

```text
STEP: Normalize model output
----------------------------
Normalized output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\ollama-generated-normalized-output.json

STEP: Enrich normalized output
------------------------------
Enriched output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\ollama-generated-enriched-output.json

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
Normalized output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\ollama-generated-normalized-output.json
Enriched output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\ollama-generated-enriched-output.json
```

## Issue Found During API Integration

The first API attempt returned JSON content inside the `thinking` field while the final `response` field was empty.

The fix was to disable thinking in the Ollama API payload:

```json
{
  "think": false
}
```

After that, the model returned usable JSON in the expected response field.

## What This Proves

| Layer                       | Result | Notes                                                                       |
| --------------------------- | ------ | --------------------------------------------------------------------------- |
| Ollama API integration      | Pass   | The repo can now generate output directly from the local model.             |
| Raw model output validation | Fail   | The model still does not reliably produce complete schema-compliant output. |
| Normalization               | Pass   | Predictable schema issues can be fixed in code.                             |
| Trusted-context enrichment  | Pass   | Missing semantic content can be restored from trusted context.              |
| Pipeline v2 validation      | Pass   | Final enriched output satisfies schema and semantic quality checks.         |

## Key Learning

Direct Ollama API generation works, but local model output still needs validation and post-processing.

The successful pattern remains:

```text
LLM generates draft content
code normalizes structure
trusted context restores required meaning
validators decide acceptance
```

## Current Verdict

This is a stronger milestone than the manual UI-based workflow.

The project now demonstrates a working local LLM system path:

```text
prompt → local model API → validation-first processing pipeline
```

## Next Improvement Target

Update the README to show the Ollama API generation workflow and then commit this milestone.

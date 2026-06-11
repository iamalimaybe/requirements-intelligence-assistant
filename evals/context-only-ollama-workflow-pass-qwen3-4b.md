# Context-Only Ollama Workflow Pass - Qwen3 4B

## Purpose

This file records the first successful workflow where the system starts from trusted context JSON only.

The prompt is no longer manually provided. It is generated automatically from the context file.

The workflow tested:

```text
trusted context JSON
→ generated prompt
→ Ollama API generation
→ raw model JSON
→ deterministic normalization
→ trusted-context enrichment
→ schema validation
→ semantic validation v2
→ pass
```

## Model

```text
qwen3:4b
```

## Context File

```text
contexts/production-report-context.json
```

## Main Script

```text
scripts/run_ollama_requirements_workflow.py
```

## Supporting Scripts

```text
scripts/build_prompt_from_context.py
scripts/generate_with_ollama.py
scripts/run_requirements_workflow.py
scripts/normalize_model_output.py
scripts/enrich_model_output.py
scripts/validate_pipeline_v2.py
```

## Command

```powershell
python .\scripts\run_ollama_requirements_workflow.py `
  --model qwen3:4b `
  --context .\contexts\production-report-context.json `
  --generated-prompt-output .\scratch\context-only-generated-prompt.txt `
  --generated-output .\scratch\context-only-generated-output.json `
  --normalized-output .\scratch\context-only-normalized-output.json `
  --enriched-output .\scratch\context-only-enriched-output.json
```

## Result

```text
STEP: Build prompt from trusted context
---------------------------------------
Generated prompt written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\context-only-generated-prompt.txt

STEP: Generate output with Ollama
---------------------------------
Generated output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\context-only-generated-output.json

STEP: Normalize, enrich, and validate generated output
------------------------------------------------------

STEP: Normalize model output
----------------------------
Normalized output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\context-only-normalized-output.json

STEP: Enrich normalized output
------------------------------
Enriched output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\context-only-enriched-output.json

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

OLLAMA WORKFLOW RESULT: PASS
```

## What This Proves

The workflow can now start from a trusted requirement context file without a manually written prompt.

This moves the project from:

```text
prompt-driven demo
```

to:

```text
context-driven local LLM workflow
```

## Key Learning

The context file is now the source of truth.

The prompt is a generated runtime artifact, not the primary requirement artifact.

The accepted architecture is:

```text
trusted context
→ generated prompt
→ local LLM draft
→ deterministic normalization
→ trusted-context enrichment
→ schema and semantic validation
```

## Current Verdict

This is a strong production-style improvement.

The project is now closer to a reusable requirements intelligence workflow because adding a new requirement should primarily mean adding a new context JSON file.

# One-Command Ollama Workflow Pass - Qwen3 4B

## Purpose

This file records the first successful one-command workflow using a local Ollama model.

The workflow now runs:

```text
prompt file
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

## Command

```powershell
python .\scripts\run_ollama_requirements_workflow.py `
  --model qwen3:4b `
  --prompt .\prompts\requirements-analysis-generation-v1.txt `
  --context .\contexts\production-report-context.json `
  --generated-output .\model-outputs\one-command-generated-output.json `
  --normalized-output .\model-outputs\one-command-normalized-output.json `
  --enriched-output .\model-outputs\one-command-enriched-output.json
```

## Output Files

```text
model-outputs/one-command-generated-output.json
model-outputs/one-command-normalized-output.json
model-outputs/one-command-enriched-output.json
```

## Result

```text
STEP: Generate output with Ollama
---------------------------------
Generated output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\one-command-generated-output.json

STEP: Normalize, enrich, and validate generated output
------------------------------------------------------

STEP: Normalize model output
----------------------------
Normalized output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\one-command-normalized-output.json

STEP: Enrich normalized output
------------------------------
Enriched output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\one-command-enriched-output.json

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
Normalized output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\one-command-normalized-output.json
Enriched output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\one-command-enriched-output.json

OLLAMA WORKFLOW RESULT: PASS
Generated output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\one-command-generated-output.json
Normalized output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\one-command-normalized-output.json
Enriched output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\one-command-enriched-output.json
```

## What This Proves

The project no longer depends on manual model interaction.

It now has a repeatable local LLM workflow:

```text
single command
→ local model generation
→ validation-first processing
→ accepted structured output
```

## Key Learning

The model is still not trusted directly.

The system accepts output only after:

```text
schema validation
semantic validation
deterministic normalization
trusted-context enrichment
```

## Current Verdict

This is the strongest workflow milestone so far.

The repository now demonstrates a practical local LLM pipeline instead of a prompt-only experiment.

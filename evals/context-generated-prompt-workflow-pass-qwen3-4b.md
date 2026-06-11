# Context-Generated Prompt Workflow Pass - Qwen3 4B

## Purpose

This file records the first successful workflow where the prompt was generated from trusted context JSON instead of being manually hardcoded.

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

## Prompt Builder

```text
scripts/build_prompt_from_context.py
```

## Generated Prompt Output

```text
scratch/generated-prompt.txt
```

The generated prompt was written to `scratch/`, so it is treated as a local runtime artifact and is not committed.

## Commands

Generate prompt from trusted context:

```powershell
python .\scripts\build_prompt_from_context.py `
  --context .\contexts\production-report-context.json `
  --output .\scratch\generated-prompt.txt
```

Run workflow using generated prompt:

```powershell
python .\scripts\run_ollama_requirements_workflow.py `
  --model qwen3:4b `
  --prompt .\scratch\generated-prompt.txt `
  --context .\contexts\production-report-context.json `
  --generated-output .\scratch\context-generated-output.json `
  --normalized-output .\scratch\context-normalized-output.json `
  --enriched-output .\scratch\context-enriched-output.json
```

## Result

```text
STEP: Generate output with Ollama
---------------------------------
Generated output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\context-generated-output.json

STEP: Normalize, enrich, and validate generated output
------------------------------------------------------

STEP: Normalize model output
----------------------------
Normalized output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\context-normalized-output.json

STEP: Enrich normalized output
------------------------------
Enriched output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\scratch\context-enriched-output.json

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

The workflow is no longer tied to a manually written Production Report prompt.

Requirement-specific information now lives in trusted context JSON, and the prompt can be generated from that context.

This moves the project from:

```text
hardcoded prompt demo
```

to:

```text
context-driven local LLM workflow
```

## Key Learning

The LLM still generates draft content, but the source of truth is the trusted context.

The accepted system pattern is now:

```text
trusted context
→ generated prompt
→ local LLM draft
→ normalization
→ enrichment
→ validation
```

## Current Verdict

This is a meaningful architecture improvement.

The project is becoming reusable for more than one requirement, because new requirement contexts can be added without rewriting the prompt manually.

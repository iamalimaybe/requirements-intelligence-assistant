# Workflow CLI Pass - Qwen3 4B

## Purpose

This file records the first successful end-to-end CLI workflow run.

The goal was to replace scattered manual commands with a single workflow runner:

```text
model output → normalize → enrich → validate
```

## Model

qwen3:4b

## Input File

```text
model-outputs/v3-semantic-repaired-v2-qwen3-4b-output.json
```

## Trusted Context File

```text
contexts/production-report-context.json
```

## Workflow Script

```text
scripts/run_requirements_workflow.py
```

## Generated Files

```text
model-outputs/workflow-normalized-output.json
model-outputs/workflow-enriched-output.json
```

## Command Used

```powershell
python .\scripts\run_requirements_workflow.py `
  --input .\model-outputs\v3-semantic-repaired-v2-qwen3-4b-output.json `
  --context .\contexts\production-report-context.json `
  --normalized-output .\model-outputs\workflow-normalized-output.json `
  --enriched-output .\model-outputs\workflow-enriched-output.json
```

## Workflow Output

```text
STEP: Normalize model output
----------------------------
Normalized output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\workflow-normalized-output.json

STEP: Enrich normalized output
------------------------------
Enriched output written to: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\workflow-enriched-output.json

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
Normalized output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\workflow-normalized-output.json
Enriched output: D:\AI_LOCAL\projects\requirements-intelligence-assistant\model-outputs\workflow-enriched-output.json
```

## What This Proves

The project now has a reusable local workflow that can:

1. take imperfect local LLM output
2. normalize predictable schema issues
3. enrich missing semantic content from trusted context
4. validate structure through JSON Schema
5. validate business usefulness through semantic validation v2
6. return one clear pass/fail result

## Key Learning

The successful workflow does not depend on the model being perfect.

The reliable pattern is:

```text
LLM drafts content
code fixes structure
trusted context restores required meaning
validators decide acceptance
```

## Current Verdict

This is a portfolio-worthy milestone.

The project now demonstrates more than local model execution. It demonstrates validation-first LLM workflow design.

## Next Improvement Target

The next step should be to update the README with the CLI workflow command and then prepare a cleaner first public version of the repo.

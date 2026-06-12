# Run Report Validation - qwen3:4b

## Purpose

This evaluation records the addition of schema validation for the reproducible demo workflow report.

The project already validates model output, enriched output, semantic coverage, and negative regression cases. The next step was to validate the run evidence itself.

## Model

```text
qwen3:4b
```

Run locally through Ollama.

## Command

```powershell
python .\scripts\run_demo_multi_context_workflow.py --model qwen3:4b
```

## Added Files

```text
schemas/run-report.schema.json
scripts/validate_run_report.py
```

## Updated File

```text
scripts/run_demo_multi_context_workflow.py
```

## What Changed

The demo workflow now writes:

```text
scratch/demo-multi-context/run-report.json
```

Then validates that report before printing final success.

Expected validation step:

```text
STEP: Validate run report
-------------------------
PASS: Run report matches the schema.
```

## What the Report Captures

The report records:

```text
model
temperature
context discovery mode
context count
output paths
repair usage
per-context step results
multi-context regression result
durations
return codes
final workflow result
```

## Result

```text
DEMO MULTI-CONTEXT WORKFLOW RESULT: PASS
```

## Significance

This makes the workflow evidence structured and checkable.

The project now validates:

```text
LLM output structure
semantic groundedness
negative failure cases
multi-context regression
workflow run report
```

This strengthens the project’s validation-first positioning.
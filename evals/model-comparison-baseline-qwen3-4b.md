# Model Comparison Baseline - qwen3:4b

## Purpose

This evaluation records the first model comparison run using the current local baseline model.

The goal was not yet to compare multiple models, but to prove that the model comparison runner can execute the full reproducible demo workflow and summarize the result.

## Model

```text
qwen3:4b
```

Run locally through Ollama.

## Command

```powershell
python .\scripts\run_model_comparison.py --model qwen3:4b
```

## What the Runner Does

The model comparison runner executes:

```text
scripts/run_demo_multi_context_workflow.py
```

for each supplied model.

For each model, it collects:

```text
final result
context count
repair count
failed context count
multi-context regression result
run-report validation result
duration
```

## Output Files

```text
scratch/model-comparison/model-comparison-summary.json
scratch/model-comparison/qwen3-4b/run-report.json
```

These files are runtime artifacts and are ignored by Git.

## Result

```text
MODEL COMPARISON RESULT: PASS
```

## Significance

This establishes `qwen3:4b` as the first local baseline for future model comparisons.

Future runs can compare this baseline against larger or different local models using the same command shape:

```powershell
python .\scripts\run_model_comparison.py `
  --model qwen3:4b `
  --model <another-model>
```

## Current Limitation

This is not yet a true multi-model comparison because only one model was tested.

The value of this milestone is that the comparison runner is now proven to work with the full validation pipeline.
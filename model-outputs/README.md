# Model Outputs

This folder contains selected local LLM outputs used by the evaluation workflow.

These files are intentionally committed because they demonstrate the progression from weak model output to validated enriched output.

## Why These Files Exist

The project evaluates a local LLM workflow where model output is treated as untrusted.

The saved outputs show different stages:

```text
raw model output
→ repaired output
→ semantic repair attempt
→ normalized output
→ enriched validated output
```

## Important Note

These outputs are not all final-quality results.

Some files intentionally show failures so the validation pipeline has evidence to test against.

Examples:

* schema failures
* semantic validation failures
* outputs with missing required fields
* outputs that pass schema but fail quality checks
* final enriched output that passes pipeline validation

## Current Passing Output

The current validated output is:

```text
v3-enriched-qwen3-4b-output.json
```

It passes:

```text
scripts/validate_pipeline_v2.py
```

## Generated Workflow Outputs

The workflow runner may produce files such as:

```text
workflow-normalized-output.json
workflow-enriched-output.json
```

These are useful for demonstrating the current CLI workflow. Future scratch outputs should go under a local ignored folder such as:

```text
scratch/
```

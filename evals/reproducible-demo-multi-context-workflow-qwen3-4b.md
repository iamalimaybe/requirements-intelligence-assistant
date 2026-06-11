# Reproducible Multi-Context Demo Workflow - qwen3:4b

## Purpose

This evaluation records the first reproducible demo workflow that regenerates outputs before running validation.

Earlier regression commands depended on existing files in `scratch/`. Since `scratch/` is ignored by Git, that was weak as a portfolio proof.

This demo workflow fixes that by regenerating the outputs for both requirement contexts before running multi-context regression tests.

## Model

```text
qwen3:4b
```

Run locally through Ollama.

## Command

```powershell
python .\scripts\run_demo_multi_context_workflow.py --model qwen3:4b
```

## Workflow

```text
Production Report context
-> generate prompt
-> call Ollama
-> normalize
-> enrich
-> validate with pipeline v3

Review Moderation context
-> generate prompt
-> call Ollama
-> repair malformed JSON if needed
-> normalize
-> enrich
-> validate with pipeline v3

Both enriched outputs
-> multi-context regression tests
```

## Result

```text
DEMO MULTI-CONTEXT WORKFLOW RESULT: PASS
```

## Important Observation

The Review Moderation context initially produced malformed JSON from the local model.

The raw failed response was saved to:

```text
scratch/demo-multi-context/review-moderation-generated-output.failed-generation.txt
```

The workflow then used one JSON repair attempt and continued successfully.

This confirms that small local models can still fail strict JSON generation, even when prompted carefully.

## What This Proves

This milestone proves:

```text
outputs can be regenerated
malformed JSON can be repaired once
normalized/enriched outputs still need validation
both contexts pass positive validation
both contexts reject controlled negative cases
```

This is stronger than relying on pre-existing output files.

## Portfolio Significance

The project now has a clone-and-run style proof command:

```powershell
python .\scripts\run_demo_multi_context_workflow.py --model qwen3:4b
```

That command demonstrates:

- local model generation
- failure handling for malformed JSON
- deterministic normalization
- trusted-context enrichment
- schema validation
- semantic validation v3
- multi-context regression testing

## Current Limitation

The repair fallback only handles malformed JSON generation.

It does not make the model output trustworthy by itself. The repaired output still must pass the deterministic workflow:

```text
normalize -> enrich -> schema validation -> semantic validation v3 -> regression tests
```

The next stronger step would be to add a structured run report so each demo run records model name, context, timings, repair usage, validation result, and output paths.
# Model Comparison: qwen3:4b vs qwen3:8b

## Purpose

This evaluation compares the current local baseline model against a larger model from the same family.

The goal was to check whether a larger local model improves reliability enough to justify runtime on the current hardware.

## Models

```text
qwen3:4b
qwen3:8b
```

Both were run locally through Ollama.

## Command

```powershell
python .\scripts\run_model_comparison.py `
  --model qwen3:4b `
  --model qwen3:8b
```

## Warm Run Result Summary

```text
qwen3:4b  result=pass  contexts=3  repairs=1  failed_contexts=0  duration=85.283s
qwen3:8b  result=pass  contexts=3  repairs=0  failed_contexts=0  duration=67.501s
```

## Validation Results

Both models passed:

```text
trusted context validation
per-context workflow validation
schema validation
semantic validation v3
multi-context regression
run-report validation
```

## Key Finding

```text
qwen3:8b passed the full workflow with zero JSON repairs and completed faster than qwen3:4b in the warm run.
```

This suggests that `qwen3:8b` may be a better default candidate than expected on the current hardware.

## Context-Level qwen3:8b Observation

For `qwen3:8b`, the context durations were:

```text
payment-webhook: 22.373s
production-report: 15.114s
review-moderation: 21.158s
```

All three contexts passed without JSON repair.

## Cold-Start Note

An earlier first run after pulling `qwen3:8b` was much slower.

That first run should be treated as a cold-start or model-load outlier, not as the main performance comparison.

## Conclusion

Across repeated warm runs, both `qwen3:4b` and `qwen3:8b` passed the full validation workflow.

The second warm run favored `qwen3:8b` on both reliability and duration:

```text
qwen3:4b: 85.283s, repairs=1
qwen3:8b: 67.501s, repairs=0
```

The third warm run favored qwen3:4b on duration, but qwen3:8b still had better JSON reliability:

```text
qwen3:4b: 47.313s, repairs=1
qwen3:8b: 67.552s, repairs=0
```

qwen3:8b consistently avoided JSON repair across the repeated warm runs. qwen3:4b remained faster in the latest run but still required repair.


## Current Recommendation

```text
Fast iteration model: qwen3:4b
Cleaner reliability candidate: qwen3:8b
```

## Next Step

Keep qwen3:4b as the documented fast default for now, and use qwen3:8b when comparing reliability or running a higher-confidence local validation pass.
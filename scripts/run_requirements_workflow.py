"""
Run the requirements-analysis processing workflow.

Purpose:
- Normalize local LLM output into the expected schema shape.
- Enrich normalized output using trusted requirement context.
- Stop before validation so validation can be handled by the caller.

Workflow:
    model output
    -> normalize
    -> enrich with trusted context
    -> processed output

Usage:
    python scripts/run_requirements_workflow.py ^
      --input model-outputs/v3-semantic-repaired-v2-qwen3-4b-output.json ^
      --context contexts/production-report-context.json ^
      --normalized-output model-outputs/workflow-normalized-output.json ^
      --enriched-output model-outputs/workflow-enriched-output.json
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

NORMALIZER = PROJECT_ROOT / "scripts" / "normalize_model_output.py"
ENRICHER = PROJECT_ROOT / "scripts" / "enrich_model_output.py"


def run_step(name: str, command: list[str]) -> int:
    print()
    print(f"STEP: {name}")
    print("-" * (len(name) + 6))

    completed_process = subprocess.run(command, cwd=PROJECT_ROOT)
    return completed_process.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run normalize -> enrich workflow for requirements-analysis model output."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to raw or near-valid model output JSON.",
    )

    parser.add_argument(
        "--context",
        required=True,
        help="Path to trusted requirement context JSON.",
    )

    parser.add_argument(
        "--normalized-output",
        required=True,
        help="Path where normalized JSON output should be written.",
    )

    parser.add_argument(
        "--enriched-output",
        required=True,
        help="Path where enriched JSON output should be written.",
    )

    return parser.parse_args()


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def main() -> int:
    args = parse_args()

    input_path = resolve_project_path(args.input)
    context_path = resolve_project_path(args.context)
    normalized_output_path = resolve_project_path(args.normalized_output)
    enriched_output_path = resolve_project_path(args.enriched_output)

    normalize_result = run_step(
        "Normalize model output",
        [
            sys.executable,
            str(NORMALIZER),
            str(input_path),
            str(normalized_output_path),
        ],
    )

    if normalize_result != 0:
        print()
        print("WORKFLOW RESULT: FAIL")
        print("Reason: Normalization failed.")
        return normalize_result

    enrich_result = run_step(
        "Enrich normalized output",
        [
            sys.executable,
            str(ENRICHER),
            str(normalized_output_path),
            str(context_path),
            str(enriched_output_path),
        ],
    )

    if enrich_result != 0:
        print()
        print("WORKFLOW RESULT: FAIL")
        print("Reason: Enrichment failed.")
        return enrich_result

    print()
    print("WORKFLOW RESULT: PASS")
    print(f"Normalized output: {normalized_output_path}")
    print(f"Enriched output: {enriched_output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
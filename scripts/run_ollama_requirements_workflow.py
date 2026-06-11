"""
Run the full local Ollama requirements-analysis workflow.

Purpose:
- Generate requirements-analysis JSON from a local Ollama model.
- Normalize predictable schema issues.
- Enrich missing semantic content from trusted context.
- Validate the final output using pipeline v2.

Workflow:
    prompt file
    -> Ollama model output
    -> normalize
    -> enrich with trusted context
    -> schema validation
    -> semantic validation v2

Usage:
    python scripts/run_ollama_requirements_workflow.py ^
      --model qwen3:4b ^
      --prompt prompts/requirements-analysis-generation-v1.txt ^
      --context contexts/production-report-context.json ^
      --generated-output model-outputs/one-command-generated-output.json ^
      --normalized-output model-outputs/one-command-normalized-output.json ^
      --enriched-output model-outputs/one-command-enriched-output.json
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

GENERATOR = PROJECT_ROOT / "scripts" / "generate_with_ollama.py"
WORKFLOW = PROJECT_ROOT / "scripts" / "run_requirements_workflow.py"


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def run_step(name: str, command: list[str]) -> int:
    print()
    print(f"STEP: {name}")
    print("-" * (len(name) + 6))

    completed_process = subprocess.run(command, cwd=PROJECT_ROOT)
    return completed_process.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Ollama generation plus normalize/enrich/validate workflow."
    )

    parser.add_argument(
        "--model",
        default="qwen3:4b",
        help="Ollama model name.",
    )

    parser.add_argument(
        "--prompt",
        required=True,
        help="Path to prompt text file.",
    )

    parser.add_argument(
        "--context",
        required=True,
        help="Path to trusted requirement context JSON.",
    )

    parser.add_argument(
        "--generated-output",
        required=True,
        help="Path where raw generated model JSON should be written.",
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

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Generation temperature.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    prompt_path = resolve_project_path(args.prompt)
    context_path = resolve_project_path(args.context)
    generated_output_path = resolve_project_path(args.generated_output)
    normalized_output_path = resolve_project_path(args.normalized_output)
    enriched_output_path = resolve_project_path(args.enriched_output)

    generate_result = run_step(
        "Generate output with Ollama",
        [
            sys.executable,
            str(GENERATOR),
            "--model",
            args.model,
            "--prompt",
            str(prompt_path),
            "--output",
            str(generated_output_path),
            "--temperature",
            str(args.temperature),
        ],
    )

    if generate_result != 0:
        print()
        print("OLLAMA WORKFLOW RESULT: FAIL")
        print("Reason: Ollama generation failed.")
        return generate_result

    workflow_result = run_step(
        "Normalize, enrich, and validate generated output",
        [
            sys.executable,
            str(WORKFLOW),
            "--input",
            str(generated_output_path),
            "--context",
            str(context_path),
            "--normalized-output",
            str(normalized_output_path),
            "--enriched-output",
            str(enriched_output_path),
        ],
    )

    if workflow_result != 0:
        print()
        print("OLLAMA WORKFLOW RESULT: FAIL")
        print("Reason: Normalize/enrich/validate workflow failed.")
        return workflow_result

    print()
    print("OLLAMA WORKFLOW RESULT: PASS")
    print(f"Generated output: {generated_output_path}")
    print(f"Normalized output: {normalized_output_path}")
    print(f"Enriched output: {enriched_output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
Run the full validation pipeline for requirements-analysis model output.

Purpose:
- Enforce correct validation order.
- Run schema validation first.
- Run semantic validation only after schema validation passes.
- Return one clear production-style pass/fail result.

Usage:
    python scripts/validate_pipeline.py model-outputs/v3-semantic-repaired-qwen3-4b-output.json
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VALIDATOR = PROJECT_ROOT / "scripts" / "validate_model_output.py"
SEMANTIC_VALIDATOR = PROJECT_ROOT / "scripts" / "semantic_validate_model_output.py"


def run_command(command: list[str]) -> int:
    completed_process = subprocess.run(command, cwd=PROJECT_ROOT)
    return completed_process.returncode


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python scripts/validate_pipeline.py <model-output-json-path>")
        return 2

    output_path = Path(sys.argv[1]).resolve()

    print("STEP 1: Schema validation")
    print("-------------------------")
    schema_result = run_command(
        [sys.executable, str(SCHEMA_VALIDATOR), str(output_path)]
    )

    if schema_result != 0:
        print("PIPELINE RESULT: FAIL")
        print("Reason: Schema validation failed. Semantic validation was skipped.")
        return 1

    print()
    print("STEP 2: Semantic validation")
    print("---------------------------")
    semantic_result = run_command(
        [sys.executable, str(SEMANTIC_VALIDATOR), str(output_path)]
    )

    if semantic_result != 0:
        print("PIPELINE RESULT: FAIL")
        print("Reason: Semantic validation failed.")
        return 1

    print("PIPELINE RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
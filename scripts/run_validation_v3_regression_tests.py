import subprocess
import sys
from pathlib import Path
from typing import List


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PIPELINE_V3 = PROJECT_ROOT / "scripts" / "validate_pipeline_v3.py"
NEGATIVE_TEST_RUNNER = PROJECT_ROOT / "scripts" / "run_validation_v3_negative_tests.py"


def run_step(name: str, command: List[str]) -> int:
    print()
    print(f"STEP: {name}")
    print("-" * (len(name) + 6))

    completed_process = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
    )

    return completed_process.returncode


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/run_validation_v3_regression_tests.py "
            "<valid_model_output_json> <context_json>",
            file=sys.stderr,
        )
        return 2

    valid_output_path = resolve_project_path(sys.argv[1])
    context_path = resolve_project_path(sys.argv[2])

    positive_result = run_step(
        "Positive validation test",
        [
            sys.executable,
            str(PIPELINE_V3),
            str(valid_output_path),
            str(context_path),
        ],
    )

    if positive_result != 0:
        print()
        print("REGRESSION TEST RESULT: FAIL")
        print("Reason: Known-good output failed pipeline v3 validation.")
        return positive_result

    negative_result = run_step(
        "Negative validation tests",
        [
            sys.executable,
            str(NEGATIVE_TEST_RUNNER),
            str(valid_output_path),
            str(context_path),
        ],
    )

    if negative_result != 0:
        print()
        print("REGRESSION TEST RESULT: FAIL")
        print("Reason: Known-bad outputs were not rejected correctly.")
        return negative_result

    print()
    print("REGRESSION TEST RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
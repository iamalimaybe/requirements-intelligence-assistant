import subprocess
import sys
from pathlib import Path
from typing import List


def run_step(step_name: str, command: List[str]) -> bool:
    print(f"Running {step_name}...")

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if completed.stdout.strip():
        print(completed.stdout.strip())

    if completed.stderr.strip():
        print(completed.stderr.strip(), file=sys.stderr)

    return completed.returncode == 0


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/validate_pipeline_v3.py "
            "<model_output_json> <context_json>",
            file=sys.stderr,
        )
        return 2

    model_output_path = Path(sys.argv[1])
    context_path = Path(sys.argv[2])
    script_dir = Path(__file__).resolve().parent

    schema_validator_path = script_dir / "validate_model_output.py"
    semantic_validator_path = script_dir / "semantic_validate_model_output_v3.py"

    if not schema_validator_path.exists():
        print(f"PIPELINE V3 RESULT: FAIL")
        print(f"- Missing schema validator: {schema_validator_path}")
        return 1

    if not semantic_validator_path.exists():
        print(f"PIPELINE V3 RESULT: FAIL")
        print(f"- Missing semantic validator: {semantic_validator_path}")
        return 1

    schema_passed = run_step(
        "schema validation",
        [
            sys.executable,
            str(schema_validator_path),
            str(model_output_path),
        ],
    )

    if not schema_passed:
        print("PIPELINE V3 RESULT: FAIL")
        return 1

    semantic_passed = run_step(
        "semantic validation v3",
        [
            sys.executable,
            str(semantic_validator_path),
            str(model_output_path),
            str(context_path),
        ],
    )

    if not semantic_passed:
        print("PIPELINE V3 RESULT: FAIL")
        return 1

    print("PIPELINE V3 RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
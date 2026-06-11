import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGRESSION_RUNNER = PROJECT_ROOT / "scripts" / "run_validation_v3_regression_tests.py"


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def parse_cases(args: List[str]) -> List[Tuple[Path, Path]]:
    if len(args) < 2 or len(args) % 2 != 0:
        raise ValueError(
            "Expected pairs of <enriched_output_json> <context_json>."
        )

    cases = []

    for index in range(0, len(args), 2):
        output_path = resolve_project_path(args[index])
        context_path = resolve_project_path(args[index + 1])
        cases.append((output_path, context_path))

    return cases


def run_case(case_number: int, output_path: Path, context_path: Path) -> int:
    print()
    print(f"CONTEXT CASE {case_number}")
    print("-" * 14)
    print(f"Output: {output_path}")
    print(f"Context: {context_path}")

    completed_process = subprocess.run(
        [
            sys.executable,
            str(REGRESSION_RUNNER),
            str(output_path),
            str(context_path),
        ],
        cwd=PROJECT_ROOT,
    )

    return completed_process.returncode


def main() -> int:
    try:
        cases = parse_cases(sys.argv[1:])
    except ValueError as error:
        print("Usage:")
        print(
            "  python scripts/run_multi_context_regression_tests.py "
            "<enriched_output_json> <context_json> "
            "[<enriched_output_json> <context_json> ...]"
        )
        print()
        print(f"ERROR: {error}")
        return 2

    failures = []

    for case_number, (output_path, context_path) in enumerate(cases, start=1):
        result = run_case(case_number, output_path, context_path)

        if result != 0:
            failures.append((case_number, output_path, context_path))

    if failures:
        print()
        print("MULTI-CONTEXT REGRESSION RESULT: FAIL")

        for case_number, output_path, context_path in failures:
            print(f"- Case {case_number} failed")
            print(f"  Output: {output_path}")
            print(f"  Context: {context_path}")

        return 1

    print()
    print("MULTI-CONTEXT REGRESSION RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
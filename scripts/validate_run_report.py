import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "run-report.schema.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a demo workflow run report against its JSON schema."
    )

    parser.add_argument(
        "report",
        help="Path to run-report.json.",
    )

    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA_PATH),
        help="Path to run report JSON schema.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_path = Path(args.report)
    schema_path = Path(args.schema)

    if not report_path.exists():
        print(f"FAIL: Run report does not exist: {report_path}")
        return 1

    if not schema_path.exists():
        print(f"FAIL: Run report schema does not exist: {schema_path}")
        return 1

    try:
        report = load_json(report_path)
    except json.JSONDecodeError as error:
        print(f"FAIL: Run report is not valid JSON: {report_path}")
        print(f"Reason: {error}")
        return 1

    try:
        schema = load_json(schema_path)
    except json.JSONDecodeError as error:
        print(f"FAIL: Run report schema is not valid JSON: {schema_path}")
        print(f"Reason: {error}")
        return 1

    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(report),
        key=lambda validation_error: list(validation_error.path),
    )

    if errors:
        print("FAIL: Run report does not match the schema.")

        for error in errors:
            path = ".".join(str(part) for part in error.path)
            location = path if path else "<root>"
            print(f"- {location}: {error.message}")

        return 1

    print("PASS: Run report matches the schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
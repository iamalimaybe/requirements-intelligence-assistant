import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "requirements-context.schema.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate trusted requirement context JSON files."
    )

    parser.add_argument(
        "contexts",
        nargs="+",
        help="One or more context JSON files to validate.",
    )

    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA_PATH),
        help="Path to requirements context JSON schema.",
    )

    return parser.parse_args()


def format_error_path(error_path: Any) -> str:
    path_parts = [str(part) for part in error_path]
    return ".".join(path_parts) if path_parts else "<root>"


def validate_context_file(
    context_path: Path,
    schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    if not context_path.exists():
        return [f"Context file does not exist: {context_path}"]

    try:
        context_data = load_json(context_path)
    except json.JSONDecodeError as error:
        return [f"Context file is not valid JSON: {context_path}. Reason: {error}"]

    validator = Draft202012Validator(schema)
    validation_errors = sorted(
        validator.iter_errors(context_data),
        key=lambda validation_error: list(validation_error.path),
    )

    for error in validation_errors:
        location = format_error_path(error.path)
        errors.append(f"{context_path} :: {location}: {error.message}")

    return errors


def main() -> int:
    args = parse_args()
    schema_path = Path(args.schema)

    if not schema_path.exists():
        print(f"FAIL: Context schema does not exist: {schema_path}")
        return 1

    try:
        schema = load_json(schema_path)
    except json.JSONDecodeError as error:
        print(f"FAIL: Context schema is not valid JSON: {schema_path}")
        print(f"Reason: {error}")
        return 1

    all_errors: list[str] = []

    for context_arg in args.contexts:
        context_path = Path(context_arg)
        all_errors.extend(validate_context_file(context_path, schema))

    if all_errors:
        print("FAIL: One or more trusted context files are invalid.")

        for error in all_errors:
            print(f"- {error}")

        return 1

    print(f"PASS: {len(args.contexts)} trusted context file(s) match the schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
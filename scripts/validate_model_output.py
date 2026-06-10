"""
Validate local LLM output against the requirements-analysis JSON schema.

Purpose:
- Treat model output as untrusted.
- Verify that generated JSON matches the expected contract.
- Print clear validation errors for missing fields, wrong field names, wrong types, or unsupported values.

Usage:
    python scripts/validate_model_output.py model-outputs/v3-qwen3-4b-output.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, exceptions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "requirements-analysis.schema.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in {path}: line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error


def format_error_path(error: exceptions.ValidationError) -> str:
    if not error.absolute_path:
        return "$"

    return "$." + ".".join(str(part) for part in error.absolute_path)


def validate_output(schema_path: Path, output_path: Path) -> int:
    schema = load_json(schema_path)
    output = load_json(output_path)

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    errors = sorted(
        validator.iter_errors(output),
        key=lambda validation_error: list(validation_error.absolute_path),
    )

    if not errors:
        print("PASS: Model output matches the schema.")
        return 0

    print("FAIL: Model output does not match the schema.")
    print()

    for index, error in enumerate(errors, start=1):
        print(f"{index}. Path: {format_error_path(error)}")
        print(f"   Error: {error.message}")
        print()

    return 1


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python scripts/validate_model_output.py <model-output-json-path>")
        return 2

    output_path = Path(sys.argv[1]).resolve()

    try:
        return validate_output(DEFAULT_SCHEMA_PATH, output_path)
    except Exception as error:
        print(f"ERROR: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
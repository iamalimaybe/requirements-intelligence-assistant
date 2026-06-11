"""
Normalize requirements-analysis model output into the expected schema shape.

Purpose:
- Fix predictable structure issues deterministically.
- Avoid using the LLM for simple schema repairs.
- Preserve existing model content where possible.
- Do not claim the output is semantically good.

This script handles issues such as:
- missing top-level keys
- model using "name" instead of "task"
- model using "name" instead of "item"
- missing required object fields
- extra fields not allowed by schema

Usage:
    python scripts/normalize_model_output.py <input-json-path> <output-json-path>

Example:
    python scripts/normalize_model_output.py ^
      model-outputs/v3-semantic-repaired-v2-qwen3-4b-output.json ^
      model-outputs/v3-semantic-repaired-v2-normalized-qwen3-4b-output.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {"ready", "blocked", "optional"}
ALLOWED_HALLUCINATION_RESULTS = {"pass", "fail", "warning", "blocked"}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Expected top-level JSON object.")

    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


def ensure_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized: list[str] = []

    for item in value:
        if isinstance(item, str) and item.strip():
            normalized.append(item.strip())

    return normalized


def normalize_status(value: Any) -> str:
    if isinstance(value, str) and value in ALLOWED_STATUSES:
        return value

    return "optional"


def normalize_depends_on(value: Any, fallback: str | None = None, status: str = "optional") -> list[str]:
    if isinstance(value, list):
        dependencies = [
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        ]

        if dependencies:
            return dependencies

    if status == "blocked" and fallback:
        return [fallback]

    return []


def first_non_blank(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def normalize_task(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    task = first_non_blank(item.get("task"), item.get("name"), item.get("description"))
    if not task:
        return None

    status = normalize_status(item.get("status"))
    reason = first_non_blank(item.get("reason"))

    if not reason:
        reason = "Model output did not provide a reason."

    return {
        "task": task,
        "status": status,
        "reason": reason,
        "depends_on": normalize_depends_on(
            item.get("depends_on"),
            fallback=task,
            status=status,
        ),
    }


def normalize_database_consideration(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    consideration = first_non_blank(item.get("item"), item.get("name"), item.get("description"))
    if not consideration:
        return None

    status = normalize_status(item.get("status"))
    reason = first_non_blank(item.get("reason"))

    if not reason:
        reason = "Model output did not provide a reason."

    return {
        "item": consideration,
        "status": status,
        "reason": reason,
        "depends_on": normalize_depends_on(
            item.get("depends_on"),
            fallback=consideration,
            status=status,
        ),
    }


def normalize_test_case(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    name = first_non_blank(item.get("name"), item.get("test"), item.get("description"))
    given = first_non_blank(item.get("given"), item.get("input"))
    expected = first_non_blank(item.get("expected"), item.get("expected_output"))

    if not name and not given and not expected:
        return None

    status = normalize_status(item.get("status"))

    return {
        "name": name or "Unnamed test case",
        "status": status,
        "given": given,
        "expected": expected,
        "depends_on": normalize_depends_on(
            item.get("depends_on"),
            fallback=name or "test case dependency",
            status=status,
        ),
    }


def normalize_hallucination_check(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    check = first_non_blank(item.get("check"), item.get("name"), item.get("description"))
    result = item.get("result")

    if not isinstance(result, str) or result not in ALLOWED_HALLUCINATION_RESULTS:
        result = "warning"

    notes = first_non_blank(item.get("notes"), item.get("reason"))

    if not check and not notes:
        return None

    return {
        "check": check or "Unspecified hallucination check",
        "result": result,
        "notes": notes or "Model output did not provide notes.",
    }


def normalize_list(value: Any, normalizer) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    normalized: list[dict[str, Any]] = []

    for item in value:
        normalized_item = normalizer(item)
        if normalized_item is not None:
            normalized.append(normalized_item)

    return normalized


def normalize_output(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "facts_used": ensure_string_list(output.get("facts_used")),
        "unknowns": ensure_string_list(output.get("unknowns")),
        "client_questions": ensure_string_list(output.get("client_questions")),
        "backend_tasks": normalize_list(output.get("backend_tasks"), normalize_task),
        "frontend_tasks": normalize_list(output.get("frontend_tasks"), normalize_task),
        "database_considerations": normalize_list(
            output.get("database_considerations"),
            normalize_database_consideration,
        ),
        "test_cases": normalize_list(output.get("test_cases"), normalize_test_case),
        "hallucination_checks": normalize_list(
            output.get("hallucination_checks"),
            normalize_hallucination_check,
        ),
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage:")
        print("  python scripts/normalize_model_output.py <input-json-path> <output-json-path>")
        return 2

    input_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()

    try:
        raw_output = load_json(input_path)
        normalized_output = normalize_output(raw_output)
        write_json(output_path, normalized_output)
        print(f"Normalized output written to: {output_path}")
        return 0
    except Exception as error:
        print(f"ERROR: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
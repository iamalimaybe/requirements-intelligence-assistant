"""
Enrich normalized requirements-analysis model output using trusted requirement context.

Purpose:
- Preserve useful model-generated content.
- Fill missing semantic content from trusted context.
- Avoid relying on the model to remember required facts, unknowns, test cases, and risk checks.
- Produce output that can be validated by the stricter pipeline.

This script assumes structure has already been normalized or can be normalized before enrichment.

Usage:
    python scripts/enrich_model_output.py <model-output-json-path> <context-json-path> <enriched-output-json-path>

Example:
    python scripts/enrich_model_output.py ^
      model-outputs/v3-semantic-repaired-v2-normalized-qwen3-4b-output.json ^
      contexts/production-report-context.json ^
      model-outputs/v3-enriched-qwen3-4b-output.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from normalize_model_output import normalize_output


RISKY_TEST_VALUE_TERMS = [
    "example_",
    "2023-",
    "manager_a",
    "companycode=abc",
    "'example",
]


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


def normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def merge_string_lists(existing: list[str], required: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for value in [*existing, *required]:
        if not isinstance(value, str) or not value.strip():
            continue

        key = normalize_text(value)

        if key not in seen:
            merged.append(value.strip())
            seen.add(key)

    return merged


def item_key(item: dict[str, Any], key_field: str) -> str:
    value = item.get(key_field)

    if isinstance(value, str):
        return normalize_text(value)

    return ""


def merge_objects(
    existing: list[dict[str, Any]],
    required: list[dict[str, Any]],
    key_field: str,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in [*existing, *required]:
        if not isinstance(item, dict):
            continue

        key = item_key(item, key_field)

        if not key:
            continue

        if key not in seen:
            merged.append(item)
            seen.add(key)

    return merged


def contains_risky_test_values(test_case: dict[str, Any]) -> bool:
    dumped = json.dumps(test_case, ensure_ascii=False).lower()
    return any(term in dumped for term in RISKY_TEST_VALUE_TERMS)


def filter_test_cases(test_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        test_case
        for test_case in test_cases
        if not contains_risky_test_values(test_case)
    ]


def enrich_output(model_output: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    normalized_model_output = normalize_output(model_output)

    required_backend_tasks = normalize_output(
        {"backend_tasks": context.get("required_backend_tasks", [])}
    )["backend_tasks"]

    required_frontend_tasks = normalize_output(
        {"frontend_tasks": context.get("required_frontend_tasks", [])}
    )["frontend_tasks"]

    required_database_considerations = normalize_output(
        {
            "database_considerations": context.get(
                "required_database_considerations",
                [],
            )
        }
    )["database_considerations"]

    required_test_cases = normalize_output(
        {"test_cases": context.get("required_test_cases", [])}
    )["test_cases"]

    required_hallucination_checks = normalize_output(
        {
            "hallucination_checks": context.get(
                "required_hallucination_checks",
                [],
            )
        }
    )["hallucination_checks"]

    safe_existing_test_cases = filter_test_cases(
        normalized_model_output.get("test_cases", [])
    )

    enriched = {
        "facts_used": merge_string_lists(
            normalized_model_output.get("facts_used", []),
            context.get("known_facts", []),
        ),
        "unknowns": merge_string_lists(
            normalized_model_output.get("unknowns", []),
            context.get("required_unknowns", []),
        ),
        "client_questions": merge_string_lists(
            normalized_model_output.get("client_questions", []),
            context.get("client_questions", []),
        ),
        "backend_tasks": merge_objects(
            normalized_model_output.get("backend_tasks", []),
            required_backend_tasks,
            "task",
        ),
        "frontend_tasks": merge_objects(
            normalized_model_output.get("frontend_tasks", []),
            required_frontend_tasks,
            "task",
        ),
        "database_considerations": merge_objects(
            normalized_model_output.get("database_considerations", []),
            required_database_considerations,
            "item",
        ),
        "test_cases": merge_objects(
            safe_existing_test_cases,
            required_test_cases,
            "name",
        ),
        "hallucination_checks": merge_objects(
            normalized_model_output.get("hallucination_checks", []),
            required_hallucination_checks,
            "check",
        ),
    }

    return normalize_output(enriched)


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage:")
        print(
            "  python scripts/enrich_model_output.py "
            "<model-output-json-path> <context-json-path> <enriched-output-json-path>"
        )
        return 2

    model_output_path = Path(sys.argv[1]).resolve()
    context_path = Path(sys.argv[2]).resolve()
    enriched_output_path = Path(sys.argv[3]).resolve()

    try:
        model_output = load_json(model_output_path)
        context = load_json(context_path)
        enriched_output = enrich_output(model_output, context)
        write_json(enriched_output_path, enriched_output)
        print(f"Enriched output written to: {enriched_output_path}")
        return 0
    except Exception as error:
        print(f"ERROR: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
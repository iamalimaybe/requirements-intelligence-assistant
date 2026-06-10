"""
Run lightweight semantic checks on requirements-analysis model output.

Purpose:
- JSON Schema checks structure only.
- This script checks content quality and usefulness.
- A schema-valid output can still be semantically weak.

Usage:
    python scripts/semantic_validate_model_output.py model-outputs/v3-repaired-qwen3-4b-output.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in {path}: line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError("Expected top-level JSON object.")

    return data


def is_blank(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def collect_items(output: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    sections = [
        "backend_tasks",
        "frontend_tasks",
        "database_considerations",
        "test_cases",
        "hallucination_checks",
    ]

    items: list[tuple[str, dict[str, Any]]] = []

    for section in sections:
        section_value = output.get(section, [])
        if not isinstance(section_value, list):
            continue

        for item in section_value:
            if isinstance(item, dict):
                items.append((section, item))

    return items


def run_semantic_checks(output: dict[str, Any]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    facts_used = output.get("facts_used", [])
    unknowns = output.get("unknowns", [])
    client_questions = output.get("client_questions", [])
    backend_tasks = output.get("backend_tasks", [])

    if not facts_used:
        failures.append("facts_used is empty, so the output has no traceability to provided facts.")

    blocked_items = [
        (section, item)
        for section, item in collect_items(output)
        if item.get("status") == "blocked"
    ]

    if blocked_items and not unknowns:
        failures.append("There are blocked items, but unknowns is empty.")

    if unknowns and not client_questions:
        failures.append("There are unknowns, but client_questions is empty.")

    if not backend_tasks:
        warnings.append("backend_tasks is empty; this may be too weak for implementation planning.")

    for section, item in collect_items(output):
        if section == "hallucination_checks":
            continue

        label = item.get("task") or item.get("item") or item.get("name") or "<unnamed item>"

        if is_blank(item.get("reason")) and section != "test_cases":
            warnings.append(f"{section}: '{label}' has an empty reason.")

        if item.get("status") == "blocked" and not item.get("depends_on"):
            warnings.append(f"{section}: blocked item '{label}' has empty depends_on.")

    text_dump = json.dumps(output, ensure_ascii=False).lower()

    risky_terms = [
        "critical",
        "non-negotiable",
        "postgresql",
        "mysql",
        "recursive cte",
        "manager_a",
        "companycode=abc",
        "react",
        "vue",
        "next.js",
    ]

    for term in risky_terms:
        if term in text_dump:
            warnings.append(f"Risky or unsupported term found: {term}")

    if "report endpoint" in text_dump:
        warnings.append("Generic 'report endpoint' found; acceptable only if treated as conceptual, not a concrete endpoint.")

    return failures, warnings


def print_results(failures: list[str], warnings: list[str]) -> int:
    if not failures and not warnings:
        print("PASS: Semantic validation found no issues.")
        return 0

    if failures:
        print("FAIL: Semantic validation found blocking issues.")
    else:
        print("PASS WITH WARNINGS: No blocking semantic issues found.")

    print()

    if failures:
        print("Failures:")
        for index, failure in enumerate(failures, start=1):
            print(f"{index}. {failure}")
        print()

    if warnings:
        print("Warnings:")
        for index, warning in enumerate(warnings, start=1):
            print(f"{index}. {warning}")
        print()

    return 1 if failures else 0


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python scripts/semantic_validate_model_output.py <model-output-json-path>")
        return 2

    output_path = Path(sys.argv[1]).resolve()

    try:
        output = load_json(output_path)
        failures, warnings = run_semantic_checks(output)
        return print_results(failures, warnings)
    except Exception as error:
        print(f"ERROR: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
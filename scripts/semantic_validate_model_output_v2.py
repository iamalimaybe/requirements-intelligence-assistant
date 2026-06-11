"""
Run stricter semantic checks on requirements-analysis model output.

Purpose:
- JSON Schema validates structure.
- Semantic validator v1 checks basic content quality.
- Semantic validator v2 checks whether the output is useful for a requirements-analysis workflow.

Usage:
    python scripts/semantic_validate_model_output_v2.py model-outputs/v3-semantic-repaired-schema-fixed-qwen3-4b-output.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_FACT_TERMS = [
    "Production Report",
    "hierarchyAgent",
    "companyCode",
    "startDate",
    "endDate",
    "DATE_ADDED",
    "summed",
]

REQUIRED_UNKNOWN_TERMS = [
    "source tables",
    "summation field",
]

RISKY_UNSUPPORTED_TERMS = [
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
    "production_data",
]


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


def text_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).lower()


def list_contains_term(values: list[Any], term: str) -> bool:
    term_lower = term.lower()
    return any(term_lower in str(value).lower() for value in values)


def section_contains_terms(section: list[dict[str, Any]], terms: list[str]) -> bool:
    dumped = text_dump(section)
    return all(term.lower() in dumped for term in terms)


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


def is_blank(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def run_semantic_checks(output: dict[str, Any]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    facts_used = output.get("facts_used", [])
    unknowns = output.get("unknowns", [])
    client_questions = output.get("client_questions", [])
    backend_tasks = output.get("backend_tasks", [])
    frontend_tasks = output.get("frontend_tasks", [])
    database_considerations = output.get("database_considerations", [])
    test_cases = output.get("test_cases", [])
    hallucination_checks = output.get("hallucination_checks", [])

    if len(facts_used) < 5:
        failures.append("facts_used should contain at least 5 grounded requirement facts.")

    for term in REQUIRED_FACT_TERMS:
        if not list_contains_term(facts_used, term):
            failures.append(f"facts_used does not mention required fact term: {term}")

    for term in REQUIRED_UNKNOWN_TERMS:
        if not list_contains_term(unknowns, term):
            failures.append(f"unknowns does not mention required unknown: {term}")

    if unknowns and len(client_questions) < len(unknowns):
        failures.append("client_questions should cover each major unknown.")

    if not backend_tasks:
        failures.append("backend_tasks is empty.")

    if not section_contains_terms(backend_tasks, ["DATE_ADDED"]):
        failures.append("backend_tasks should include a task for applying DATE_ADDED filtering.")

    if not section_contains_terms(backend_tasks, ["sum"]):
        failures.append("backend_tasks should include a task for summing the selected metric/field.")

    if not frontend_tasks:
        failures.append("frontend_tasks is empty.")

    if not test_cases:
        failures.append("test_cases is empty.")

    if len(test_cases) < 2:
        warnings.append("test_cases has fewer than 2 cases; coverage is weak.")

    if not hallucination_checks:
        failures.append("hallucination_checks is empty.")

    if len(hallucination_checks) < 2:
        warnings.append("hallucination_checks has fewer than 2 checks; risk coverage is weak.")

    blocked_items = [
        (section, item)
        for section, item in collect_items(output)
        if item.get("status") == "blocked"
    ]

    if blocked_items and not unknowns:
        failures.append("There are blocked items, but unknowns is empty.")

    for section, item in collect_items(output):
        if section == "hallucination_checks":
            if is_blank(item.get("check")):
                failures.append("hallucination_checks contains an empty check.")
            if is_blank(item.get("notes")):
                warnings.append("hallucination_checks contains empty notes.")
            continue

        label = item.get("task") or item.get("item") or item.get("name") or "<unnamed item>"

        if is_blank(item.get("reason")) and section != "test_cases":
            failures.append(f"{section}: '{label}' has an empty reason.")

        if item.get("status") == "blocked" and not item.get("depends_on"):
            failures.append(f"{section}: blocked item '{label}' has empty depends_on.")

    dumped = text_dump(output)

    for term in RISKY_UNSUPPORTED_TERMS:
        if term.lower() in dumped:
            warnings.append(f"Risky or unsupported term found: {term}")

    if "report endpoint" in dumped:
        failures.append("Generic 'report endpoint' found; use neutral wording such as backend/report request contract.")

    return failures, warnings


def print_results(failures: list[str], warnings: list[str]) -> int:
    if not failures and not warnings:
        print("PASS: Semantic validation v2 found no issues.")
        return 0

    if failures:
        print("FAIL: Semantic validation v2 found blocking issues.")
    else:
        print("PASS WITH WARNINGS: Semantic validation v2 found no blocking issues.")

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
        print("  python scripts/semantic_validate_model_output_v2.py <model-output-json-path>")
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
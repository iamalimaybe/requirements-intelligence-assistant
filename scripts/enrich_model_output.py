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
    normalized = value.lower()
    normalized = normalized.replace("_", " ")
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace(" and ", " ")
    normalized = "".join(
        character if character.isalnum() or character.isspace() else " "
        for character in normalized
    )

    return " ".join(normalized.split())

def strings_overlap(first: str, second: str) -> bool:
    ignored_terms = {
        "a",
        "an",
        "and",
        "are",
        "for",
        "from",
        "is",
        "of",
        "or",
        "the",
        "to",
        "what",
        "which",
        "with",
    }

    first_terms = {
        term
        for term in normalize_text(first).split()
        if len(term) >= 4 and term not in ignored_terms
    }

    second_terms = {
        term
        for term in normalize_text(second).split()
        if len(term) >= 4 and term not in ignored_terms
    }

    if not first_terms or not second_terms:
        return False

    overlap = first_terms.intersection(second_terms)

    if len(first_terms) <= 3 or len(second_terms) <= 3:
        return len(overlap) >= 2

    return len(overlap) >= 3

def merge_string_lists(existing: list[str], required: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for value in [*required, *existing]:
        if not isinstance(value, str) or not value.strip():
            continue

        cleaned_value = value.strip()
        key = normalize_text(cleaned_value)

        if key in seen:
            continue

        if any(strings_overlap(cleaned_value, existing_value) for existing_value in merged):
            continue

        merged.append(cleaned_value)
        seen.add(key)

    return merged


def merge_exact_string_lists(existing: list[str], required: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for value in [*required, *existing]:
        if not isinstance(value, str) or not value.strip():
            continue

        cleaned_value = value.strip()
        key = normalize_text(cleaned_value)

        if key in seen:
            continue

        merged.append(cleaned_value)
        seen.add(key)

    return merged


def item_key(item: dict[str, Any], key_field: str) -> str:
    value = item.get(key_field)

    if isinstance(value, str):
        return normalize_text(value)

    return ""

def question_covers_unknown(question: str, unknown: str) -> bool:
    question_text = normalize_text(question)
    unknown_text = normalize_text(unknown)

    ignored_terms = {
        "exact",
        "complete",
        "provided",
        "required",
        "records",
        "feedback",
    }

    unknown_terms = [
        term.strip()
        for term in unknown_text.replace("field name", "field").split()
        if len(term.strip()) >= 5 and term.strip() not in ignored_terms
    ]

    if not unknown_terms:
        return False

    matched_terms = [
        term
        for term in unknown_terms
        if term in question_text or f"{term}s" in question_text
    ]

    if len(unknown_terms) <= 2:
        return len(matched_terms) >= 1

    return len(matched_terms) >= 2


def add_questions_for_uncovered_unknowns(
    unknowns: list[str],
    client_questions: list[str],
) -> list[str]:
    questions: list[str] = []
    seen: set[str] = set()

    for question in client_questions:
        if not isinstance(question, str) or not question.strip():
            continue

        key = normalize_text(question)

        if key not in seen:
            questions.append(question.strip())
            seen.add(key)

    for unknown in unknowns:
        if not isinstance(unknown, str) or not unknown.strip():
            continue

        if any(question_covers_unknown(question, unknown) for question in questions):
            continue

        fallback_question = f"Please clarify: {unknown.strip()}"
        key = normalize_text(fallback_question)

        if key not in seen:
            questions.append(fallback_question)
            seen.add(key)

    return questions

def text_terms(value: str) -> set[str]:
    ignored_terms = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "into",
        "using",
        "used",
        "admin",
        "user",
        "users",
        "record",
        "records",
    }

    return {
        term.strip(".,:;()[]{}")
        for term in normalize_text(value).split()
        if len(term.strip(".,:;()[]{}")) >= 5
        and term.strip(".,:;()[]{}") not in ignored_terms
    }


def object_text(item: dict[str, Any]) -> str:
    values: list[str] = []

    for value in item.values():
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            values.extend(str(child) for child in value)

    return normalize_text(" ".join(values))


def objects_overlap(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_terms = text_terms(object_text(first))
    second_terms = text_terms(object_text(second))

    if not first_terms or not second_terms:
        return False

    overlap = first_terms.intersection(second_terms)

    return len(overlap) >= 3


def is_weak_generated_object(item: dict[str, Any]) -> bool:
    status = item.get("status")
    depends_on = item.get("depends_on")

    if isinstance(status, str) and status == "blocked" and depends_on == []:
        return True

    text = object_text(item)

    weak_phrases = [
        "trusted context states",
        "suggested anonymized fields",
        "suggested review status values",
        "feature scope matches requirements",
        "fields are appropriate",
        "status values are valid",
    ]

    return any(phrase in text for phrase in weak_phrases)


def merge_objects(
    existing: list[dict[str, Any]],
    required: list[dict[str, Any]],
    key_field: str,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in required:
        if not isinstance(item, dict):
            continue

        key = item_key(item, key_field)

        if not key:
            continue

        if key not in seen:
            merged.append(item)
            seen.add(key)

    for item in existing:
        if not isinstance(item, dict):
            continue

        key = item_key(item, key_field)

        if not key:
            continue

        if key in seen:
            continue

        if is_weak_generated_object(item):
            continue

        if any(objects_overlap(item, required_item) for required_item in required):
            continue

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
        "facts_used": merge_exact_string_lists(
            normalized_model_output.get("facts_used", []),
            context.get("known_facts", []),
        ),
        "unknowns": merge_string_lists(
            normalized_model_output.get("unknowns", []),
            context.get("required_unknowns", []),
        ),
        "client_questions": add_questions_for_uncovered_unknowns(
            unknowns=merge_string_lists(
                normalized_model_output.get("unknowns", []),
                context.get("required_unknowns", []),
            ),
            client_questions=context.get("client_questions", []),
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
            [],
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
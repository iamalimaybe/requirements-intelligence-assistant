import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


ALLOWED_STATUS_VALUES = {"ready", "blocked", "optional"}
ALLOWED_HALLUCINATION_RESULT_VALUES = {"pass", "fail", "warning", "blocked"}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "their",
    "this",
    "to",
    "use",
    "used",
    "using",
    "with",
}

CATEGORY_DEFINITIONS = {
    "facts_used": {
        "label": "facts used",
        "aliases": [
            "facts",
            "fact",
            "known_facts",
            "required_facts",
            "facts_used",
            "trusted_facts",
            "business_facts",
            "constraints",
        ],
    },
    "unknowns": {
        "label": "unknowns",
        "aliases": [
            "unknowns",
            "unknown",
            "open_items",
            "open_item",
            "missing_information",
            "unresolved_items",
        ],
    },
    "client_questions": {
        "label": "client questions",
        "aliases": [
            "client_questions",
            "questions",
            "open_questions",
            "clarifying_questions",
            "questions_for_client",
        ],
    },
    "backend_tasks": {
        "label": "backend tasks",
        "aliases": [
            "backend_tasks",
            "backend_task",
            "required_backend_tasks",
            "api_tasks",
            "service_tasks",
        ],
    },
    "frontend_tasks": {
        "label": "frontend tasks",
        "aliases": [
            "frontend_tasks",
            "frontend_task",
            "required_frontend_tasks",
            "ui_tasks",
            "client_side_tasks",
        ],
    },
    "database_considerations": {
        "label": "database considerations",
        "aliases": [
            "database_considerations",
            "database_consideration",
            "db_considerations",
            "db_consideration",
            "database_notes",
            "database_tasks",
            "data_considerations",
        ],
    },
    "test_cases": {
        "label": "test cases",
        "aliases": [
            "test_cases",
            "test_case",
            "tests",
            "test_scenarios",
            "validation_tests",
        ],
    },
    "hallucination_checks": {
        "label": "hallucination checks",
        "aliases": [
            "hallucination_checks",
            "hallucination_check",
            "unsupported_assumption_checks",
            "assumption_checks",
            "grounding_checks",
        ],
    },
}


RISKY_DB_TERM_GROUPS = [
    ["postgresql", "postgres"],
    ["sql server", "mssql", "t-sql", "tsql"],
    ["mysql"],
    ["mariadb"],
    ["oracle"],
    ["mongodb", "mongo"],
    ["sqlite"],
    ["dynamodb"],
    ["redis"],
    ["cassandra"],
    ["snowflake"],
    ["bigquery"],
]

RISKY_FRONTEND_TERM_GROUPS = [
    ["react", "reactjs"],
    ["angular"],
    ["vue", "vue.js"],
    ["svelte"],
    ["next.js", "nextjs"],
    ["nuxt", "nuxt.js"],
    ["vite"],
    ["tailwind", "tailwindcss"],
    ["bootstrap"],
    ["jquery"],
]

COMMON_UPPERCASE_TERMS = {
    "API",
    "CSV",
    "DB",
    "HTTP",
    "JSON",
    "REST",
    "SQL",
    "UI",
    "URL",
}


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError(f"File not found: {path}")
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path}: {error}")


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def normalize_text(value: str) -> str:
    lowered = value.lower()
    lowered = lowered.replace("_", " ")
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def tokenize(value: str) -> Set[str]:
    normalized = normalize_text(value)
    tokens = set()

    for token in normalized.split():
        if len(token) < 3:
            continue
        if token in STOPWORDS:
            continue
        tokens.add(token)

    return tokens


def primitive_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    return ""


def item_to_text(item: Any) -> str:
    parts = []

    def walk(value: Any) -> None:
        primitive = primitive_to_text(value)
        if primitive:
            parts.append(primitive)
            return

        if isinstance(value, list):
            for child in value:
                walk(child)
            return

        if isinstance(value, dict):
            for key, child in value.items():
                parts.append(str(key))
                walk(child)

    walk(item)
    return " ".join(parts)


def full_text(value: Any) -> str:
    return item_to_text(value)


def add_items_from_value(value: Any, items: List[Any]) -> None:
    if isinstance(value, list):
        for child in value:
            items.append(child)
        return

    if isinstance(value, dict):
        has_item_shape = any(
            normalize_key(key) in {"id", "title", "name", "description", "task", "question", "result", "status"}
            for key in value.keys()
        )

        if has_item_shape:
            items.append(value)
            return

        for child in value.values():
            if isinstance(child, list):
                for entry in child:
                    items.append(entry)
        return

    if primitive_to_text(value):
        items.append(value)


def key_matches_category(key: str, path: List[str], category_name: str, aliases: Iterable[str]) -> bool:
    normalized_key = normalize_key(key)
    normalized_path = [normalize_key(part) for part in path]
    normalized_aliases = {normalize_key(alias) for alias in aliases}

    if normalized_key in normalized_aliases:
        return True

    if any(normalized_key.endswith(alias) for alias in normalized_aliases):
        return True

    path_text = " ".join(normalized_path)

    if category_name == "backend_tasks":
        return "backend" in path_text and "task" in normalized_key

    if category_name == "frontend_tasks":
        return "frontend" in path_text and "task" in normalized_key

    if category_name == "database_considerations":
        has_database_hint = "database" in path_text or "db" in normalized_path
        has_detail_hint = any(
            hint in normalized_key
            for hint in ["consideration", "task", "note", "join", "table", "field", "data"]
        )
        return has_database_hint and has_detail_hint

    if category_name == "test_cases":
        has_test_hint = "test" in normalized_key or "test" in path_text
        has_case_hint = any(hint in normalized_key for hint in ["case", "scenario", "validation", "expected"])
        return has_test_hint and has_case_hint

    if category_name == "client_questions":
        return "client" in path_text and "question" in normalized_key

    if category_name == "hallucination_checks":
        return "hallucination" in normalized_key or "groundingcheck" in normalized_key

    return False


def collect_category_items(data: Any, category_name: str) -> List[Any]:
    definition = CATEGORY_DEFINITIONS[category_name]
    aliases = definition["aliases"]
    collected = []
    seen = set()

    def walk(value: Any, path: List[str]) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                next_path = path + [key]

                if key_matches_category(key, next_path, category_name, aliases):
                    before_count = len(collected)
                    add_items_from_value(child, collected)

                    for item in collected[before_count:]:
                        fingerprint = normalize_text(item_to_text(item))
                        if fingerprint in seen:
                            continue
                        seen.add(fingerprint)

                walk(child, next_path)

        elif isinstance(value, list):
            for child in value:
                walk(child, path)

    walk(data, [])
    unique_items = []
    unique_seen = set()

    for item in collected:
        fingerprint = normalize_text(item_to_text(item))
        if not fingerprint:
            continue
        if fingerprint in unique_seen:
            continue
        unique_seen.add(fingerprint)
        unique_items.append(item)

    return unique_items


def coverage_match(required_text: str, target_text: str) -> bool:
    normalized_required = normalize_text(required_text)
    normalized_target = normalize_text(target_text)

    if not normalized_required:
        return True

    if len(normalized_required) >= 12 and normalized_required in normalized_target:
        return True

    required_tokens = tokenize(required_text)
    target_tokens = tokenize(target_text)

    if not required_tokens:
        return True

    overlap = required_tokens.intersection(target_tokens)

    if len(required_tokens) <= 2:
        return len(overlap) == len(required_tokens)

    if len(required_tokens) <= 5:
        return len(overlap) >= max(2, round(len(required_tokens) * 0.60))

    return len(overlap) >= max(3, round(len(required_tokens) * 0.55))


def validate_category_coverage(output_data: Any, context_data: Any) -> List[str]:
    errors = []

    for category_name, definition in CATEGORY_DEFINITIONS.items():
        context_items = collect_category_items(context_data, category_name)

        if not context_items:
            continue

        output_items = collect_category_items(output_data, category_name)

        if not output_items:
            errors.append(f"Missing output section for {definition['label']}.")
            continue

        output_text = item_to_text(output_items)

        for item in context_items:
            required_text = item_to_text(item)

            if coverage_match(required_text, output_text):
                continue

            preview = required_text.strip().replace("\n", " ")
            preview = re.sub(r"\s+", " ", preview)

            if len(preview) > 160:
                preview = preview[:157] + "..."

            errors.append(f"Missing required {definition['label']} item from context: {preview}")

    return errors


def iter_dicts(value: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(value, dict):
        yield value

        for child in value.values():
            yield from iter_dicts(child)

    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def get_case_insensitive_value(data: Dict[str, Any], key_name: str) -> Any:
    normalized_target = normalize_key(key_name)

    for key, value in data.items():
        if normalize_key(key) == normalized_target:
            return value

    return None


def has_non_empty_key(data: Dict[str, Any], key_name: str) -> bool:
    value = get_case_insensitive_value(data, key_name)

    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, list):
        return len(value) > 0

    if isinstance(value, dict):
        return len(value) > 0

    return True


def validate_status_values(output_data: Any) -> List[str]:
    errors = []

    for item in iter_dicts(output_data):
        for key, value in item.items():
            if normalize_key(key) != "status":
                continue

            if not isinstance(value, str):
                errors.append("Status value must be a string.")
                continue

            normalized_value = value.strip().lower()

            if normalized_value not in ALLOWED_STATUS_VALUES:
                errors.append(
                    f"Invalid status value '{value}'. "
                    f"Allowed values: {sorted(ALLOWED_STATUS_VALUES)}."
                )

            if normalized_value == "blocked" and not has_non_empty_key(item, "depends_on"):
                item_text = item_to_text(item)
                preview = re.sub(r"\s+", " ", item_text).strip()

                if len(preview) > 120:
                    preview = preview[:117] + "..."

                errors.append(f"Blocked item is missing depends_on: {preview}")

    return errors


def validate_hallucination_result_values(output_data: Any) -> List[str]:
    errors = []
    hallucination_items = collect_category_items(output_data, "hallucination_checks")

    for item in hallucination_items:
        if not isinstance(item, dict):
            continue

        result = get_case_insensitive_value(item, "result")

        if result is None:
            continue

        if not isinstance(result, str):
            errors.append("Hallucination check result must be a string.")
            continue

        normalized_result = result.strip().lower()

        if normalized_result not in ALLOWED_HALLUCINATION_RESULT_VALUES:
            errors.append(
                f"Invalid hallucination check result '{result}'. "
                f"Allowed values: {sorted(ALLOWED_HALLUCINATION_RESULT_VALUES)}."
            )

    return errors


def contains_term(text: str, term: str) -> bool:
    escaped = re.escape(term.lower())
    pattern = r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def extract_sentence_window(text: str, start_index: int, end_index: int) -> Tuple[str, int, int]:
    sentence_boundaries = ".!?\n;"
    left_boundary = -1

    for boundary in sentence_boundaries:
        position = text.rfind(boundary, 0, start_index)

        if position > left_boundary:
            left_boundary = position

    left = 0 if left_boundary == -1 else left_boundary + 1
    right_candidates = []

    for boundary in sentence_boundaries:
        position = text.find(boundary, end_index)

        if position != -1:
            right_candidates.append(position)

    right = min(right_candidates) if right_candidates else len(text)

    return text[left:right], start_index - left, end_index - left


def is_guarded_mention(text: str, start_index: int, end_index: Optional[int] = None) -> bool:
    if end_index is None:
        end_index = start_index

        while end_index < len(text):
            current = text[end_index]

            if current.isspace() or current in ",:()[]{}<>\"'":
                break

            end_index += 1

    sentence, relative_start, relative_end = extract_sentence_window(
        text,
        start_index,
        end_index,
    )

    sentence = sentence.lower()
    term_text = sentence[relative_start:relative_end].strip()

    if not term_text:
        return False

    term_pattern = re.escape(term_text)

    direct_guard_patterns = [
        rf"\b(?:do not|don't|should not|must not|cannot|can't|never|not)\s+"
        rf"(?:assume|use|implement|select|choose|invent|add|introduce)\b.{{0,80}}{term_pattern}",
        rf"{term_pattern}.{{0,80}}\b(?:should not|must not|cannot|can't|not)\s+"
        rf"(?:be\s+)?(?:assumed|used|implemented|selected|chosen|introduced|added)\b",
        rf"{term_pattern}.{{0,80}}\b"
        rf"(?:is|are|was|were)?\s*"
        rf"(?:not supported|unsupported|not confirmed|unconfirmed|not in context|"
        rf"not present in context|not provided by context|invented|hallucinated|fake)\b",
        rf"\b(?:unsupported|unconfirmed|invented|hallucinated|fake)\b.{{0,80}}{term_pattern}",
        rf"{term_pattern}.{{0,80}}\b(?:unless|until)\s+(?:the\s+)?context\b",
        rf"\bwithout\s+(?:trusted\s+)?context\b.{{0,80}}{term_pattern}",
    ]

    for pattern in direct_guard_patterns:
        if re.search(pattern, sentence):
            return True

    assertive_usage_patterns = [
        rf"\b(?:use|uses|using|build|builds|built|implement|implements|implemented|"
        rf"configure|configures|configured|migrate|migrates|migrated|store|stores|stored|"
        rf"deploy|deploys|deployed|select|selects|selected|choose|chooses|chosen|"
        rf"connect|connects|connected|join|joins|joined|query|queries|queried)\b.{{0,60}}{term_pattern}",
        rf"{term_pattern}.{{0,60}}\b(?:will|should|must|can|could|is|are)\s+"
        rf"(?:be\s+)?(?:used|implemented|configured|selected|chosen|deployed|connected|queried)\b",
    ]

    for pattern in assertive_usage_patterns:
        if re.search(pattern, sentence):
            return False

    broad_guard_markers = [
        "unsupported",
        "unconfirmed",
        "not confirmed",
        "not in context",
        "not present in context",
        "not provided by context",
        "without context",
        "invented",
        "hallucinated",
        "fake",
    ]

    return any(marker in sentence for marker in broad_guard_markers)


def find_term_occurrences(text: str, term: str) -> Iterable[Tuple[int, int]]:
    escaped = re.escape(term.lower())
    pattern = r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])"

    for match in re.finditer(pattern, text.lower()):
        yield match.start(), match.end()


def validate_unsupported_term_groups(
    output_text: str,
    context_text: str,
    term_groups: List[List[str]],
    label: str,
) -> List[str]:
    errors = []

    for group in term_groups:
        supported_by_context = any(contains_term(context_text, term) for term in group)

        if supported_by_context:
            continue

        for term in group:
            for start, _ in find_term_occurrences(output_text, term):
                if is_guarded_mention(output_text, start, end):
                    continue

                errors.append(
                    f"Unsupported {label} term '{term}' appears in output but not in context."
                )
                break

    return errors


def validate_implementation_estimates(output_text: str, context_text: str) -> List[str]:
    errors = []
    patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:hour|hours|day|days|week|weeks|sprint|sprints)\b",
        r"\b\d+(?:\.\d+)?\s*(?:story\s+point|story\s+points|points)\b",
        r"\b(?:eta|estimate|estimated|effort|timeline|duration)\s*[:=]\s*[^,\n.]+",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, output_text, flags=re.IGNORECASE):
            phrase = match.group(0)

            if contains_term(context_text, phrase):
                continue

            if is_guarded_mention(output_text, match.start(), match.end()):
                continue

            errors.append(
                f"Unsupported implementation estimate appears in output but not in context: {phrase}"
            )

    return errors


def validate_fake_sample_values(output_text: str, context_text: str) -> List[str]:
    errors = []
    sample_pattern = r"(?:sample|example|mock|dummy|test value|e\.g\.)[^.\n]{0,140}"
    value_pattern = r"\b[A-Z]{2,}[A-Z0-9_]{1,}\b|\b\d{4}-\d{2}-\d{2}\b|\b\d+\.\d+\b"

    for sample_match in re.finditer(sample_pattern, output_text, flags=re.IGNORECASE):
        window = sample_match.group(0)

        for value_match in re.finditer(value_pattern, window):
            value = value_match.group(0)

            if value in COMMON_UPPERCASE_TERMS:
                continue

            if value.lower() in context_text.lower():
                continue

            errors.append(
                f"Possible invented sample value '{value}' appears in output but not in context."
            )

    return errors


def validate_risky_unsupported_hallucinations(output_data: Any, context_data: Any) -> List[str]:
    output_text = full_text(output_data)
    context_text = full_text(context_data)

    errors = []
    errors.extend(
        validate_unsupported_term_groups(
            output_text=output_text,
            context_text=context_text,
            term_groups=RISKY_DB_TERM_GROUPS,
            label="database engine",
        )
    )
    errors.extend(
        validate_unsupported_term_groups(
            output_text=output_text,
            context_text=context_text,
            term_groups=RISKY_FRONTEND_TERM_GROUPS,
            label="frontend framework",
        )
    )
    errors.extend(validate_implementation_estimates(output_text, context_text))
    errors.extend(validate_fake_sample_values(output_text, context_text))

    return errors


def validate(output_data: Any, context_data: Any) -> List[str]:
    errors = []
    errors.extend(validate_category_coverage(output_data, context_data))
    errors.extend(validate_status_values(output_data))
    errors.extend(validate_hallucination_result_values(output_data))
    errors.extend(validate_risky_unsupported_hallucinations(output_data, context_data))

    return errors


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/semantic_validate_model_output_v3.py "
            "<model_output_json> <context_json>",
            file=sys.stderr,
        )
        return 2

    output_path = Path(sys.argv[1])
    context_path = Path(sys.argv[2])

    try:
        output_data = load_json(output_path)
        context_data = load_json(context_path)
        errors = validate(output_data, context_data)
    except ValueError as error:
        print(f"SEMANTIC VALIDATION V3 RESULT: FAIL")
        print(f"- {error}")
        return 1

    if errors:
        print("SEMANTIC VALIDATION V3 RESULT: FAIL")

        for index, error in enumerate(errors, start=1):
            print(f"{index}. {error}")

        return 1

    print("SEMANTIC VALIDATION V3 RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
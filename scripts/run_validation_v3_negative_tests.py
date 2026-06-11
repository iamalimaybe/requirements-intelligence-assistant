import copy
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

CATEGORY_ALIASES = {
    "facts_used": [
        "facts",
        "fact",
        "known_facts",
        "required_facts",
        "facts_used",
        "trusted_facts",
        "business_facts",
        "constraints",
    ],
    "backend_tasks": [
        "backend_tasks",
        "backend_task",
        "required_backend_tasks",
        "api_tasks",
        "service_tasks",
    ],
    "frontend_tasks": [
        "frontend_tasks",
        "frontend_task",
        "required_frontend_tasks",
        "ui_tasks",
        "client_side_tasks",
    ],
    "database_considerations": [
        "database_considerations",
        "database_consideration",
        "db_considerations",
        "db_consideration",
        "database_notes",
        "database_tasks",
        "data_considerations",
    ],
    "hallucination_checks": [
        "hallucination_checks",
        "hallucination_check",
        "unsupported_assumption_checks",
        "assumption_checks",
        "grounding_checks",
    ],
}

DB_TERMS = [
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Oracle",
    "SQLite",
]

FRONTEND_TERMS = [
    "React",
    "Angular",
    "Vue",
    "Next.js",
    "Svelte",
]

MutationResult = Tuple[bool, str]
Mutator = Callable[[Any, Any], MutationResult]


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


def item_to_text(value: Any) -> str:
    parts = []

    def walk(current: Any) -> None:
        if current is None:
            return

        if isinstance(current, (str, int, float, bool)):
            parts.append(str(current))
            return

        if isinstance(current, list):
            for child in current:
                walk(child)
            return

        if isinstance(current, dict):
            for key, child in current.items():
                parts.append(str(key))
                walk(child)

    walk(value)
    return " ".join(parts)


def contains_term(data: Any, term: str) -> bool:
    return term.lower() in item_to_text(data).lower()


def choose_unsupported_term(context_data: Any, terms: List[str]) -> Optional[str]:
    for term in terms:
        if not contains_term(context_data, term):
            return term

    return None


def find_category_lists(data: Any, category_name: str) -> List[List[Any]]:
    aliases = {normalize_key(alias) for alias in CATEGORY_ALIASES[category_name]}
    matches = []

    def add_nested_lists(value: Any) -> None:
        if isinstance(value, list):
            matches.append(value)
            return

        if isinstance(value, dict):
            for child in value.values():
                if isinstance(child, list):
                    matches.append(child)

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if normalize_key(key) in aliases:
                    add_nested_lists(child)

                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    return matches


def iter_dicts(value: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(value, dict):
        yield value

        for child in value.values():
            yield from iter_dicts(child)

    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def append_text_to_value(parent: Any, key: Any, text: str) -> bool:
    value = parent[key]

    if isinstance(value, str):
        parent[key] = value.rstrip() + " " + text
        return True

    if isinstance(value, dict):
        preferred_keys = [
            "description",
            "task",
            "title",
            "name",
            "question",
            "check",
            "reason",
            "notes",
        ]

        for preferred_key in preferred_keys:
            for existing_key, child in value.items():
                if normalize_key(existing_key) == normalize_key(preferred_key) and isinstance(child, str):
                    value[existing_key] = child.rstrip() + " " + text
                    return True

        for existing_key, child in value.items():
            if isinstance(child, str):
                value[existing_key] = child.rstrip() + " " + text
                return True

        for existing_key, child in value.items():
            if isinstance(child, (dict, list)):
                if append_text_to_value(value, existing_key, text):
                    return True

    if isinstance(value, list):
        for index in range(len(value)):
            if append_text_to_value(value, index, text):
                return True

    return False


def append_text_to_category(data: Any, category_name: str, text: str) -> bool:
    category_lists = find_category_lists(data, category_name)

    for category_list in category_lists:
        for index in range(len(category_list)):
            if append_text_to_value(category_list, index, text):
                return True

    return False


def find_first_status_item(data: Any) -> Optional[Tuple[Dict[str, Any], str]]:
    for item in iter_dicts(data):
        for key in item.keys():
            if normalize_key(key) == "status":
                return item, key

    return None


def find_first_hallucination_result_item(data: Any) -> Optional[Tuple[Dict[str, Any], str]]:
    hallucination_lists = find_category_lists(data, "hallucination_checks")

    for hallucination_list in hallucination_lists:
        for item in iter_dicts(hallucination_list):
            for key in item.keys():
                if normalize_key(key) == "result":
                    return item, key

    return None


def remove_depends_on_fields(item: Dict[str, Any]) -> None:
    for key in list(item.keys()):
        if normalize_key(key) == "dependson":
            del item[key]


def mutate_missing_required_fact(output_data: Any, context_data: Any) -> MutationResult:
    fact_lists = find_category_lists(output_data, "facts_used")

    for fact_list in fact_lists:
        if fact_list:
            removed = fact_list.pop(0)
            preview = item_to_text(removed).strip()

            if len(preview) > 120:
                preview = preview[:117] + "..."

            return True, f"Removed one fact from facts_used: {preview}"

    return False, "Could not find a facts_used list with at least one item."


def mutate_invalid_status(output_data: Any, context_data: Any) -> MutationResult:
    status_item = find_first_status_item(output_data)

    if status_item is None:
        return False, "Could not find any item with a status field."

    item, key = status_item
    item[key] = "in_progress"

    return True, "Changed one status value to invalid value: in_progress"


def mutate_blocked_without_depends_on(output_data: Any, context_data: Any) -> MutationResult:
    status_item = find_first_status_item(output_data)

    if status_item is None:
        return False, "Could not find any item with a status field."

    item, key = status_item
    item[key] = "blocked"
    remove_depends_on_fields(item)

    return True, "Changed one item to blocked and removed depends_on."


def mutate_invalid_hallucination_result(output_data: Any, context_data: Any) -> MutationResult:
    result_item = find_first_hallucination_result_item(output_data)

    if result_item is None:
        return False, "Could not find any hallucination check item with a result field."

    item, key = result_item
    item[key] = "unknown"

    return True, "Changed one hallucination check result to invalid value: unknown"


def mutate_invented_db_engine(output_data: Any, context_data: Any) -> MutationResult:
    term = choose_unsupported_term(context_data, DB_TERMS)

    if term is None:
        return False, "Could not find a database engine term that is absent from the context."

    added = append_text_to_category(
        output_data,
        "database_considerations",
        f"Use {term} for this implementation.",
    )

    if not added:
        return False, "Could not find a database_considerations item to mutate."

    return True, f"Added unsupported database engine term: {term}"


def mutate_invented_frontend_framework(output_data: Any, context_data: Any) -> MutationResult:
    term = choose_unsupported_term(context_data, FRONTEND_TERMS)

    if term is None:
        return False, "Could not find a frontend framework term that is absent from the context."

    added = append_text_to_category(
        output_data,
        "frontend_tasks",
        f"Build this screen using {term}.",
    )

    if not added:
        return False, "Could not find a frontend_tasks item to mutate."

    return True, f"Added unsupported frontend framework term: {term}"


def mutate_implementation_estimate(output_data: Any, context_data: Any) -> MutationResult:
    added = append_text_to_category(
        output_data,
        "backend_tasks",
        "Estimated duration: 3 days.",
    )

    if not added:
        return False, "Could not find a backend_tasks item to mutate."

    return True, "Added unsupported implementation estimate: 3 days."


def mutate_fake_sample_value(output_data: Any, context_data: Any) -> MutationResult:
    fake_value = "FAKE_AGENT_999"

    if contains_term(context_data, fake_value):
        return False, f"Fake sample value unexpectedly exists in context: {fake_value}"

    added = append_text_to_category(
        output_data,
        "backend_tasks",
        f"Example sample value: {fake_value}.",
    )

    if not added:
        return False, "Could not find a backend_tasks item to mutate."

    return True, f"Added unsupported sample value: {fake_value}"


def run_pipeline(script_dir: Path, output_path: Path, context_path: Path) -> Tuple[int, str, str]:
    command = [
        sys.executable,
        str(script_dir / "validate_pipeline_v3.py"),
        str(output_path),
        str(context_path),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    return completed.returncode, completed.stdout, completed.stderr


def main() -> int:
    if len(sys.argv) not in {3, 4}:
        print(
            "Usage: python scripts/run_validation_v3_negative_tests.py "
            "<valid_model_output_json> <context_json> [negative_output_dir]",
            file=sys.stderr,
        )
        return 2

    valid_output_path = Path(sys.argv[1])
    context_path = Path(sys.argv[2])
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    if len(sys.argv) == 4:
        negative_output_dir = Path(sys.argv[3])
    else:
        negative_output_dir = project_root / "scratch" / "v3-negative-tests"

    try:
        valid_output_data = load_json(valid_output_path)
        context_data = load_json(context_path)
    except Exception as error:
        print("NEGATIVE TEST RESULT: FAIL")
        print(f"- Could not load input JSON: {error}")
        return 1

    test_cases: List[Tuple[str, Mutator]] = [
        ("missing-required-fact", mutate_missing_required_fact),
        ("invalid-status", mutate_invalid_status),
        ("blocked-without-depends-on", mutate_blocked_without_depends_on),
        ("invalid-hallucination-result", mutate_invalid_hallucination_result),
        ("invented-db-engine", mutate_invented_db_engine),
        ("invented-frontend-framework", mutate_invented_frontend_framework),
        ("unsupported-implementation-estimate", mutate_implementation_estimate),
        ("fake-sample-value", mutate_fake_sample_value),
    ]

    failures = []

    print(f"Writing negative fixtures to: {negative_output_dir}")

    for test_name, mutator in test_cases:
        mutated_output_data = copy.deepcopy(valid_output_data)
        mutation_created, mutation_message = mutator(mutated_output_data, context_data)

        if not mutation_created:
            failures.append(f"{test_name}: mutation could not be created. {mutation_message}")
            print(f"[FAIL] {test_name}: mutation could not be created.")
            continue

        mutated_output_path = negative_output_dir / f"{test_name}.json"
        write_json(mutated_output_path, mutated_output_data)

        return_code, stdout, stderr = run_pipeline(script_dir, mutated_output_path, context_path)

        if return_code == 0:
            failures.append(
                f"{test_name}: bad output was not rejected. Mutation: {mutation_message}"
            )
            print(f"[FAIL] {test_name}: bad output was not rejected.")
            print(stdout.strip())

            if stderr.strip():
                print(stderr.strip(), file=sys.stderr)

            continue

        print(f"[PASS] {test_name}: rejected as expected.")

    if failures:
        print("NEGATIVE TEST RESULT: FAIL")

        for index, failure in enumerate(failures, start=1):
            print(f"{index}. {failure}")

        return 1

    print("NEGATIVE TEST RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
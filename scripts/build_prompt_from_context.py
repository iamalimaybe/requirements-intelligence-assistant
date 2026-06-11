"""
Build a requirements-analysis prompt from trusted context JSON.

Purpose:
- Keep the prompt generic.
- Keep requirement-specific facts in context JSON.
- Generate a prompt file that can be passed to the Ollama workflow.

Usage:
    python scripts/build_prompt_from_context.py ^
      --context contexts/production-report-context.json ^
      --output scratch/generated-prompt.txt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Context file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Context JSON must be a top-level object.")

    return data


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def as_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []

    if not isinstance(value, list):
        raise ValueError(f"Context field '{field_name}' must be a list.")

    items: list[str] = []

    for item in value:
        if isinstance(item, str) and item.strip():
            items.append(item.strip())

    return items


def bullet_list(items: list[str]) -> str:
    if not items:
        return "- None provided."

    return "\n".join(f"- {item}" for item in items)


def build_prompt(context: dict[str, Any]) -> str:
    title = str(context.get("title", "Untitled Requirement")).strip()

    known_facts = as_string_list(context.get("known_facts"), "known_facts")
    required_unknowns = as_string_list(
        context.get("required_unknowns"),
        "required_unknowns",
    )

    return f"""You are a software requirements analyst.

Return valid JSON only.
Do not include markdown.
Do not include explanations outside JSON.
Do not invent table names.
Do not invent endpoint names.
Do not invent database engine.
Do not invent frontend framework.
Do not invent sample values.
Do not invent implementation estimates.
Do not add hierarchy traversal unless the trusted context explicitly requires it.

Analyze only the trusted context below.

Requirement:
{title}

Trusted facts:
{bullet_list(known_facts)}

Known unknowns:
{bullet_list(required_unknowns)}

Return JSON using this exact structure:
{{
  "facts_used": [],
  "unknowns": [],
  "client_questions": [],
  "backend_tasks": [
    {{
      "task": "",
      "status": "",
      "reason": "",
      "depends_on": []
    }}
  ],
  "frontend_tasks": [
    {{
      "task": "",
      "status": "",
      "reason": "",
      "depends_on": []
    }}
  ],
  "database_considerations": [
    {{
      "item": "",
      "status": "",
      "reason": "",
      "depends_on": []
    }}
  ],
  "test_cases": [
    {{
      "name": "",
      "status": "",
      "given": "",
      "expected": "",
      "depends_on": []
    }}
  ],
  "hallucination_checks": [
    {{
      "check": "",
      "result": "",
      "notes": ""
    }}
  ]
}}

Allowed status values:
- ready
- blocked
- optional

Allowed hallucination check result values:
- pass
- fail
- warning
- blocked
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a generic requirements-analysis prompt from trusted context JSON."
    )

    parser.add_argument(
        "--context",
        required=True,
        help="Path to trusted context JSON file.",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path where generated prompt text should be written.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    context_path = Path(args.context).resolve()
    output_path = Path(args.output).resolve()

    try:
        context = read_json(context_path)
        prompt = build_prompt(context)
        write_text(output_path, prompt)

        print(f"Generated prompt written to: {output_path}")
        return 0
    except Exception as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
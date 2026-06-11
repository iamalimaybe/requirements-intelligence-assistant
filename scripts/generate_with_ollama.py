"""
Generate requirements-analysis JSON using a local Ollama model.

Purpose:
- Call Ollama directly instead of manually pasting prompts into the UI.
- Save the model response as JSON for downstream workflow steps.
- Keep generation separate from normalization, enrichment, and validation.
- Repair malformed model JSON once when the first generation attempt fails.

Usage:
    python scripts/generate_with_ollama.py ^
      --model qwen3:4b ^
      --prompt prompts/requirements-analysis-generation-v1.txt ^
      --output model-outputs/ollama-generated-qwen3-4b-output.json
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"

class ModelJsonParseError(ValueError):
    def __init__(self, message: str, response_text: str) -> None:
        super().__init__(message)
        self.response_text = response_text

def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def call_ollama(
    ollama_url: str,
    model: str,
    prompt: str,
    temperature: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "format": "json",
        "options": {
            "temperature": temperature
        }
    }

    request = urllib.request.Request(
        ollama_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.URLError as error:
        raise ConnectionError(
            "Could not connect to Ollama. Make sure Ollama is running."
        ) from error

    try:
        return json.loads(response_body)
    except json.JSONDecodeError as error:
        raise ValueError(f"Ollama returned invalid JSON response: {response_body}") from error


def get_response_text(ollama_response: dict[str, Any]) -> str:
    response_text = ollama_response.get("response")

    if not isinstance(response_text, str) or not response_text.strip():
        debug_response = json.dumps(ollama_response, indent=2, ensure_ascii=False)
        raise ValueError(
            "Ollama response did not contain a non-empty 'response' field.\n"
            f"Raw Ollama response:\n{debug_response}"
        )

    return response_text


def parse_model_json(ollama_response: dict[str, Any]) -> dict[str, Any]:
    response_text = get_response_text(ollama_response)

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise ModelJsonParseError(
            "Model response was not valid JSON.\n"
            f"Raw model response:\n{response_text}",
            response_text=response_text,
        ) from error

    if not isinstance(parsed, dict):
        raise ModelJsonParseError(
            "Model response JSON must be a top-level object.",
            response_text=response_text,
        )

    return parsed


def failed_response_path(output_path: Path, label: str) -> Path:
    return output_path.with_name(f"{output_path.stem}.{label}.txt")


def build_json_repair_prompt(original_prompt: str, invalid_response: str) -> str:
    return f"""
You are repairing malformed JSON from a local LLM.

Return valid JSON only.
Do not include markdown.
Do not include explanations outside JSON.
Do not invent table names.
Do not invent endpoint names.
Do not invent database engine.
Do not invent frontend framework.
Do not invent sample values.
Do not invent implementation estimates.

The original task required this exact JSON structure:
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

Original prompt:
{original_prompt}

Malformed model response:
{invalid_response}

Repair the malformed response into valid JSON that follows the required structure.
Preserve any usable facts and unknowns from the malformed response.
Complete missing sections only from the trusted context in the original prompt.
Return JSON only.
""".strip()


def generate_once(
    ollama_url: str,
    model: str,
    prompt: str,
    temperature: float,
) -> tuple[dict[str, Any], str]:
    ollama_response = call_ollama(
        ollama_url=ollama_url,
        model=model,
        prompt=prompt,
        temperature=temperature,
    )

    response_text = get_response_text(ollama_response)
    parsed_json = parse_model_json(ollama_response)

    return parsed_json, response_text


def generate_with_repair(
    ollama_url: str,
    model: str,
    prompt: str,
    temperature: float,
    output_path: Path,
    max_repair_attempts: int,
) -> dict[str, Any]:
    print("Generation attempt 1...")

    try:
        model_json, _ = generate_once(
            ollama_url=ollama_url,
            model=model,
            prompt=prompt,
            temperature=temperature,
        )
        return model_json

    except ModelJsonParseError as first_error:
        first_response_text = first_error.response_text

        failed_path = failed_response_path(output_path, "failed-generation")
        write_text(failed_path, first_response_text)
        print(f"Invalid model JSON saved to: {failed_path}")

        if max_repair_attempts < 1:
            raise first_error

        repair_prompt = build_json_repair_prompt(
            original_prompt=prompt,
            invalid_response=first_response_text,
        )

        for repair_attempt in range(1, max_repair_attempts + 1):
            print(f"Repair attempt {repair_attempt} of {max_repair_attempts}...")

            try:
                repaired_json, _ = generate_once(
                    ollama_url=ollama_url,
                    model=model,
                    prompt=repair_prompt,
                    temperature=temperature,
                )
                return repaired_json

            except ModelJsonParseError as repair_error:
                repair_failed_path = failed_response_path(
                    output_path,
                    f"failed-repair-{repair_attempt}",
                )
                write_text(repair_failed_path, repair_error.response_text)
                print(f"Invalid repair JSON saved to: {repair_failed_path}")

                if repair_attempt == max_repair_attempts:
                    raise repair_error

        raise first_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate requirements-analysis JSON through local Ollama."
    )

    parser.add_argument(
        "--model",
        default="qwen3:4b",
        help="Ollama model name.",
    )

    parser.add_argument(
        "--prompt",
        required=True,
        help="Path to prompt text file.",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path where parsed model JSON should be saved.",
    )

    parser.add_argument(
        "--ollama-url",
        default=DEFAULT_OLLAMA_URL,
        help="Ollama generate API URL.",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Generation temperature. Lower values improve repeatability.",
    )

    parser.add_argument(
        "--max-repair-attempts",
        type=int,
        default=1,
        help="Maximum repair attempts after malformed model JSON.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    prompt_path = Path(args.prompt).resolve()
    output_path = Path(args.output).resolve()

    if args.max_repair_attempts < 0:
        print("ERROR: --max-repair-attempts cannot be negative.")
        return 2

    try:
        prompt = read_text(prompt_path)
        model_json = generate_with_repair(
            ollama_url=args.ollama_url,
            model=args.model,
            prompt=prompt,
            temperature=args.temperature,
            output_path=output_path,
            max_repair_attempts=args.max_repair_attempts,
        )
        write_json(output_path, model_json)

        print(f"Generated output written to: {output_path}")
        return 0
    except Exception as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
"""
Generate requirements-analysis JSON using a local Ollama model.

Purpose:
- Call Ollama directly instead of manually pasting prompts into the UI.
- Save the model response as JSON for downstream workflow steps.
- Keep generation separate from normalization, enrichment, and validation.

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


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


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


def parse_model_json(ollama_response: dict[str, Any]) -> dict[str, Any]:
    response_text = ollama_response.get("response")

    if not isinstance(response_text, str) or not response_text.strip():
        debug_response = json.dumps(ollama_response, indent=2, ensure_ascii=False)
        raise ValueError(
            "Ollama response did not contain a non-empty 'response' field.\n"
            f"Raw Ollama response:\n{debug_response}"
        )

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Model response was not valid JSON.\n"
            f"Raw model response:\n{response_text}"
        ) from error

    if not isinstance(parsed, dict):
        raise ValueError("Model response JSON must be a top-level object.")

    return parsed


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

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    prompt_path = Path(args.prompt).resolve()
    output_path = Path(args.output).resolve()

    try:
        prompt = read_text(prompt_path)
        ollama_response = call_ollama(
            ollama_url=args.ollama_url,
            model=args.model,
            prompt=prompt,
            temperature=args.temperature,
        )
        model_json = parse_model_json(ollama_response)
        write_json(output_path, model_json)

        print(f"Generated output written to: {output_path}")
        return 0
    except Exception as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
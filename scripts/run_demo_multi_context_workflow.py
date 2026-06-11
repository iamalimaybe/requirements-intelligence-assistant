import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OLLAMA_WORKFLOW = PROJECT_ROOT / "scripts" / "run_ollama_requirements_workflow.py"
MULTI_CONTEXT_REGRESSION = PROJECT_ROOT / "scripts" / "run_multi_context_regression_tests.py"

DEFAULT_CASES = [
    {
        "name": "production-report",
        "context": PROJECT_ROOT / "contexts" / "production-report-context.json",
    },
    {
        "name": "review-moderation",
        "context": PROJECT_ROOT / "contexts" / "review-moderation-context.json",
    },
]


def run_step(name: str, command: List[str]) -> int:
    print()
    print(f"STEP: {name}")
    print("-" * (len(name) + 6))

    completed_process = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
    )

    return completed_process.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate demo outputs for all requirement contexts, then run "
            "multi-context validation regression tests."
        )
    )

    parser.add_argument(
        "--model",
        default="qwen3:4b",
        help="Ollama model name.",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Generation temperature.",
    )

    parser.add_argument(
        "--output-dir",
        default="scratch/demo-multi-context",
        help="Directory where regenerated demo outputs should be written.",
    )

    return parser.parse_args()


def build_case_paths(output_dir: Path, case_name: str) -> dict[str, Path]:
    return {
        "generated_prompt": output_dir / f"{case_name}-generated-prompt.txt",
        "generated_output": output_dir / f"{case_name}-generated-output.json",
        "normalized_output": output_dir / f"{case_name}-normalized-output.json",
        "enriched_output": output_dir / f"{case_name}-enriched-output.json",
    }


def validate_required_files() -> List[str]:
    missing_files = []

    required_files = [
        OLLAMA_WORKFLOW,
        MULTI_CONTEXT_REGRESSION,
        *[case["context"] for case in DEFAULT_CASES],
    ]

    for path in required_files:
        if not path.exists():
            missing_files.append(str(path))

    return missing_files


def run_context_workflow(
    case_name: str,
    context_path: Path,
    paths: dict[str, Path],
    model: str,
    temperature: float,
) -> int:
    return run_step(
        f"Generate and validate context: {case_name}",
        [
            sys.executable,
            str(OLLAMA_WORKFLOW),
            "--model",
            model,
            "--context",
            str(context_path),
            "--generated-prompt-output",
            str(paths["generated_prompt"]),
            "--generated-output",
            str(paths["generated_output"]),
            "--normalized-output",
            str(paths["normalized_output"]),
            "--enriched-output",
            str(paths["enriched_output"]),
            "--temperature",
            str(temperature),
        ],
    )


def run_multi_context_regression(
    regression_inputs: List[Tuple[Path, Path]],
) -> int:
    command = [
        sys.executable,
        str(MULTI_CONTEXT_REGRESSION),
    ]

    for output_path, context_path in regression_inputs:
        command.append(str(output_path))
        command.append(str(context_path))

    return run_step(
        "Run multi-context regression tests",
        command,
    )


def main() -> int:
    args = parse_args()
    output_dir = PROJECT_ROOT / args.output_dir

    missing_files = validate_required_files()

    if missing_files:
        print("DEMO MULTI-CONTEXT WORKFLOW RESULT: FAIL")
        print("Reason: Required files are missing.")

        for missing_file in missing_files:
            print(f"- {missing_file}")

        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    regression_inputs: List[Tuple[Path, Path]] = []

    for case in DEFAULT_CASES:
        case_name = case["name"]
        context_path = case["context"]
        paths = build_case_paths(output_dir, case_name)

        result = run_context_workflow(
            case_name=case_name,
            context_path=context_path,
            paths=paths,
            model=args.model,
            temperature=args.temperature,
        )

        if result != 0:
            print()
            print("DEMO MULTI-CONTEXT WORKFLOW RESULT: FAIL")
            print(f"Reason: Context workflow failed for {case_name}.")
            return result

        regression_inputs.append((paths["enriched_output"], context_path))

    regression_result = run_multi_context_regression(regression_inputs)

    if regression_result != 0:
        print()
        print("DEMO MULTI-CONTEXT WORKFLOW RESULT: FAIL")
        print("Reason: Multi-context regression failed.")
        return regression_result

    print()
    print("DEMO MULTI-CONTEXT WORKFLOW RESULT: PASS")
    print(f"Output directory: {output_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
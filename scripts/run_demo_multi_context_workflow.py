import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OLLAMA_WORKFLOW = PROJECT_ROOT / "scripts" / "run_ollama_requirements_workflow.py"
MULTI_CONTEXT_REGRESSION = PROJECT_ROOT / "scripts" / "run_multi_context_regression_tests.py"
RUN_REPORT_VALIDATOR = PROJECT_ROOT / "scripts" / "validate_run_report.py"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def context_case_name(context_path: Path) -> str:
    name = context_path.stem

    if name.endswith("-context"):
        name = name[: -len("-context")]

    safe_name = "".join(
        character if character.isalnum() or character in {"-", "_"} else "-"
        for character in name.lower()
    )

    return "-".join(part for part in safe_name.split("-") if part)


def discover_contexts(explicit_contexts: list[str] | None) -> list[dict[str, Path | str]]:
    if explicit_contexts:
        context_paths = [resolve_project_path(value) for value in explicit_contexts]
    else:
        context_paths = sorted((PROJECT_ROOT / "contexts").glob("*-context.json"))

    cases = []

    for context_path in context_paths:
        cases.append(
            {
                "name": context_case_name(context_path),
                "context": context_path,
            }
        )

    return cases


def run_step(name: str, command: List[str]) -> tuple[int, dict[str, Any]]:
    print()
    print(f"STEP: {name}")
    print("-" * (len(name) + 6))

    started_at = now_utc()
    started_time = time.perf_counter()

    completed_process = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
    )

    ended_at = now_utc()
    duration_seconds = round(time.perf_counter() - started_time, 3)

    step_report = {
        "name": name,
        "command": command,
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": duration_seconds,
        "return_code": completed_process.returncode,
        "result": "pass" if completed_process.returncode == 0 else "fail",
    }

    return completed_process.returncode, step_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate demo outputs for requirement contexts, then run "
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

    parser.add_argument(
        "--context",
        action="append",
        help=(
            "Optional context JSON path. Can be repeated. "
            "If omitted, all contexts/*-context.json files are used."
        ),
    )

    return parser.parse_args()


def build_case_paths(output_dir: Path, case_name: str) -> dict[str, Path]:
    return {
        "generated_prompt": output_dir / f"{case_name}-generated-prompt.txt",
        "generated_output": output_dir / f"{case_name}-generated-output.json",
        "normalized_output": output_dir / f"{case_name}-normalized-output.json",
        "enriched_output": output_dir / f"{case_name}-enriched-output.json",
        "failed_generation": output_dir / f"{case_name}-generated-output.failed-generation.txt",
        "failed_repair_1": output_dir / f"{case_name}-generated-output.failed-repair-1.txt",
    }


def remove_stale_case_outputs(paths: dict[str, Path]) -> None:
    for path in paths.values():
        if path.exists():
            path.unlink()


def validate_required_files(cases: list[dict[str, Path | str]]) -> List[str]:
    missing_files = []

    required_files = [
        OLLAMA_WORKFLOW,
        MULTI_CONTEXT_REGRESSION,
        RUN_REPORT_VALIDATOR,
        *[case["context"] for case in cases],
    ]

    for path in required_files:
        path = Path(path)

        if not path.exists():
            missing_files.append(str(path))

    return missing_files


def run_context_workflow(
    case_name: str,
    context_path: Path,
    paths: dict[str, Path],
    model: str,
    temperature: float,
) -> tuple[int, dict[str, Any]]:
    command = [
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
    ]

    result, step_report = run_step(
        f"Generate and validate context: {case_name}",
        command,
    )

    case_report = {
        "name": case_name,
        "context_path": str(context_path),
        "generated_prompt_path": str(paths["generated_prompt"]),
        "generated_output_path": str(paths["generated_output"]),
        "normalized_output_path": str(paths["normalized_output"]),
        "enriched_output_path": str(paths["enriched_output"]),
        "failed_generation_path": (
            str(paths["failed_generation"])
            if paths["failed_generation"].exists()
            else None
        ),
        "failed_repair_path": (
            str(paths["failed_repair_1"])
            if paths["failed_repair_1"].exists()
            else None
        ),
        "repair_used": paths["failed_generation"].exists(),
        "result": "pass" if result == 0 else "fail",
        "step": step_report,
    }

    return result, case_report


def run_multi_context_regression(
    regression_inputs: List[Tuple[Path, Path]],
) -> tuple[int, dict[str, Any]]:
    command = [
        sys.executable,
        str(MULTI_CONTEXT_REGRESSION),
    ]

    for output_path, context_path in regression_inputs:
        command.append(str(output_path))
        command.append(str(context_path))

    result, step_report = run_step(
        "Run multi-context regression tests",
        command,
    )

    regression_report = {
        "result": "pass" if result == 0 else "fail",
        "step": step_report,
    }

    return result, regression_report


def validate_run_report(report_path: Path) -> tuple[int, dict[str, Any]]:
    command = [
        sys.executable,
        str(RUN_REPORT_VALIDATOR),
        str(report_path),
    ]

    result, step_report = run_step(
        "Validate run report",
        command,
    )

    validation_report = {
        "result": "pass" if result == 0 else "fail",
        "step": step_report,
    }

    return result, validation_report


def main() -> int:
    args = parse_args()
    output_dir = resolve_project_path(args.output_dir)
    report_path = output_dir / "run-report.json"
    cases = discover_contexts(args.context)

    report: dict[str, Any] = {
        "workflow": "demo-multi-context",
        "model": args.model,
        "temperature": args.temperature,
        "output_dir": str(output_dir),
        "report_path": str(report_path),
        "context_discovery": {
            "mode": "explicit" if args.context else "auto",
            "pattern": "contexts/*-context.json" if not args.context else None,
            "context_count": len(cases),
        },
        "started_at": now_utc(),
        "ended_at": None,
        "duration_seconds": None,
        "result": "fail",
        "contexts": [],
        "multi_context_regression": None,
        "run_report_validation": None,
    }

    started_time = time.perf_counter()

    if not cases:
        report["ended_at"] = now_utc()
        report["duration_seconds"] = round(time.perf_counter() - started_time, 3)
        report["error"] = "No context files found."
        write_json(report_path, report)

        print("DEMO MULTI-CONTEXT WORKFLOW RESULT: FAIL")
        print("Reason: No context files found.")
        print("Expected at least one file matching: contexts/*-context.json")
        print(f"Run report written to: {report_path}")
        return 1

    missing_files = validate_required_files(cases)

    if missing_files:
        report["ended_at"] = now_utc()
        report["duration_seconds"] = round(time.perf_counter() - started_time, 3)
        report["missing_files"] = missing_files
        write_json(report_path, report)

        print("DEMO MULTI-CONTEXT WORKFLOW RESULT: FAIL")
        print("Reason: Required files are missing.")

        for missing_file in missing_files:
            print(f"- {missing_file}")

        print(f"Run report written to: {report_path}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    regression_inputs: List[Tuple[Path, Path]] = []

    print(f"Discovered {len(cases)} context file(s).")

    for case in cases:
        case_name = str(case["name"])
        context_path = Path(case["context"])
        paths = build_case_paths(output_dir, case_name)

        remove_stale_case_outputs(paths)

        result, case_report = run_context_workflow(
            case_name=case_name,
            context_path=context_path,
            paths=paths,
            model=args.model,
            temperature=args.temperature,
        )

        report["contexts"].append(case_report)
        write_json(report_path, report)

        if result != 0:
            report["ended_at"] = now_utc()
            report["duration_seconds"] = round(time.perf_counter() - started_time, 3)
            report["result"] = "fail"
            write_json(report_path, report)

            print()
            print("DEMO MULTI-CONTEXT WORKFLOW RESULT: FAIL")
            print(f"Reason: Context workflow failed for {case_name}.")
            print(f"Run report written to: {report_path}")
            return result

        regression_inputs.append((paths["enriched_output"], context_path))

    regression_result, regression_report = run_multi_context_regression(regression_inputs)
    report["multi_context_regression"] = regression_report

    if regression_result != 0:
        report["ended_at"] = now_utc()
        report["duration_seconds"] = round(time.perf_counter() - started_time, 3)
        report["result"] = "fail"
        write_json(report_path, report)

        print()
        print("DEMO MULTI-CONTEXT WORKFLOW RESULT: FAIL")
        print("Reason: Multi-context regression failed.")
        print(f"Run report written to: {report_path}")
        return regression_result

    report["ended_at"] = now_utc()
    report["duration_seconds"] = round(time.perf_counter() - started_time, 3)
    report["result"] = "pass"
    write_json(report_path, report)

    report_validation_result, report_validation = validate_run_report(report_path)
    report["run_report_validation"] = report_validation
    write_json(report_path, report)

    if report_validation_result != 0:
        print()
        print("DEMO MULTI-CONTEXT WORKFLOW RESULT: FAIL")
        print("Reason: Run report validation failed.")
        print(f"Run report written to: {report_path}")
        return report_validation_result

    print()
    print("DEMO MULTI-CONTEXT WORKFLOW RESULT: PASS")
    print(f"Context count: {len(cases)}")
    print(f"Output directory: {output_dir}")
    print(f"Run report written to: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
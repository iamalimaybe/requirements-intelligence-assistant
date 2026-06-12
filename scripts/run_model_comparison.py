import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_WORKFLOW = PROJECT_ROOT / "scripts" / "run_demo_multi_context_workflow.py"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_model_name(model: str) -> str:
    safe_name = "".join(
        character if character.isalnum() or character in {"-", "_"} else "-"
        for character in model.lower()
    )

    return "-".join(part for part in safe_name.split("-") if part)


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")

    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the reproducible demo workflow across one or more Ollama models."
    )

    parser.add_argument(
        "--model",
        action="append",
        required=True,
        help="Ollama model name. Can be repeated.",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Generation temperature.",
    )

    parser.add_argument(
        "--output-dir",
        default="scratch/model-comparison",
        help="Directory where comparison reports should be written.",
    )

    return parser.parse_args()


def count_repairs(run_report: dict[str, Any]) -> int:
    contexts = run_report.get("contexts", [])

    if not isinstance(contexts, list):
        return 0

    return sum(
        1
        for context in contexts
        if isinstance(context, dict) and context.get("repair_used") is True
    )


def count_failed_contexts(run_report: dict[str, Any]) -> int:
    contexts = run_report.get("contexts", [])

    if not isinstance(contexts, list):
        return 0

    return sum(
        1
        for context in contexts
        if isinstance(context, dict) and context.get("result") != "pass"
    )


def context_count(run_report: dict[str, Any]) -> int:
    context_discovery = run_report.get("context_discovery", {})

    if isinstance(context_discovery, dict):
        value = context_discovery.get("context_count")

        if isinstance(value, int):
            return value

    contexts = run_report.get("contexts", [])

    if isinstance(contexts, list):
        return len(contexts)

    return 0


def nested_result(run_report: dict[str, Any], key: str) -> str:
    value = run_report.get(key)

    if isinstance(value, dict):
        result = value.get("result")

        if isinstance(result, str):
            return result

    return "missing"


def run_demo_for_model(
    model: str,
    temperature: float,
    model_output_dir: Path,
) -> tuple[int, dict[str, Any]]:
    command = [
        sys.executable,
        str(DEMO_WORKFLOW),
        "--model",
        model,
        "--temperature",
        str(temperature),
        "--output-dir",
        str(model_output_dir),
    ]

    print()
    print(f"MODEL: {model}")
    print("-" * (len(model) + 7))

    started_at = now_utc()
    started_time = time.perf_counter()

    completed_process = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
    )

    ended_at = now_utc()
    duration_seconds = round(time.perf_counter() - started_time, 3)
    run_report_path = model_output_dir / "run-report.json"

    summary: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "result": "fail",
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": duration_seconds,
        "return_code": completed_process.returncode,
        "output_dir": str(model_output_dir),
        "run_report_path": str(run_report_path),
        "context_count": 0,
        "repair_count": 0,
        "failed_context_count": 0,
        "multi_context_regression": "missing",
        "run_report_validation": "missing",
    }

    if run_report_path.exists():
        try:
            run_report = load_json(run_report_path)
            summary["result"] = str(run_report.get("result", "fail"))
            summary["context_count"] = context_count(run_report)
            summary["repair_count"] = count_repairs(run_report)
            summary["failed_context_count"] = count_failed_contexts(run_report)
            summary["multi_context_regression"] = nested_result(
                run_report,
                "multi_context_regression",
            )
            summary["run_report_validation"] = nested_result(
                run_report,
                "run_report_validation",
            )
        except (json.JSONDecodeError, ValueError) as error:
            summary["result"] = "fail"
            summary["error"] = f"Could not read run report: {error}"
    else:
        summary["error"] = "Run report was not written."

    if completed_process.returncode != 0:
        summary["result"] = "fail"

    return completed_process.returncode, summary


def print_summary_table(results: list[dict[str, Any]]) -> None:
    headers = [
        "model",
        "result",
        "contexts",
        "repairs",
        "failed_ctx",
        "regression",
        "report",
        "duration_s",
    ]

    rows = []

    for result in results:
        rows.append(
            [
                str(result.get("model", "")),
                str(result.get("result", "")),
                str(result.get("context_count", "")),
                str(result.get("repair_count", "")),
                str(result.get("failed_context_count", "")),
                str(result.get("multi_context_regression", "")),
                str(result.get("run_report_validation", "")),
                str(result.get("duration_seconds", "")),
            ]
        )

    column_widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    header_line = "  ".join(
        headers[index].ljust(column_widths[index])
        for index in range(len(headers))
    )

    separator = "  ".join("-" * width for width in column_widths)

    print()
    print("MODEL COMPARISON SUMMARY")
    print("------------------------")
    print(header_line)
    print(separator)

    for row in rows:
        print(
            "  ".join(
                row[index].ljust(column_widths[index])
                for index in range(len(headers))
            )
        )


def main() -> int:
    args = parse_args()

    if not DEMO_WORKFLOW.exists():
        print(f"FAIL: Demo workflow script does not exist: {DEMO_WORKFLOW}")
        return 1

    output_dir = resolve_project_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    comparison_started_at = now_utc()
    comparison_started_time = time.perf_counter()

    results: list[dict[str, Any]] = []

    for model in args.model:
        model_output_dir = output_dir / safe_model_name(model)

        _, summary = run_demo_for_model(
            model=model,
            temperature=args.temperature,
            model_output_dir=model_output_dir,
        )

        results.append(summary)

    comparison_report = {
        "workflow": "model-comparison",
        "started_at": comparison_started_at,
        "ended_at": now_utc(),
        "duration_seconds": round(time.perf_counter() - comparison_started_time, 3),
        "temperature": args.temperature,
        "model_count": len(args.model),
        "result": "pass"
        if all(result.get("result") == "pass" for result in results)
        else "fail",
        "results": results,
    }

    summary_path = output_dir / "model-comparison-summary.json"
    write_json(summary_path, comparison_report)

    print_summary_table(results)

    print()
    print(f"Model comparison summary written to: {summary_path}")

    if comparison_report["result"] != "pass":
        print("MODEL COMPARISON RESULT: FAIL")
        return 1

    print("MODEL COMPARISON RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
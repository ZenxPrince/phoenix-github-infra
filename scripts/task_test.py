"""
task_test.py — Testing and Validation
"""

import json
import subprocess
from pathlib import Path


def run(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def main():
    print("=== Phoenix Test & Validation ===")
    print()

    results = {}

    # Python compilation
    python_files = list(Path(".").rglob("*.py"))
    compile_failures = []

    for file in python_files:
        code, output = run(["python", "-m", "py_compile", str(file)])

        if code != 0:
            compile_failures.append({
                "file": str(file),
                "error": output[-1000:],
            })

    results["python_compile"] = {
        "status": "ok" if not compile_failures else "fail",
        "files_checked": len(python_files),
        "failures": compile_failures,
    }

    print(
        f"Python compilation: "
        f"{'PASS' if not compile_failures else 'FAIL'}"
    )

    # JSON validation
    json_files = list(Path(".").rglob("*.json"))
    json_failures = []

    for file in json_files:
        try:
            json.loads(file.read_text(encoding="utf-8"))
        except Exception as exc:
            json_failures.append({
                "file": str(file),
                "error": str(exc),
            })

    results["json_validation"] = {
        "status": "ok" if not json_failures else "fail",
        "files_checked": len(json_files),
        "failures": json_failures,
    }

    print(
        f"JSON validation: "
        f"{'PASS' if not json_failures else 'FAIL'}"
    )

    # Ruff
    ruff_code, ruff_output = run(["ruff", "check", "scripts"])

    results["ruff"] = {
        "status": "ok" if ruff_code == 0 else "warn",
        "output": ruff_output[-2000:],
    }

    print(
        f"Ruff: "
        f"{'PASS' if ruff_code == 0 else 'WARN'}"
    )

    Path("logs").mkdir(exist_ok=True)

    report = Path("logs/test_results.json")
    report.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Report written: {report}")


if __name__ == "__main__":
    main()

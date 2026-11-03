"""
task_deps.py — Dependency and Vulnerability Checks
"""

import subprocess
from pathlib import Path
from datetime import datetime, timezone


def run(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def main():
    print("=== Phoenix Dependency Check ===")
    print()

    Path("logs").mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    output = [
        f"Phoenix Dependency Check — {timestamp}",
        "",
    ]

    # Check outdated Python packages.
    code, result = run(
        ["python", "-m", "pip", "list", "--outdated"]
    )

    output.append("=== Outdated Python Packages ===")
    output.append(result if result else "No outdated packages reported.")
    output.append("")

    # Safety vulnerability scan when available.
    safety_code, safety_result = run(
        ["safety", "check"]
    )

    output.append("=== Safety Vulnerability Scan ===")

    if safety_code == 0:
        output.append(
            safety_result
            if safety_result
            else "No vulnerabilities reported."
        )
    else:
        output.append(
            "Safety command unavailable or reported an issue:"
        )
        output.append(safety_result)

    output.append("")

    report = Path("logs/dependencies.log")
    report.write_text(
        "\n".join(output),
        encoding="utf-8",
    )

    print(f"Report written: {report}")


if __name__ == "__main__":
    main()

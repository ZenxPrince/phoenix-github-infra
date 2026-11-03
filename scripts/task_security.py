"""
task_security.py — Security and Repository Hardening Checks
"""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SECRET_PATTERNS = [
    r"ghp_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"LEETCODE_SESSION\s*[:=]\s*[\"'][^\"']+[\"']",
]


def run(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def scan_files():
    findings = []

    _, output = run([
        "git",
        "grep",
        "-n",
        "-I",
        "-E",
        "|".join(SECRET_PATTERNS),
    ])

    if output:
        findings.extend(output.splitlines())

    return findings


def check_gitignore():
    path = Path(".gitignore")

    if not path.exists():
        return ["Missing .gitignore"]

    content = path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    required = [
        ".env",
        ".env.*",
        "*.log",
        ".sync_state.json",
    ]

    return [
        item
        for item in required
        if item not in content
    ]


def main():
    print("=== Phoenix Security Check ===")
    print()

    Path("docs").mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    secret_findings = scan_files()
    gitignore_findings = check_gitignore()

    bandit_code, bandit_output = run([
        "bandit",
        "-r",
        "scripts",
        "-q",
    ])

    report = [
        "# Security Log",
        "",
        f"Generated: {timestamp}",
        "",
        "## Secret Pattern Scan",
        "",
    ]

    if secret_findings:
        report.append(
            f"Potential findings: {len(secret_findings)}"
        )
        report.extend(
            f"- {finding}"
            for finding in secret_findings
        )
    else:
        report.append("No configured secret patterns detected.")

    report.extend([
        "",
        "## .gitignore Coverage",
        "",
    ])

    if gitignore_findings:
        report.append(
            "Missing expected protections:"
        )
        report.extend(
            f"- {item}"
            for item in gitignore_findings
        )
    else:
        report.append(
            "Expected sensitive-file protections present."
        )

    report.extend([
        "",
        "## Bandit SAST",
        "",
    ])

    if bandit_code == 0:
        report.append(
            "Bandit completed without reported findings."
        )
    else:
        report.append(
            "Bandit reported findings or could not complete:"
        )
        report.append(bandit_output[-4000:])

    (Path("docs") / "SECURITY_LOG.md").write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    print("Created: docs/SECURITY_LOG.md")

    if secret_findings:
        print(
            f"WARNING: {len(secret_findings)} potential "
            "secret-pattern finding(s)."
        )

    if gitignore_findings:
        print(
            f"WARNING: {len(gitignore_findings)} "
            ".gitignore protection(s) missing."
        )

    print("Security check complete.")


if __name__ == "__main__":
    main()

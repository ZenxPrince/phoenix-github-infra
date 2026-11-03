"""
task_health.py — Repository Health Check
Verifies file integrity, Git integrity, workflow states, and commit cadence.
"""

import os
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from github import Github
    HAS_PYGITHUB = True
except ImportError:
    HAS_PYGITHUB = False

REPO_NAME = os.environ.get("REPO", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def run(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).strip()


def check_required_files() -> list[str]:
    required = [
        "README.md",
        ".github/workflows/autonomous-engineering.yml",
        "scripts/task_health.py",
    ]
    return [f for f in required if not Path(f).exists()]


def check_git_integrity() -> dict:
    code, out = run(["git", "fsck", "--no-dangling", "--quiet"])
    return {
        "status": "ok" if code == 0 else "warn",
        "output": out[:500],
    }


def check_commit_cadence() -> dict:
    code, out = run([
        "git",
        "log",
        "--oneline",
        "--since=7 days ago",
        "--format=%H %ai %s",
    ])

    lines = [line for line in out.splitlines() if line.strip()]

    return {
        "commits_last_7d": len(lines),
        "recent": lines[:5],
    }


def check_large_files() -> list[str]:
    code, out = run(["git", "ls-files", "-z"])

    if code != 0:
        return []

    large = []

    for filename in out.split("\0"):
        if not filename:
            continue

        path = Path(filename)

        if path.exists() and path.stat().st_size > 10 * 1024 * 1024:
            size_mb = path.stat().st_size // 1024 // 1024
            large.append(f"{filename} ({size_mb} MB)")

    return large


def check_github_actions() -> dict:
    if not HAS_PYGITHUB or not TOKEN or not REPO_NAME:
        return {
            "status": "skipped",
            "reason": "GitHub API configuration unavailable",
        }

    try:
        github = Github(TOKEN)
        repo = github.get_repo(REPO_NAME)

        runs = repo.get_workflow_runs(status="failure")

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        recent_failures = []

        for workflow_run in runs:
            if workflow_run.created_at < cutoff:
                break

            recent_failures.append({
                "name": workflow_run.name,
                "created": workflow_run.created_at.isoformat(),
                "url": workflow_run.html_url,
            })

            if len(recent_failures) >= 5:
                break

        return {
            "status": "ok" if not recent_failures else "warn",
            "recent_failures": recent_failures,
        }

    except Exception as exc:
        return {
            "status": "error",
            "reason": str(exc),
        }


def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print(f"=== Repository Health Check — {timestamp} ===")
    print()

    results = {}

    missing = check_required_files()

    results["required_files"] = {
        "status": "ok" if not missing else "warn",
        "missing": missing,
    }

    icon = "✅" if not missing else "⚠️"
    print(
        f"{icon} Required files: "
        f"{'all present' if not missing else f'{len(missing)} missing: {missing}'}"
    )

    git_ok = check_git_integrity()
    results["git_integrity"] = git_ok

    icon = "✅" if git_ok["status"] == "ok" else "⚠️"
    print(f"{icon} Git integrity: {git_ok['status']}")

    cadence = check_commit_cadence()
    results["commit_cadence"] = cadence

    print(f"📊 Commits last 7 days: {cadence['commits_last_7d']}")

    for commit in cadence["recent"][:3]:
        print(f"   {commit}")

    large = check_large_files()
    results["large_files"] = large

    icon = "✅" if not large else "⚠️"
    print(f"{icon} Large files (>10 MB): {len(large)}")

    for filename in large:
        print(f"   {filename}")

    failures = check_github_actions()
    results["recent_failures"] = failures

    failure_count = len(failures.get("recent_failures", []))

    icon = "✅" if failure_count == 0 else "⚠️"
    print(f"{icon} Recent workflow failures (7d): {failure_count}")

    Path("logs").mkdir(exist_ok=True)

    report_path = Path(
        f"logs/health_{datetime.now().strftime('%Y%m%d')}.json"
    )

    report_path.write_text(
        json.dumps(results, indent=2, default=str),
        encoding="utf-8",
    )

    print(f"\n📄 Report written: {report_path}")

    warnings = sum(
        1
        for value in results.values()
        if isinstance(value, dict)
        and value.get("status") == "warn"
    )

    if warnings:
        print(f"\n⚠️ {warnings} warning(s) found — review logs above.")
    else:
        print("\n✅ All health checks passed.")


if __name__ == "__main__":
    main()

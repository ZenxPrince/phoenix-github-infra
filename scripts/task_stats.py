"""
task_stats.py — Repository Engineering Statistics
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def main():
    print("=== Phoenix Repository Statistics ===")

    Path("docs").mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    _, commit_output = run([
        "git",
        "log",
        "--since=30 days ago",
        "--format=%H",
    ])

    commits_30d = len([
        line for line in commit_output.splitlines()
        if line.strip()
    ])

    _, file_output = run([
        "git",
        "ls-files",
    ])

    tracked_files = [
        line for line in file_output.splitlines()
        if line.strip()
    ]

    extension_counts = {}

    for filename in tracked_files:
        suffix = Path(filename).suffix.lower() or "[no extension]"
        extension_counts[suffix] = extension_counts.get(suffix, 0) + 1

    stats = {
        "generated_at": timestamp,
        "commits_last_30_days": commits_30d,
        "tracked_files": len(tracked_files),
        "file_extensions": dict(
            sorted(
                extension_counts.items(),
                key=lambda item: (-item[1], item[0])
            )
        ),
    }

    (Path("docs") / "stats.json").write_text(
        json.dumps(stats, indent=2),
        encoding="utf-8",
    )

    report = f"""# Repository Statistics

Generated: {timestamp}

## Overview

- Tracked files: {len(tracked_files)}
- Commits in last 30 days: {commits_30d}

## File Distribution

"""

    for extension, count in sorted(
        extension_counts.items(),
        key=lambda item: (-item[1], item[0])
    ):
        report += f"- `{extension}`: {count}\n"

    (Path("docs") / "STATS.md").write_text(
        report,
        encoding="utf-8",
    )

    print("Created: docs/stats.json")
    print("Created: docs/STATS.md")


if __name__ == "__main__":
    main()

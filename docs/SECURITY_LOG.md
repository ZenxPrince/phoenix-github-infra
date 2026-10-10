# Security Log

Generated: 2026-10-10 10:04 UTC

## Secret Pattern Scan

Potential findings: 1
- fatal: command line, 'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|LEETCODE_SESSION\s*[:=]\s*[\"'][^\"']+[\"']': Invalid preceding regular expression

## .gitignore Coverage

Expected sensitive-file protections present.

## Bandit SAST

Bandit reported findings or could not complete:
Location: scripts/task_health.py:23:13
22	def run(cmd: list[str]) -> tuple[int, str]:
23	    result = subprocess.run(cmd, capture_output=True, text=True)
24	    return result.returncode, (result.stdout + result.stderr).strip()

--------------------------------------------------
>> Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess
   Location: scripts/task_security.py:6:0
5	import re
6	import subprocess
7	from datetime import datetime, timezone

--------------------------------------------------
>> Issue: [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html
   Location: scripts/task_security.py:21:13
20	def run(command):
21	    result = subprocess.run(
22	        command,
23	        capture_output=True,
24	        text=True,
25	    )
26	    return result.returncode, (result.stdout + result.stderr).strip()

--------------------------------------------------
>> Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess
   Location: scripts/task_stats.py:6:0
5	import json
6	import subprocess
7	from datetime import datetime, timezone

--------------------------------------------------
>> Issue: [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html
   Location: scripts/task_stats.py:12:13
11	def run(command):
12	    result = subprocess.run(
13	        command,
14	        capture_output=True,
15	        text=True,
16	    )
17	    return result.returncode, (result.stdout + result.stderr).strip()

--------------------------------------------------
>> Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_imports.html#b404-import-subprocess
   Location: scripts/task_test.py:6:0
5	import json
6	import subprocess
7	from pathlib import Path

--------------------------------------------------
>> Issue: [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input.
   Severity: Low   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b603_subprocess_without_shell_equals_true.html
   Location: scripts/task_test.py:11:13
10	def run(command):
11	    result = subprocess.run(
12	        command,
13	        capture_output=True,
14	        text=True,
15	    )
16	    return result.returncode, (result.stdout + result.stderr).strip()

--------------------------------------------------

Code scanned:
	Total lines of code: 811
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 10
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 10
Files skipped (1):
	scripts/sync_leetcode.py (syntax error while parsing AST from file)
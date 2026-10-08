import os, sys, json, time, re, requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# â”€â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SESSION   = os.environ.get("LEETCODE_SESSION", "")
CSRF      = os.environ.get("LEETCODE_CSRF", "")
FORCE     = os.environ.get("FORCE_FULL_SYNC", "false").lower() == "true"`r`nLEETCODE_USERNAME = os.environ.get("LEETCODE_USERNAME", "ZenxPrince")
STATE_FILE = Path(".sync_state.json")

LANG_EXT = {
    "python"     : ".py",
    "python3"    : ".py",
    "cpp"        : ".cpp",
    "c"          : ".c",
    "java"       : ".java",
    "javascript" : ".js",
    "typescript" : ".ts",
    "golang"     : ".go",
    "rust"       : ".rs",
    "kotlin"     : ".kt",
    "swift"      : ".swift",
    "scala"      : ".scala",
    "ruby"       : ".rb",
    "php"        : ".php",
    "csharp"     : ".cs",
    "bash"       : ".sh",
    "sql"        : ".sql",
    "mysql"      : ".sql",
    "mssql"      : ".sql",
    "oraclesql"  : ".sql",
    "dart"       : ".dart",
    "racket"     : ".rkt",
    "erlang"     : ".erl",
    "elixir"     : ".ex",
}

LANG_COMMENT = {
    "python": "#", "python3": "#", "ruby": "#", "bash": "#", "sql": "--",
    "mysql": "--", "mssql": "--", "oraclesql": "--",
    "cpp": "//", "c": "//", "java": "//", "javascript": "//",
    "typescript": "//", "golang": "//", "rust": "//", "kotlin": "//",
    "swift": "//", "scala": "//", "php": "//", "csharp": "//",
    "dart": "//",
}

HEADERS = {
    "Cookie"           : f"LEETCODE_SESSION={SESSION}; csrftoken={CSRF}",
    "X-CSRFToken"      : CSRF,
    "Referer"          : "https://leetcode.com/",
    "Content-Type"     : "application/json",
    "User-Agent"       : "Mozilla/5.0 (compatible; LeetCodeSync/3.0)",
}

GQL_URL = "https://leetcode.com/graphql"

# â”€â”€â”€ State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"synced": {}, "last_sync": None}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

# â”€â”€â”€ GraphQL helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def gql(query: str, variables: dict = {}, retries: int = 3) -> Optional[dict]:
    for attempt in range(retries):
        try:
            r = requests.post(GQL_URL,
                json={"query": query, "variables": variables},
                headers=HEADERS, timeout=30)
            if r.status_code == 403:
                print("â›” 403 Forbidden â€” check LEETCODE_SESSION and LEETCODE_CSRF secrets.")
                sys.exit(1)
            if r.status_code == 429:
                wait = 60 * (attempt + 1)
                print(f"â³ Rate limited â€” waiting {wait}sâ€¦")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json().get("data")
        except requests.RequestException as e:
            print(f"âš ï¸  Request error (attempt {attempt+1}): {e}")
            time.sleep(10 * (attempt + 1))
    return None

# â”€â”€â”€ Fetch accepted submissions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SUBMISSIONS_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
  }
}
"""
PROBLEM_DETAIL_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    questionFrontendId
    title
    titleSlug
    difficulty
    topicTags { name }
    content
  }
}
"""

SUBMISSION_DETAIL_QUERY = """
query submissionDetails($submissionId: Int!) {
  submissionDetails(submissionId: $submissionId) {
    code
    lang { verboseName }
    runtimeMs
    memoryMB
    timestamp
  }
}
"""

def fetch_all_accepted(state: dict) -> list[dict]:
    accepted = []
    offset = 0
    limit = 20
    last_key = None
    seen = set(state["synced"].keys()) if not FORCE else set()

    print(f"ðŸ” Fetching submissions (force_full={FORCE})â€¦")

    while True:
        vars_ = {"offset": offset, "limit": limit}
        if last_key:
            vars_["lastKey"] = last_key

        data = gql(SUBMISSIONS_QUERY, vars_)
        if not data:
            break

        sl = data.get("submissionList", {})
        subs = sl.get("submissions", [])
        if not subs:
            break

        for s in subs:
            if s["statusDisplay"] != "Accepted":
                continue
            key = f"{s['titleSlug']}_{s['lang']}"
            if key in seen:
                continue
            accepted.append(s)
            seen.add(key)

        if not sl.get("hasNext", False):
            break

        last_key = sl.get("lastKey")
        offset += limit
        time.sleep(1.5)   # polite rate limiting

    print(f"ðŸ“¥ Found {len(accepted)} new accepted solution(s) to sync.")
    return accepted

def fetch_problem_detail(slug: str) -> Optional[dict]:
    data = gql(PROBLEM_DETAIL_QUERY, {"titleSlug": slug})
    return data.get("question") if data else None

def fetch_submission_code(sub_id: str) -> Optional[dict]:
    data = gql(SUBMISSION_DETAIL_QUERY, {"submissionId": int(sub_id)})
    return data.get("submissionDetails") if data else None

# â”€â”€â”€ File generation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

def build_comment_header(lang: str, problem: dict, detail: dict) -> str:
    cm = LANG_COMMENT.get(lang, "//")
    tags = ", ".join(t["name"] for t in (problem.get("topicTags") or []))
    runtime = detail.get("runtimeMs", "N/A")
    memory  = detail.get("memoryMB",  "N/A")
    ts      = datetime.fromtimestamp(int(detail.get("timestamp", 0)), tz=timezone.utc)
    lines = [
        f"{cm} â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
        f"{cm} Problem  : {problem['questionFrontendId']}. {problem['title']}",
        f"{cm} Difficulty: {problem.get('difficulty', 'Unknown')}",
        f"{cm} Topics   : {tags or 'N/A'}",
        f"{cm} Runtime  : {runtime} ms",
        f"{cm} Memory   : {memory} MB",
        f"{cm} Solved   : {ts.strftime('%Y-%m-%d')}",
        f"{cm} URL      : https://leetcode.com/problems/{problem['titleSlug']}/",
        f"{cm} â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
        "",
    ]
    return "\n".join(lines)

def write_solution(problem: dict, sub: dict, detail: dict):
    pid     = problem["questionFrontendId"].zfill(4)
    title   = problem["title"]
    slug    = problem["titleSlug"]
    diff    = problem.get("difficulty", "Unknown").lower()
    lang    = sub["lang"].lower()
    ext     = LANG_EXT.get(lang, f".{lang}")
    lang_dir = lang.replace("python3", "python")

    folder = Path(f"{diff}/{pid}-{slugify(title)}")
    folder.mkdir(parents=True, exist_ok=True)

    # README per problem (once)
    readme = folder / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# {pid}. {title}\n\n"
            f"**Difficulty:** {problem.get('difficulty', 'Unknown')}  \n"
            f"**Topics:** {', '.join(t['name'] for t in (problem.get('topicTags') or []))}\n\n"
            f"[View on LeetCode](https://leetcode.com/problems/{slug}/)\n"
        )

    # Solution file
    sol_file = folder / f"solution{ext}"
    header = build_comment_header(lang, problem, detail)
    code = detail.get("code", "# code not available")
    sol_file.write_text(header + code + "\n")

    print(f"  âœ…  {pid}. {title} ({lang}) â†’ {sol_file}")
    return str(sol_file)

# â”€â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def update_readme_summary(state: dict):
    total = len(state["synced"])
    by_diff = {}
    for v in state["synced"].values():
        d = v.get("difficulty", "Unknown")
        by_diff[d] = by_diff.get(d, 0) + 1

    readme = Path("README.md")
    content = f"""# ZenxPrince â€” LeetCode Solutions

Auto-synced via [Phoenix Engineering Infrastructure](https://github.com/ZenxPrince).

## Progress

| Total | Easy | Medium | Hard |
|-------|------|--------|------|
| {total} | {by_diff.get('Easy', 0)} | {by_diff.get('Medium', 0)} | {by_diff.get('Hard', 0)} |

_Last synced: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_

## Structure

```
<difficulty>/
  <id>-<problem-slug>/
    README.md          # problem description & metadata
    solution.<ext>     # accepted solution with header comment
```

> Solutions are organized by difficulty, then by problem ID.
"""
    readme.write_text(content)

def main():
    if not SESSION or not CSRF:
        print("âš ï¸  LEETCODE_SESSION or LEETCODE_CSRF not set â€” skipping sync.")
        sys.exit(0)

    state = load_state()
    submissions = fetch_all_accepted(state)

    if not submissions:
        print("âœ… Nothing new to sync.")
        update_readme_summary(state)
        save_state(state)
        return

    synced_count = 0
    for sub in submissions:
        slug = sub["titleSlug"]
        lang = sub["lang"].lower()
        key  = f"{slug}_{lang}"

        print(f"\nâ†’ {sub['title']} ({lang})")

        problem = fetch_problem_detail(slug)
        if not problem:
            print(f"  âš ï¸  Could not fetch problem detail â€” skipping.")
            continue

        detail = fetch_submission_code(sub["id"])
        if not detail:
            print(f"  âš ï¸  Could not fetch submission code â€” skipping.")
            continue

        write_solution(problem, sub, detail)

        state["synced"][key] = {
            "title"      : sub["title"],
            "difficulty" : problem.get("difficulty", "Unknown"),
            "lang"       : lang,
            "synced_at"  : datetime.now(timezone.utc).isoformat(),
        }
        synced_count += 1
        time.sleep(1)   # polite pacing

    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    update_readme_summary(state)
    save_state(state)

    print(f"\nðŸŽ‰ Synced {synced_count} solution(s).")
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write(f"synced_count={synced_count}\n")

main()

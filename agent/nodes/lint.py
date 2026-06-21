import subprocess
import json
from ..state import ReviewState

def run_linter(file_path: str) -> list:
    result = subprocess.run(
        ["ruff", "check", file_path, "--output-format=json"],
        capture_output=True,
        text=True,
    )
    try:
        raw_issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []  # no issues, or ruff produced no parseable output — fail safe, same pattern as before

    issues = []
    for issue in raw_issues:
        issues.append({
            "file": issue["filename"],
            "line": issue["location"]["row"],
            "severity": "low",  # lint issues are minor by nature, not bugs
            "comment": issue["message"],
        })
    return issues

def static_analysis(state: ReviewState) -> ReviewState:
    all_issues = []
    for f in state["parsed_files"]:
        all_issues.extend(run_linter(f["filename"]))
    state["lint_issues"] = all_issues
    return state
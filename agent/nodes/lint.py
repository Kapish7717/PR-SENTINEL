import subprocess
import json
from ..state import ReviewState
import os
import tempfile
import requests
def run_linter(file_path: str,original_filename:str=None) -> list:
    import sys
    executable_dir = os.path.dirname(sys.executable)
    ruff_path = os.path.join(executable_dir, "ruff.exe")
    if not os.path.exists(ruff_path):
        ruff_path = os.path.join(executable_dir, "ruff")
    if not os.path.exists(ruff_path):
        ruff_path = "ruff"

    result = subprocess.run(
        [ruff_path, "check", file_path, "--output-format=json"],
        capture_output=True,
        text=True,
    )
    try:
        raw_issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []  # no issues, or ruff produced no parseable output — fail safe, same pattern as before

    issues = []
    severity_map = {"error": "medium", "warning": "low"}
    for issue in raw_issues:
        issues.append({
            "file": original_filename or os.path.basename(issue["filename"]),
            "line": issue["location"]["row"],
            "severity": severity_map.get(issue.get("severity", "warning"), "low"),  # lint issues are minor by nature, not bugs
            "comment": issue["message"],
        })
    return issues

def get_pr_head_sha(owner: str, repo: str, pr_number: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {}
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token.strip()}"
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get("head", {}).get("sha", "")
    except Exception:
        pass
    return ""

def get_file_content(owner: str, repo: str, filename: str, ref: str = None) -> str:
    ref_param = f"?ref={ref}" if ref else ""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}{ref_param}"
    headers = {
        "Accept": "application/vnd.github.v3.raw"
    }
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token.strip()}"
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.text
    except Exception:
        pass
    return ""

def static_analysis(state: ReviewState) -> ReviewState:
    all_issues = []
    owner = state.get("owner")
    repo = state.get("repo")
    pr_number = state.get("pr_number")

    ref = None
    if owner and repo and pr_number:
        ref = get_pr_head_sha(owner, repo, pr_number)

    for f in state["parsed_files"]:
        filename = f["filename"]
        if not filename.endswith(".py"):
            continue

        content = ""
        # 1. First, check if file exists locally on disk
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file_obj:
                content = file_obj.read()
        # 2. If running on a GitHub PR, fetch the file content from the PR branch/commit
        elif owner and repo:
            content = get_file_content(owner, repo, filename, ref)

        if not content:
            continue

        # Run linter on content string using temporary file
        raw_issues = lint_from_content(filename, content)
        filtered = filter_to_changed_lines(raw_issues, state["parsed_files"])
        all_issues.extend(filtered)

    state["lint_issues"] = all_issues
    return state

def filter_to_changed_lines(lint_issues,parsed_files):
    changed_lines_by_file = {
        f["filename"]: {line_no for line_no, _ in f["added_lines"]}
        for f in parsed_files
    }
    return [
          issue for issue in lint_issues
          if issue["line"] in changed_lines_by_file.get(issue["file"], set())
      ]
    
def lint_from_content(filename:str,content:str)->list:
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        return run_linter(tmp_path,original_filename=filename)
    finally:
        os.unlink(tmp_path)
import requests

def get_pr_diff(owner: str, repo_name: str, pr_number: int, token: str) -> str:
    """
    Fetch the diff of a GitHub Pull Request as raw text.
    """
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def post_review_comment(
    owner: str,
    repo_name: str,
    pr_number: int,
    commit_sha: str,
    path: str,
    line: int,
    body: str,
    token: str
) -> dict:
    """
    Post an inline review comment on a specific line of a file in a Pull Request.
    """
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "body": body,
        "commit_id": commit_sha,
        "path": path,
        "line": line,
        "side": "RIGHT"  # RIGHT corresponds to the 'after' version of the code (added lines)
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 201:
        # Log failure but do not crash the pipeline if a comment fails to post
        print(f"Failed to post comment to {path}:{line}. Response: {response.text}")
        return {}
    return response.json()

def set_commit_status(
    owner: str,
    repo_name: str,
    sha: str,
    state: str,
    description: str,
    token: str
) -> dict:
    """
    Set the commit/check status on GitHub.
    state: 'pending' | 'success' | 'failure' | 'error'
    """
    url = f"https://api.github.com/repos/{owner}/{repo_name}/statuses/{sha}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "state": state,
        "description": description[:140],  # GitHub caps description at 140 characters
        "context": "PR Sentinel"
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

import os
import requests
from mcp.server.fastmcp import FastMCP
from agent.nodes.lint import lint_from_content

# Initialize FastMCP server
mcp = FastMCP("PR-Sentinel")

@mcp.tool()
async def get_pr_diff(owner: str, repo: str, pr_number: str) -> str:
    """
    Fetch the diff of a GitHub Pull Request.
    
    Args:
        owner: The owner of the repository (e.g. "psf")
        repo: The repository name (e.g. "requests")
        pr_number: The pull request number (e.g. "6169")
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    headers = {
        "Accept": "application/vnd.github.v3.diff"
    }

    # Fetch token from environment if configured
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token.strip()}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.text

@mcp.tool()
def run_linter(filename: str, content: str) -> list:
    """
    Run ruff linter on the provided file content.
    
    Args:
        filename: The name of the file (e.g. "app.py")
        content: The code content of the file
    """
    return lint_from_content(filename, content)

if __name__ == "__main__":
    mcp.run()

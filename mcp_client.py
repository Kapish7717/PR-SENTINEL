from mcp.server.fastmcp import FastMCP
import requests
import os
mcp = FastMCP("PR-Sentinel")


@mcp.tool()
async def get_pr_diff(owner:str,repo:str,pr_number:str)->str:
    """
    Fetch the diff of a GitHub Pull Request.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }

    response = requests.get(url, headers=headers)

    response.raise_for_status()

    return response.text



import os
import sys
import json
import argparse
import asyncio

# Add parent directory of 'scripts' to python search path to support running from workspace root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env manually before other imports
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from agent.graph import graph

def main():
    parser = argparse.ArgumentParser(description="Run PR Sentinel locally or on a GitHub PR.")
    parser.add_argument("--owner", help="GitHub repository owner (e.g., 'psf')")
    parser.add_argument("--repo", help="GitHub repository name (e.g., 'requests')")
    parser.add_argument("--pr", type=int, help="GitHub Pull Request number (e.g., 6169)")
    parser.add_argument("--patch", default="sample.patch", help="Path to a local patch file (default: sample.patch)")

    args = parser.parse_args()

    raw_diff = ""
    if args.owner and args.repo and args.pr:
        from mcp_tools.server import get_pr_diff
        print(f"Fetching diff for GitHub PR {args.owner}/{args.repo}#{args.pr}...")
        try:
            raw_diff = asyncio.run(get_pr_diff(args.owner, args.repo, str(args.pr)))
        except Exception as e:
            print(f"Failed to fetch PR diff from GitHub: {e}")
            sys.exit(1)
    else:
        # Fall back to local patch file
        patch_path = os.path.abspath(args.patch)
        if not os.path.exists(patch_path):
            # Check relative path
            patch_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", args.patch))

        if not os.path.exists(patch_path):
            print(f"Error: local patch file not found at {args.patch}")
            sys.exit(1)

        print(f"Reading local patch file: {patch_path}")
        with open(patch_path, "r", encoding="utf-8") as f:
            raw_diff = f.read()

    initial_state = {
        "raw_diff": raw_diff,
        "parsed_files": [],
        "lint_issues": [],
        "llm_findings": [],
        "all_findings": [],
        "final_review": "",
        "owner": args.owner if args.owner else "",
        "repo": args.repo if args.repo else "",
        "pr_number": str(args.pr) if args.pr else ""
    }

    print("Invoking StateGraph pipeline...")
    result = graph.invoke(initial_state)
    print("\n=== PIPELINE RESULTS ===")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

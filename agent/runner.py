import os
from github.auth import get_github_token
from github.client import get_pr_diff, post_review_comment, set_commit_status
from agent.graph import graph
from db.session import SessionLocal
from db.models import Review

def review_pr(
    pr_id: int,
    repo: str,
    commit_sha: str,
    installation_id: int = None
):
    """
    Background worker that runs the PR review workflow:
    1. Sets commit status to pending.
    2. Fetches the PR diff.
    3. Runs the static analysis and LLM reasoning LangGraph pipeline.
    4. Posts findings back to GitHub as inline comments.
    5. Updates the commit status to success/failure.
    6. Logs the review results to the database.
    """
    if "/" not in repo:
        print(f"Invalid repository format: {repo}")
        return

    owner, repo_name = repo.split("/", 1)
    
    # 1. Get GitHub token and set status to pending
    try:
        token = get_github_token(installation_id)
        set_commit_status(
            owner=owner,
            repo_name=repo_name,
            sha=commit_sha,
            state="pending",
            description="PR Sentinel is reviewing code diffs...",
            token=token
        )
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    # 2. Fetch diff and run pipeline
    try:
        print(f"Fetching diff for {repo} PR #{pr_id}...")
        raw_diff = get_pr_diff(owner, repo_name, pr_id, token)
        
        initial_state = {
            "raw_diff": raw_diff,
            "parsed_files": [],
            "lint_issues": [],
            "llm_findings": [],
            "all_findings": [],
            "final_review": [],
            "owner": owner,
            "repo": repo_name,
            "pr_number": str(pr_id)
        }

        print("Invoking LangGraph PR review pipeline...")
        result = graph.invoke(initial_state)
        findings = result.get("final_review", [])
        
        # 3. Post comments to GitHub
        print(f"Review complete. Found {len(findings)} findings.")
        for finding in findings:
            file_path = finding.get("file")
            line_no = finding.get("line")
            severity = finding.get("severity", "medium").upper()
            comment = finding.get("comment")
            
            # Format comment with visual emojis
            severity_emoji = "⚠️" if severity == "LOW" else "🛑" if severity == "HIGH" else "💀" if severity == "CRITICAL" else "📝"
            comment_body = (
                f"### {severity_emoji} PR Sentinel Review\n"
                f"**Severity**: `{severity}`\n\n"
                f"{comment}"
            )
            
            print(f"Posting comment on {file_path}:{line_no}...")
            post_review_comment(
                owner=owner,
                repo_name=repo_name,
                pr_number=pr_id,
                commit_sha=commit_sha,
                path=file_path,
                line=line_no,
                body=comment_body,
                token=token
            )

        # 4. Save review results to database
        try:
            db = SessionLocal()
            verdict = "issues_found" if findings else "clean"
            review_record = Review(
                pr_id=pr_id,
                repo=repo,
                commit_sha=commit_sha,
                verdict=verdict,
                findings=findings,
                model_used="llama-3.3-70b-versatile"
            )
            db.add(review_record)
            db.commit()
            print("Successfully persisted review to the database.")
        except Exception as db_err:
            print(f"Failed to log review to database: {db_err}")
        finally:
            db.close()

        # 5. Set status to success
        status_desc = f"Review complete. {len(findings)} issues found." if findings else "Review complete. Code looks clean!"
        set_commit_status(
            owner=owner,
            repo_name=repo_name,
            sha=commit_sha,
            state="success",
            description=status_desc,
            token=token
        )
        print("Set GitHub commit status to SUCCESS.")

    except Exception as err:
        print(f"Error during PR review workflow: {err}")
        try:
            set_commit_status(
                owner=owner,
                repo_name=repo_name,
                sha=commit_sha,
                state="error",
                description=f"Review error: {str(err)[:100]}",
                token=token
            )
        except Exception as status_err:
            print(f"Failed to set commit status on error: {status_err}")

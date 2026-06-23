from typing import TypedDict

class ReviewState(TypedDict):
    raw_diff : str
    parsed_files:list
    lint_issues:list
    llm_findings:list
    all_findings:list
    final_review:str
    owner: str
    repo: str
    pr_number: str

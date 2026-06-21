from typing import TypedDict, List

class ReviewState(TypedDict):
    raw_diff : str
    parser_files:list
    lint_issues:list
    llm_findings:list
    final_review:str

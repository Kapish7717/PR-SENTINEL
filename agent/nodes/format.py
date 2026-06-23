from ..state import ReviewState
def format_review(state:ReviewState)->ReviewState:
    state['final_review'] = state['lint_issues'] + state['llm_findings']
    return state
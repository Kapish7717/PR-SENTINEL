from typing import TypedDict, List
from unidiff import PatchSet
from groq import Groq
import os
import re
import json
# from langgraph.graph import StateGraph, END






def static_analysis(state:ReviewState)->ReviewState:
    state['lint_issues'] = []
    return state    



def aggregate_findings(state:ReviewState)->ReviewState:
    state['final_review'] = state['lint_issues'] + state['llm_findings']
    return state

# graph = StateGraph(ReviewState)
# graph.add_node("ingest", ingest_diff)
# graph.add_node("lint", static_analysis)
# graph.add_node("reason", contextual_reasoning)
# graph.add_node("aggregate", aggregate_findings)

# graph.set_entry_point("ingest")
# graph.add_edge("ingest", "lint")
# graph.add_edge("lint", "reason")
# graph.add_edge("reason", "aggregate")
# graph.add_edge("aggregate", END)

# app = graph.compile()

import requests

if __name__ == "__main__":
    raw_diff = open("sample.patch").read()

    # resp = requests.get("https://github.com/psf/requests/pull/6169.diff")
    # with open("test_diffs/real_pr_1.patch", "w") as f:
    #     f.write(resp.text)
    # raw_diff = resp.text
    parsed_files = parse_with_unidiff(raw_diff)
    prompt = build_review_prompt(parsed_files)
    raw_response = call_llm(prompt)
    findings = parse_llm_response(raw_response)
    verified_findings = verify_findings(findings,parsed_files)
    json.dump(verified_findings, open("sample.json", "w"), indent=4)
    print(verified_findings)
# ruff: noqa: E402
import os
import json
import sys

# Add parent directory of 'agent' to python search path to support running directly from inside agent/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env manually before other imports to prevent KeyError on GROQ_API_KEY
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

from langgraph.graph import StateGraph, END
from agent.state import ReviewState
from agent.nodes.ingest import ingest_diff
from agent.nodes.lint import static_analysis
from agent.nodes.reasoning import contextual_reasoning
from agent.nodes.verify import verify_findings
from agent.nodes.format import format_review

def verify_node(state: ReviewState) -> ReviewState:
    state["llm_findings"] = verify_findings(state.get("llm_findings", []), state.get("parsed_files", []))
    return state

def build_graph():
    graph = StateGraph(ReviewState)

    # register all nodes
    graph.add_node("ingest",    ingest_diff)
    graph.add_node("lint",      static_analysis)
    graph.add_node("reason",    contextual_reasoning)
    graph.add_node("verify",    verify_node)
    graph.add_node("format",    format_review)

    # wire the edges
    graph.set_entry_point("ingest")
    graph.add_edge("ingest",  "lint")
    graph.add_edge("lint",    "reason")
    graph.add_edge("reason",  "verify")
    graph.add_edge("verify",  "format")
    graph.add_edge("format",  END)

    return graph.compile()

graph = build_graph()

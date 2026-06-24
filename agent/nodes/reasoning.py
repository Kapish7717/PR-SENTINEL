from groq import Groq
import os
import json
import re
from ..state import ReviewState
from ..prompts import build_review_prompt

# Initialize client lazily to prevent KeyError on module import when key is missing
_client = None

def get_groq_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        _client = Groq(api_key=api_key)
    return _client

def call_llm(prompt:str)->str:
    client = get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content

def parse_llm_response(raw_response:str)->list:
    cleaned = raw_response.strip()

    cleaned = re.sub(r"^```json\s*|\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    try:
        findings = json.loads(cleaned)
        if not isinstance(findings, list):
            return []
        return findings
    except json.JSONDecodeError:
        # model returned something unparseable — don't crash the whole pipeline,
        # just log it and treat this PR as "no findings" for now
        print(f"Failed to parse LLM response: {cleaned[:200]}")
        return []


def contextual_reasoning(state:ReviewState)->ReviewState:
    state['llm_findings'] = []
    prompt = build_review_prompt(state['parsed_files'])
    response = call_llm(prompt)
    state['llm_findings'] = parse_llm_response(response)
    return state
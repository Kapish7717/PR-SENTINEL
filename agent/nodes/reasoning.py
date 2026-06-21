from groq import Groq
import os
import json
import re
from ..state import ReviewState
from ..prompts import build_review_prompt

client = Groq(api_key=os.environ['GROQ_API_KEY'])

def call_llm(prompt:str)->str:
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
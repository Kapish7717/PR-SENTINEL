
def build_review_prompt(parsed_files:list)->str:
    diff_text=""
    for f in parsed_files:
        diff_text += f"\n### File: {f['filename']}\n"
        for line_no, content in f["added_lines"]:
            diff_text += f"+{line_no}: {content}"

    prompt = f"""You are a senior software engineer reviewing a pull request.
Below are the lines ADDED in this PR (lines removed are not shown).

{diff_text}

Review this code for REAL issues only:
- Logic bugs (e.g. unhandled edge cases, off-by-one errors, wrong conditions)
- Security concerns (e.g. SQL injection, hardcoded secrets, unsafe input handling)
- Missed error handling (e.g. unguarded null/empty values, unhandled exceptions)

Do NOT comment on code style, formatting, or naming — a linter already handles that.
Special case: for dependency/config files (setup.py, setup.cfg, requirements.txt,
pyproject.toml), only flag an issue if the change introduces a syntax error, an
impossible version constraint, or a known security vulnerability. Do NOT flag
version range changes as inherently risky.

CRITICAL: For every finding, you MUST include an "evidence" field containing the
EXACT line of code from above, copied character-for-character, that demonstrates
the problem. If you cannot find a real line that proves the issue, DO NOT report it.
It is better to report zero issues than to report something you cannot point to
exactly in the code shown above.

If you find nothing wrong, return an empty list — this is a valid and common outcome.

Respond with ONLY a JSON array, no other text, no markdown formatting. Format:
[
  {{"file": "app.py", "line": 12, "severity": "high", "comment": "explanation here", "evidence": "exact code line here"}}
]
"""
    return prompt



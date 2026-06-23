import pytest
from unittest.mock import patch, MagicMock
from agent.nodes.lint import (
    run_linter,
    filter_to_changed_lines,
    lint_from_content,
    static_analysis
)

# ============================================================
# filter_to_changed_lines tests — no mocking needed, pure logic
# ============================================================

def test_filter_keeps_only_changed_lines(sample_lint_issues, sample_parsed_files):
    """Sirf wahi issues aane chahiye jo PR ki changed lines pe hain"""
    result = filter_to_changed_lines(sample_lint_issues, sample_parsed_files)
    
    returned_lines = [issue["line"] for issue in result]
    assert 1  in returned_lines   # line 1  changed thi  ✅
    assert 6  in returned_lines   # line 6  changed thi  ✅
    assert 50 not in returned_lines  # line 50 nahi change hui ❌
    assert 99 not in returned_lines  # line 99 nahi change hui ❌

def test_filter_returns_empty_when_no_overlap():
    """Agar koi bhi lint issue changed lines pe nahi, toh [] aana chahiye"""
    lint_issues = [
        {"file": "app.py", "line": 99, "severity": "low", "comment": "old issue"}
    ]
    parsed_files = [
        {"filename": "app.py", "added_lines": [(1, "x = 5\n")], "removed_lines": []}
    ]
    result = filter_to_changed_lines(lint_issues, parsed_files)
    assert result == []

def test_filter_handles_unknown_filename():
    """Agar ruff ne aisa filename diya jo parsed_files mein hai hi nahi"""
    lint_issues = [
        {"file": "some_random_file.py", "line": 1, "severity": "low", "comment": "..."}
    ]
    parsed_files = [
        {"filename": "app.py", "added_lines": [(1, "x=5\n")], "removed_lines": []}
    ]
    # crash nahi hona chahiye, bas [] return ho
    result = filter_to_changed_lines(lint_issues, parsed_files)
    assert result == []

def test_filter_works_with_multiple_files():
    """Multi-file PR mein har file ke issues sahi se filter hone chahiye"""
    lint_issues = [
        {"file": "app.py",    "line": 5,  "severity": "medium", "comment": "issue in app"},
        {"file": "utils.py",  "line": 10, "severity": "low",    "comment": "issue in utils"},
        {"file": "app.py",    "line": 99, "severity": "low",    "comment": "old issue in app"},
    ]
    parsed_files = [
        {"filename": "app.py",   "added_lines": [(5, "x=1\n")],  "removed_lines": []},
        {"filename": "utils.py", "added_lines": [(10, "y=2\n")], "removed_lines": []},
    ]
    result = filter_to_changed_lines(lint_issues, parsed_files)
    assert len(result) == 2          # sirf 2 valid issues
    assert result[0]["file"] == "app.py"
    assert result[1]["file"] == "utils.py"

# ============================================================
# run_linter tests — ruff ko mock karo (real subprocess mat chalao)
# ============================================================

MOCK_RUFF_OUTPUT = [
    {
        "filename": "/tmp/tmpxyz123.py",
        "location": {"row": 1},
        "message": "`json` imported but unused",
        "severity": "error"
    }
]

@patch("agent.nodes.lint.subprocess.run")
def test_run_linter_basic(mock_run):
    """ruff ka output sahi se parse hona chahiye"""
    mock_run.return_value = MagicMock(
        stdout=str(MOCK_RUFF_OUTPUT).replace("'", '"'),
        returncode=1
    )
    # json-safe output chahiye, toh directly json string use karo
    import json
    mock_run.return_value.stdout = json.dumps(MOCK_RUFF_OUTPUT)

    result = run_linter("/tmp/tmpxyz123.py")
    assert len(result) == 1
    assert result[0]["line"] == 1
    assert result[0]["severity"] == "medium"    # "error" → "medium" mapping
    assert "unused" in result[0]["comment"]

@patch("agent.nodes.lint.subprocess.run")
def test_run_linter_original_filename_override(mock_run):
    """original_filename dene pe temp path override hona chahiye"""
    import json
    mock_run.return_value = MagicMock(stdout=json.dumps(MOCK_RUFF_OUTPUT))

    result = run_linter("/tmp/tmpxyz123.py", original_filename="app.py")
    assert result[0]["file"] == "app.py"   # temp path nahi, original naam aana chahiye

@patch("agent.nodes.lint.subprocess.run")
def test_run_linter_empty_output(mock_run):
    """Agar ruff koi issue nahi dhundhe, toh [] return hona chahiye"""
    mock_run.return_value = MagicMock(stdout="[]")
    result = run_linter("clean_file.py")
    assert result == []

@patch("agent.nodes.lint.subprocess.run")
def test_run_linter_invalid_json(mock_run):
    """Agar ruff ka output parse nahi hua, crash nahi hona chahiye"""
    mock_run.return_value = MagicMock(stdout="this is not json at all")
    result = run_linter("app.py")
    assert result == []   # fail safe

# ============================================================
# lint_from_content tests
# ============================================================

@patch("agent.nodes.lint.run_linter")
def test_lint_from_content_passes_original_filename(mock_run_linter):
    """lint_from_content ko original filename run_linter tak pohonchaana chahiye"""
    mock_run_linter.return_value = []
    lint_from_content("app.py", "import json\nx = 5\n")

    # confirm: run_linter call mein original_filename="app.py" gaya
    call_args = mock_run_linter.call_args
    assert call_args.kwargs["original_filename"] == "app.py"

@patch("agent.nodes.lint.run_linter")
@patch("agent.nodes.lint.os.unlink")
def test_lint_from_content_deletes_temp_file(mock_unlink, mock_run_linter):
    """Temp file hamesha delete honi chahiye — chahe run_linter crash kare ya na kare"""
    mock_run_linter.return_value = []
    lint_from_content("app.py", "x = 5\n")
    assert mock_unlink.called   # os.unlink zaroor call hua hona chahiye

@patch("agent.nodes.lint.run_linter")
@patch("agent.nodes.lint.os.unlink")
def test_lint_from_content_deletes_temp_file_even_on_crash(mock_unlink, mock_run_linter):
    """run_linter crash kare tab bhi temp file delete honi chahiye (finally block test)"""
    mock_run_linter.side_effect = Exception("ruff crashed")
    
    with pytest.raises(Exception):
        lint_from_content("app.py", "x = 5\n")
    
    assert mock_unlink.called   # finally block kaam kiya ✅
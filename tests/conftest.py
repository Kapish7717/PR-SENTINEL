import pytest

@pytest.fixture
def sample_lint_issues():
    return [
        {"file": "app.py", "line": 1, "severity": "medium", "comment": "unused import"},
        {"file": "app.py", "line": 6, "severity": "low", "comment": "too many blank lines"},
        {"file": "app.py", "line": 50, "severity": "medium", "comment": "undefined name"},
        {"file": "app.py", "line": 99, "severity": "low", "comment": "line too long"},
    ]

@pytest.fixture
def sample_parsed_files():
    return [
        {
            "filename": "app.py",
            "added_lines": [
                (1, "import os\n"),
                (6, "x = 5\n"),
            ],
            "removed_lines": []
        }
    ]

# tests/test_validators.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from validators import validate_finding, validate_findings

SAMPLE_CODE = "\n".join([f"line {i}" for i in range(1, 51)])  # 50-line fake file

def test_valid_finding():
    finding = {
        "file_path": "auth.py",
        "start_line": 5,
        "end_line": 10,
        "issue_type": "security",
        "severity": "High",
        "confidence": 0.9,
        "description": "SQL injection vulnerability via string concatenation causes security exposure.",
        "remediation": "Use parameterized queries.",
        "code_suggestion": "",
        "tags": ["sql-injection"],
        "references": []
    }
    assert validate_finding(finding, SAMPLE_CODE) == True
    print("✅ test_valid_finding passed")

def test_out_of_bounds():
    finding = {
        "file_path": "auth.py",
        "start_line": 999,   # out of bounds
        "end_line": 1000,
        "issue_type": "bug",
        "severity": "High",
        "confidence": 0.9,
        "description": "Some error causes exception failure.",
        "remediation": "Fix it.",
        "code_suggestion": "",
        "tags": [],
        "references": []
    }
    assert validate_finding(finding, SAMPLE_CODE) == False
    print("✅ test_out_of_bounds passed")

def test_unjustified_severity():
    finding = {
        "file_path": "utils.py",
        "start_line": 1,
        "end_line": 2,
        "issue_type": "style",
        "severity": "Critical",   # Critical but description doesn't justify it
        "confidence": 0.5,
        "description": "Missing docstring on function.",
        "remediation": "Add a docstring.",
        "code_suggestion": "",
        "tags": [],
        "references": []
    }
    assert validate_finding(finding, SAMPLE_CODE) == False
    print("✅ test_unjustified_severity passed")

def test_empty_remediation():
    finding = {
        "file_path": "app.py",
        "start_line": 3,
        "end_line": 5,
        "issue_type": "bug",
        "severity": "Medium",
        "confidence": 0.8,
        "description": "Incorrect loop bound causes incorrect output under certain inputs.",
        "remediation": "",   # empty
        "code_suggestion": "",
        "tags": [],
        "references": []
    }
    assert validate_finding(finding, SAMPLE_CODE) == False
    print("✅ test_empty_remediation passed")

def test_invalid_issue_type():
    finding = {
        "file_path": "app.py",
        "start_line": 1,
        "end_line": 2,
        "issue_type": "unknown_type",   # invalid
        "severity": "Low",
        "confidence": 0.7,
        "description": "Some minor naming issue.",
        "remediation": "Rename it.",
        "code_suggestion": "",
        "tags": [],
        "references": []
    }
    assert validate_finding(finding, SAMPLE_CODE) == False
    print("✅ test_invalid_issue_type passed")

if __name__ == "__main__":
    test_valid_finding()
    test_out_of_bounds()
    test_unjustified_severity()
    test_empty_remediation()
    test_invalid_issue_type()
    print("\n✅ All validator tests passed!")

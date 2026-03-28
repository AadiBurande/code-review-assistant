# tests/test_integration.py
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from loader import CodeDocumentLoader, detect_language
from analyzers import run_static_analysis, findings_to_dict
from aggregator import deduplicate, _score_findings, _verdict, build_report
from langgraph_pipeline import run_pipeline

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_inputs")
BUGGY_PY   = os.path.join(SAMPLE_DIR, "buggy_python.py")
VULN_JAVA  = os.path.join(SAMPLE_DIR, "vulnerable_java.java")
LEAKY_JS   = os.path.join(SAMPLE_DIR, "leaky_js.js")


# ── Loader Tests ──────────────────────────────────────────────────────────────

def test_loader_detects_python():
    assert detect_language("app.py") == "python"

def test_loader_detects_java():
    assert detect_language("Main.java") == "java"

def test_loader_detects_javascript():
    assert detect_language("index.js") == "javascript"

def test_loader_chunks_python_file():
    loader = CodeDocumentLoader(BUGGY_PY)
    chunks = loader.load()
    assert len(chunks) >= 4, "Should produce at least 4 chunks (functions + module level)"
    for chunk in chunks:
        assert chunk.start_line >= 1
        assert chunk.end_line >= chunk.start_line
        assert chunk.language == "python"
        assert chunk.content.strip() != ""

def test_loader_preserves_line_numbers():
    loader = CodeDocumentLoader(BUGGY_PY)
    chunks = loader.load()
    names = [c.ast_node_name for c in chunks]
    assert "get_user" in names
    assert "calculate_average" in names
    assert "find_duplicates" in names


# ── Static Analyzer Tests ─────────────────────────────────────────────────────

def test_static_analysis_python_finds_sql_injection():
    findings = asyncio.run(run_static_analysis(BUGGY_PY, "python"))
    dicts = findings_to_dict(findings)
    rules = [f["rule_id"] for f in dicts]
    assert "B608" in rules, "bandit should detect SQL injection (B608)"

def test_static_analysis_python_finds_hardcoded_password():
    findings = asyncio.run(run_static_analysis(BUGGY_PY, "python"))
    dicts = findings_to_dict(findings)
    rules = [f["rule_id"] for f in dicts]
    assert "B105" in rules, "bandit should detect hardcoded password (B105)"

def test_static_analysis_returns_normalized_schema():
    findings = asyncio.run(run_static_analysis(BUGGY_PY, "python"))
    dicts = findings_to_dict(findings)
    assert len(dicts) > 0
    required_keys = {"file_path", "line", "severity", "rule_id", "tool", "description"}
    for f in dicts:
        assert required_keys.issubset(f.keys())


# ── Deduplication Tests ───────────────────────────────────────────────────────

def test_deduplication_removes_exact_duplicates():
    finding = {
        "file_path": "test.py", "start_line": 10, "end_line": 10,
        "issue_type": "security", "severity": "High", "confidence": 0.9,
        "description": "SQL injection vulnerability found here",
        "remediation": "Use parameterized queries",
        "code_suggestion": "", "tags": [], "references": []
    }
    duped = [finding, dict(finding), dict(finding)]
    result = deduplicate(duped)
    assert len(result) == 1

def test_deduplication_escalates_severity():
    base = {
        "file_path": "test.py", "start_line": 5, "end_line": 5,
        "issue_type": "security", "severity": "Medium", "confidence": 0.7,
        "description": "hardcoded password found in source code",
        "remediation": "Use env vars", "code_suggestion": "",
        "tags": [], "references": []
    }
    higher = dict(base)
    higher["severity"] = "Critical"
    result = deduplicate([base, higher])
    assert result[0]["severity"] == "Critical"

def test_deduplication_keeps_unique_findings():
    f1 = {
        "file_path": "a.py", "start_line": 1, "end_line": 1,
        "issue_type": "bug", "severity": "High", "confidence": 0.9,
        "description": "off by one error in loop index",
        "remediation": "", "code_suggestion": "", "tags": [], "references": []
    }
    f2 = {
        "file_path": "a.py", "start_line": 20, "end_line": 20,
        "issue_type": "security", "severity": "Critical", "confidence": 0.95,
        "description": "sql injection via string concatenation query",
        "remediation": "", "code_suggestion": "", "tags": [], "references": []
    }
    result = deduplicate([f1, f2])
    assert len(result) == 2


# ── Scoring Tests ─────────────────────────────────────────────────────────────

def test_score_perfect_code():
    score = _score_findings([])
    assert score == 100.0

def test_score_decreases_with_critical_findings():
    findings = [
        {"issue_type": "security", "severity": "Critical"},
        {"issue_type": "bug",      "severity": "High"},
    ]
    score = _score_findings(findings)
    assert score < 100.0

def test_verdict_accept():
    assert _verdict(80.0) == "Accept"

def test_verdict_needs_changes():
    assert _verdict(60.0) == "Needs Changes"

def test_verdict_reject():
    assert _verdict(30.0) == "Reject"


# ── Full Pipeline Integration Tests ──────────────────────────────────────────

def test_pipeline_detects_off_by_one():
    state = run_pipeline(BUGGY_PY, "test", "python", debug=False)
    descriptions = [f["description"].lower() for f in state["all_findings"]]
    found = any(
        kw in d for d in descriptions
        for kw in ("off-by-one", "off by one", "index", "range", "indexerror", "loop bound", "out of range")
    )
    assert found, "Pipeline should detect off-by-one error in calculate_average"

def test_pipeline_detects_sql_injection():
    state = run_pipeline(BUGGY_PY, "test", "python", debug=False)
    descriptions = [f["description"].lower() for f in state["all_findings"]]
    found = any(
        kw in d for d in descriptions
        for kw in ("sql", "injection", "query", "string-based", "concatenat")
    )
    assert found, "Pipeline should detect SQL injection in get_user"

def test_pipeline_detects_hardcoded_secret():
    state = run_pipeline(BUGGY_PY, "test", "python", debug=False)
    descriptions = [f["description"].lower() for f in state["all_findings"]]
    found = any(
        kw in d for d in descriptions
        for kw in ("password", "hardcoded", "secret", "credential", "supersecret")
    )
    assert found, "Pipeline should detect hardcoded password"

def test_pipeline_detects_resource_leak():
    state = run_pipeline(BUGGY_PY, "test", "python", debug=False)
    descriptions = [f["description"].lower() for f in state["all_findings"]]
    found = any(
        kw in d for d in descriptions
        for kw in ("open", "resource", "file", "closed", "leak", "with statement", "encoding")
    )
    assert found, "Pipeline should detect unclosed file resource"

def test_pipeline_detects_nested_loop_inefficiency():
    state = run_pipeline(BUGGY_PY, "test", "python", debug=False)
    descriptions = [f["description"].lower() for f in state["all_findings"]]
    found = any(
        kw in d for d in descriptions
        for kw in ("o(n", "nested", "duplicate", "quadratic", "inefficien", "loop", "enumerate", "range and len")
    )
    assert found, "Pipeline should detect O(n²) nested loop inefficiency"

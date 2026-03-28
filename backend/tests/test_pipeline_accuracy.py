# tests/test_pipeline_accuracy.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langgraph_pipeline import run_pipeline
from aggregator import build_report

def test_buggy_python2_is_rejected():
    """
    buggy_python2.py must score below 85 and NOT be accepted.
    Previously scored 75.5 → accept (WRONG). Should be reject or needs_changes.
    """
    state = run_pipeline(
        source_path="tests/sample_inputs/buggy_python2.py",
        project_name="accuracy_test",
        language="python",
        project_context="Accuracy regression test — must not accept buggy code.",
        debug=False,
    )

    report = build_report(state, language="python")
    score   = report.metadata.score
    verdict = report.metadata.verdict

    print(f"\n{'='*50}")
    print(f"  Score  : {score}/100")
    print(f"  Verdict: {verdict}")
    print(f"  Findings: {report.metadata.total_findings}")
    print(f"  Sub-scores: {report.metadata.sub_scores}")
    print(f"{'='*50}")

    # ── Assertions ──────────────────────────────────────────────────────
    assert score < 85, \
        f"FAIL: Score {score} too high — buggy code should not pass 85"
    
    assert verdict in ("needs_changes", "reject"), \
        f"FAIL: Verdict '{verdict}' is wrong — should be needs_changes or reject"

    assert report.metadata.total_findings >= 5, \
        f"FAIL: Only {report.metadata.total_findings} findings — agents may be under-reporting"

    security_score = report.metadata.sub_scores.get("security", 100)
    assert security_score < 80, \
        f"FAIL: Security score {security_score} too high for code with MD5 + shell injection"

    print("\n✅ test_buggy_python2_is_rejected PASSED")

if __name__ == "__main__":
    test_buggy_python2_is_rejected()

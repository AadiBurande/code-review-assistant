# tests/test_pdf_generation.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pathlib import Path
from langgraph_pipeline import run_pipeline
from aggregator import build_report
from pdf_generator import generate_pdf_report

def test_pdf_generated():
    state = run_pipeline(
        source_path="tests/sample_inputs/buggy_python2.py",
        project_name="pdf_test",
        language="python",
        debug=False,
    )
    report   = build_report(state, language="python")
    pdf_path = "reports/test_pdf_output.pdf"
    result   = generate_pdf_report(report, pdf_path)

    assert Path(pdf_path).exists(), "FAIL: PDF file was not created"
    assert Path(pdf_path).stat().st_size > 5000, "FAIL: PDF is suspiciously small (likely empty)"
    print(f"✅ PDF generated successfully → {pdf_path} ({Path(pdf_path).stat().st_size} bytes)")

if __name__ == "__main__":
    test_pdf_generated()

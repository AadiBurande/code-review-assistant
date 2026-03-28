# tests/test_context_builder.py
# tests/test_context_builder.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from context_builder import build_context, extract_imports, extract_function_signatures, extract_external_calls

SAMPLE_CODE = """
import os
import hashlib
from pathlib import Path
import requests

async def fetch_data(url: str):
    pass

def _private_helper(x):
    return x * 2

class DataProcessor:
    def process(self, data):
        result = requests.get(url)
        return hashlib.md5(data).hexdigest()
"""

def test_imports():
    imports = extract_imports(SAMPLE_CODE)
    assert "os" in imports["stdlib"]
    assert "hashlib" in imports["stdlib"]
    assert "requests" in imports["third_party"]
    print("✅ test_imports passed")

def test_signatures():
    sigs = extract_function_signatures(SAMPLE_CODE)
    sig_names = " ".join(sigs)
    assert "fetch_data" in sig_names       # async def
    assert "_private_helper" in sig_names  # private
    assert "DataProcessor" in sig_names    # class
    print("✅ test_signatures passed")

def test_external_calls():
    calls = extract_external_calls(SAMPLE_CODE)
    assert any("requests" in c for c in calls)
    assert any("hashlib" in c for c in calls)
    print("✅ test_external_calls passed")

def test_build_context():
    ctx = build_context(SAMPLE_CODE, "test_file.py")
    assert "hashlib" in ctx
    assert "requests" in ctx
    assert "fetch_data" in ctx
    print("✅ test_build_context passed")
    print("\n--- Context Output ---")
    print(ctx)

if __name__ == "__main__":
    test_imports()
    test_signatures()
    test_external_calls()
    test_build_context()
    print("\n✅ All context_builder tests passed!")

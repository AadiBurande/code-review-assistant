# validators.py
import re
from typing import List, Dict

# ── False positive description fragments ──────────────────────────────────────

FALSE_POSITIVE_DESC_FRAGMENTS = [
    "example code",
    "test fixture",
    "mock object",
    "placeholder",
    "dummy value",
]

# ── Severity keyword justification map ───────────────────────────────────────

SEVERITY_KEYWORD_MAP = {
    "Critical": [
        "crash", "data loss", "corruption", "injection", "rce", "arbitrary",
        "exfiltration", "bypass", "execution", "exploit", "remote", "takeover",
    ],
    "High": [
        "error", "exception", "failure", "security", "exposure", "vulnerable",
        "unauthorized", "overflow", "race", "injection", "dereference",
        "secret", "password", "hardcoded", "token", "key", "credential",
        "leak", "disclosure", "sensitive", "plaintext", "unencrypted",
        "weak", "insecure", "missing", "unsafe", "traversal", "path",
        "detected", "hash", "recursion", "infinite", "resource",
        "sql", "command", "deserialization", "pickle", "eval", "exec",
        "mutable", "default", "argument", "shared state",
        "n+1", "query", "database", "round-trip",
        "never closed", "file handle", "connection",
    ],
}

# ── Minimum confidence per issue type ────────────────────────────────────────

MIN_CONFIDENCE = {
    "bug":         0.75,
    "security":    0.80,
    "performance": 0.75,
    "style":       0.70,
}

# ── Safe SQL patterns — parameterized queries ─────────────────────────────────

SAFE_SQL_PATTERNS = ["?", ":param", "%s", "%(", "placeholders", "in_("]

# ── Tags that belong only to style/bug — never valid as security findings ─────

STYLE_ONLY_TAGS = {
    "line-length", "line_length",
    "operator-spacing", "whitespace",
    "e501", "trailing-whitespace",
    "unused-parameter", "unused-argument",
    "unnecessary-parens", "pylint/c0325", "c0325",
    "sql-injection",  
}

# ── Helper: line existence check ─────────────────────────────────────────────

def _line_exists(start_line: int, end_line: int, total_lines: int) -> bool:
    # Allow +2 line tolerance for edge cases
    return 1 <= start_line <= total_lines and start_line <= end_line <= total_lines + 2


# ── Helper: severity keyword justification ───────────────────────────────────

def _severity_justified(finding: Dict) -> bool:
    severity    = finding.get("severity",    "Info")
    description = finding.get("description", "").lower()
    if severity not in SEVERITY_KEYWORD_MAP:
        return True
    return any(kw in description for kw in SEVERITY_KEYWORD_MAP[severity])


# ── Helper: SQL injection false positive detector ─────────────────────────────

def _is_sql_false_positive(finding: Dict, code: str) -> bool:
    """
    Detects SQL injection false positives on parameterized queries.
    Checks a ±3 line window around the flagged line — catches cases like
    `placeholders = "?, ?, ?"` defined one line above the flagged f-string.
    """
    issue_type  = finding.get("issue_type",  "")
    description = finding.get("description", "").lower()
    start_line  = finding.get("start_line",  0)

    if "sql" not in description:
        return False

    try:
        lines        = code.split("\n")
        window_start = max(0, start_line - 4)
        window_end   = min(len(lines), start_line + 2)
        window       = "\n".join(lines[window_start:window_end]).lower()
    except Exception:
        return False

    has_safe_pattern  = any(p in window for p in SAFE_SQL_PATTERNS)
    # Direct string concatenation with user input — e.g. "SELECT..." + user_input
    has_string_concat = re.search(r'["\'].*\+.*["\']', window) is not None

    if has_safe_pattern and not has_string_concat:
        return True
    return False


# ── Main validator ────────────────────────────────────────────────────────────

def validate_finding(finding: Dict, code: str) -> bool:
    if not isinstance(finding, dict):
        print(f"  [Validator] ✗ Finding is not a dict: {type(finding)}")
        return False

    total_lines = len(code.split("\n"))

    start_line  = finding.get("start_line",  0)
    end_line    = finding.get("end_line",    0)
    description = finding.get("description", "").lower()
    severity    = finding.get("severity",    "Info")
    issue_type  = finding.get("issue_type",  "")
    remediation = finding.get("remediation", "")
    confidence  = finding.get("confidence",  0)

    # ── Rule 1: line numbers must be integers ─────────────────────────────────
    if not isinstance(start_line, int) or not isinstance(end_line, int):
        print(f"  [Validator] ✗ Non-integer line numbers: {start_line}, {end_line}")
        return False

    # ── Rule 2: line bounds must exist in file ────────────────────────────────
    if not _line_exists(start_line, end_line, total_lines):
        print(f"  [Validator] ✗ Out-of-bounds line {start_line}-{end_line} "
              f"(file has {total_lines} lines)")
        return False

    # ── Rule 3: filter known false positive description fragments ─────────────
    if any(fp in description for fp in FALSE_POSITIVE_DESC_FRAGMENTS):
        print(f"  [Validator] ✗ False positive pattern: {description[:60]}")
        return False

    # ── Rule 4: SQL injection false positive on parameterized queries ─────────
    if _is_sql_false_positive(finding, code):
        print(f"  [Validator] ✗ SQL false positive — parameterized query at line {start_line}")
        return False

    # ── Rule 5: severity must be justified by description keywords ────────────
    if not _severity_justified(finding):
        print(f"  [Validator] ✗ {severity} not justified by: {description[:60]}")
        return False

    # ── Rule 6: non-empty description and remediation ─────────────────────────
    if not str(description).strip():
        print("  [Validator] ✗ Empty description")
        return False

    if not str(remediation).strip():
        print("  [Validator] ✗ Empty remediation")
        return False

    # ── Rule 7: valid issue_type ──────────────────────────────────────────────
    if issue_type not in {"bug", "security", "performance", "style"}:
        print(f"  [Validator] ✗ Invalid issue_type: '{issue_type}'")
        return False

    # ── Rule 8: minimum confidence threshold ──────────────────────────────────
    threshold = MIN_CONFIDENCE.get(issue_type, 0.70)
    if isinstance(confidence, (int, float)) and confidence < threshold:
        print(f"  [Validator] ✗ Confidence {confidence:.2f} below threshold "
              f"{threshold} for {issue_type}")
        return False

    # ── Rule 9: block style-only tags reported as security findings ───────────
    finding_tags = {t.lower() for t in finding.get("tags", [])}
    if issue_type == "security" and finding_tags & STYLE_ONLY_TAGS:
        print(f"  [Validator] ✗ Style-only tags in security finding: {finding_tags & STYLE_ONLY_TAGS}")
        return False

    return True


# ── Batch validator ───────────────────────────────────────────────────────────

def validate_findings(findings: List[Dict], code: str) -> List[Dict]:
    """Filter findings through all validation rules. Never raises — always returns a list."""
    if not isinstance(findings, list):
        print(f"  [Validator] ✗ findings is not a list: {type(findings)}")
        return []

    validated = []
    for f in findings:
        try:
            if validate_finding(f, code):
                validated.append(f)
        except Exception as e:
            print(f"  [Validator] ✗ Unexpected error validating finding: {e}")
            continue

    print(f"  [Validator] {len(findings)} → {len(validated)} valid finding(s)")
    return validated
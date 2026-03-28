# analyzers.py
import subprocess
import json
import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed


# ── Normalized Finding Schema ───────────────────────────────────────────────────

@dataclass
class StaticFinding:
    file_path: str
    line: int
    end_line: int
    severity: str
    rule_id: str
    tool: str
    description: str
    category: str


# ── Severity Normalizer ─────────────────────────────────────────────────────────

def normalize_severity(raw: str) -> str:
    raw = raw.upper().strip()
    if raw in ("ERROR", "CRITICAL", "HIGH", "C"):
        return "High"
    elif raw in ("WARNING", "MEDIUM", "W"):
        return "Medium"
    elif raw in ("INFO", "LOW", "REFACTOR", "CONVENTION", "R", "I"):
        return "Low"
    return "Info"


# ── Python: pylint ──────────────────────────────────────────────────────────────

def run_pylint(file_path: str) -> List[StaticFinding]:
    findings = []
    try:
        result = subprocess.run(
            ["pylint", file_path, "--output-format=json", "--disable=C0114,C0115,C0116"],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout) if result.stdout.strip() else []
        for item in data:
            findings.append(StaticFinding(
                file_path=file_path,
                line=item.get("line", 0),
                end_line=item.get("endLine") or item.get("line", 0),
                severity=normalize_severity(item.get("type", "info")),
                rule_id=item.get("message-id", "PYLINT"),
                tool="pylint",
                description=item.get("message", ""),
                category="bug" if item.get("type") in ("error", "fatal") else "style",
            ))
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[pylint] Skipped: {e}")
    return findings


# ── Python: flake8 ──────────────────────────────────────────────────────────────

def run_flake8(file_path: str) -> List[StaticFinding]:
    findings = []
    try:
        result = subprocess.run(
            ["flake8", file_path, "--format=%(path)s::%(row)d::%(col)d::%(code)s::%(text)s"],
            capture_output=True, text=True, timeout=60
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split("::")
            if len(parts) == 5:
                _, row, _, code, text = parts
                findings.append(StaticFinding(
                    file_path=file_path,
                    line=int(row),
                    end_line=int(row),
                    severity="Low",
                    rule_id=code.strip(),
                    tool="flake8",
                    description=text.strip(),
                    category="style",
                ))
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[flake8] Skipped: {e}")
    return findings


# ── Python: bandit ──────────────────────────────────────────────────────────────

def run_bandit(file_path: str) -> List[StaticFinding]:
    findings = []
    try:
        result = subprocess.run(
            ["bandit", "-f", "json", "-q", file_path],
            capture_output=True, text=True, timeout=60
        )
        raw = result.stdout.strip()
        if not raw:
            return findings
        data = json.loads(raw)
        for item in data.get("results", []):
            findings.append(StaticFinding(
                file_path=file_path,
                line=item.get("line_number", 0),
                end_line=item.get("line_number", 0),
                severity=normalize_severity(item.get("issue_severity", "low")),
                rule_id=item.get("test_id", "BANDIT"),
                tool="bandit",
                description=item.get("issue_text", ""),
                category="security",
            ))
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[bandit] Skipped: {e}")
    return findings


# ── Python: radon ───────────────────────────────────────────────────────────────

def run_radon(file_path: str) -> List[StaticFinding]:
    findings = []
    try:
        result = subprocess.run(
            ["radon", "cc", file_path, "-s", "-j"],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        for fname, blocks in data.items():
            for block in blocks:
                complexity = block.get("complexity", 0)
                if complexity >= 10:
                    findings.append(StaticFinding(
                        file_path=file_path,
                        line=block.get("lineno", 0),
                        end_line=block.get("endline", 0),
                        severity="Medium" if complexity < 15 else "High",
                        rule_id="RADON_CC",
                        tool="radon",
                        description=f"Cyclomatic complexity {complexity} in '{block.get('name', '')}' (threshold: 10)",
                        category="performance",
                    ))
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[radon] Skipped: {e}")
    return findings


# ── JavaScript: custom pattern scanner ─────────────────────────────────────────

def run_js_pattern_scan(file_path: str) -> List[StaticFinding]:
    findings = []
    patterns = [
        (r'eval\s*\(', "High", "security", "JS_EVAL", "Use of eval() — arbitrary code execution risk"),
        (r'innerHTML\s*=', "High", "security", "JS_INNERHTML", "Direct innerHTML assignment — XSS vulnerability"),
        (r'outerHTML\s*=', "High", "security", "JS_OUTERHTML", "Direct outerHTML assignment — XSS vulnerability"),
        (r'document\.write\s*\(', "High", "security", "JS_DOCWRITE", "document.write() usage — XSS risk"),
        (r'setTimeout\s*\(\s*["\']', "Medium", "security", "JS_SETTIMEOUT_STR", "setTimeout with string argument — eval equivalent"),
        (r'setInterval\s*\(\s*["\']', "Medium", "security", "JS_SETINTERVAL_STR", "setInterval with string argument — eval equivalent"),
        (r'child_process', "High", "security", "JS_CHILD_PROCESS", "child_process usage — command injection risk"),
        (r'\.exec\s*\(', "High", "security", "JS_EXEC", "exec() usage — command injection risk"),
        (r'password\s*=\s*["\'][^"\']+["\']', "High", "security", "JS_HARDCODED_PASS", "Hardcoded password detected"),
        (r'(secret|api_key|apikey|token)\s*=\s*["\'][^"\']{8,}["\']', "High", "security", "JS_HARDCODED_SECRET", "Hardcoded secret/API key detected"),
        (r'Math\.random\(\)', "Medium", "security", "JS_WEAK_RANDOM", "Math.random() is not cryptographically secure"),
        (r'http://', "Medium", "security", "JS_HTTP", "Insecure HTTP connection — use HTTPS"),
        (r'verify\s*:\s*false', "High", "security", "JS_TLS_VERIFY_OFF", "TLS verification disabled — MITM attack risk"),
        (r'allowUnauthorized\s*:\s*true', "High", "security", "JS_UNAUTH_TLS", "Unauthorized TLS connections allowed"),
        (r'req\.(body|query|params)\.\w+.*(\+|`)', "High", "security", "JS_USER_INPUT_CONCAT", "User input concatenated directly — injection risk"),
        (r'==\s', "Low", "bug", "JS_LOOSE_EQ", "Loose equality (==) — use === instead"),
        (r'var\s+', "Low", "style", "JS_VAR", "Use of var — prefer const or let"),
        (r'console\.(log|warn|error)\s*\(', "Low", "style", "JS_CONSOLE", "console statement left in code"),
        (r'TODO|FIXME|HACK|XXX', "Low", "style", "JS_TODO", "TODO/FIXME comment found"),
        (r'\.catch\s*\(\s*\)', "Medium", "bug", "JS_EMPTY_CATCH", "Empty catch block — errors silently swallowed"),
        (r'require\s*\(\s*req\.(body|query|params)', "High", "security", "JS_DYNAMIC_REQUIRE", "Dynamic require with user input — code injection risk"),
        (r'new\s+Function\s*\(', "High", "security", "JS_NEW_FUNCTION", "new Function() — eval equivalent, code injection risk"),
        (r'__dirname\s*\+.*req\.', "High", "security", "JS_PATH_TRAVERSAL", "Path built with user input — path traversal risk"),
        (r'res\.send\s*\(.*req\.(body|query|params)', "High", "security", "JS_REFLECTED_XSS", "User input reflected in response — XSS risk"),
        (r'cors\s*\(\s*\{[^}]*origin\s*:\s*["\*]', "Medium", "security", "JS_CORS_WILDCARD", "CORS wildcard origin — allows any domain"),
        (r'helmet', "Low", "security", "JS_NO_HELMET", "Ensure helmet.js is configured for security headers"),
        (r'process\.env\.\w+\s*\|\|\s*["\'][^"\']+["\']', "Medium", "security", "JS_ENV_FALLBACK", "Hardcoded fallback for env variable — use proper secrets management"),
    ]

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for line_num, line_content in enumerate(lines, start=1):
            for pattern, severity, category, rule_id, description in patterns:
                if re.search(pattern, line_content, re.IGNORECASE):
                    findings.append(StaticFinding(
                        file_path=file_path,
                        line=line_num,
                        end_line=line_num,
                        severity=severity,
                        rule_id=rule_id,
                        tool="js_pattern_scan",
                        description=description,
                        category=category,
                    ))
    except Exception as e:
        print(f"[js_pattern_scan] Skipped: {e}")
    return findings


# ── Java: custom pattern scanner ───────────────────────────────────────────────

def run_java_pattern_scan(file_path: str) -> List[StaticFinding]:
    findings = []
    patterns = [
        (r'Statement\s+\w+\s*=.*createStatement', "High", "security", "JAVA_RAW_STMT", "Raw SQL Statement — use PreparedStatement to prevent SQL injection"),
        (r'".*\+\s*\w+.*"', "High", "security", "JAVA_SQL_CONCAT", "String concatenation in query — SQL injection risk"),
        (r'Runtime\.getRuntime\(\)\.exec\s*\(', "High", "security", "JAVA_CMD_EXEC", "Runtime.exec() — command injection risk"),
        (r'ProcessBuilder', "Medium", "security", "JAVA_PROCESS_BUILDER", "ProcessBuilder usage — verify inputs to prevent command injection"),
        (r'MessageDigest\.getInstance\s*\(\s*"MD5"', "High", "security", "JAVA_MD5", "MD5 is cryptographically broken — use SHA-256 or better"),
        (r'MessageDigest\.getInstance\s*\(\s*"SHA-1"', "Medium", "security", "JAVA_SHA1", "SHA-1 is weak — use SHA-256 or better"),
        (r'password\s*=\s*"[^"]+"', "High", "security", "JAVA_HARDCODED_PASS", "Hardcoded password detected"),
        (r'(secret|apikey|api_key|token)\s*=\s*"[^"]+"', "High", "security", "JAVA_HARDCODED_SECRET", "Hardcoded secret/API key detected"),
        (r'new\s+Random\s*\(\)', "Medium", "security", "JAVA_WEAK_RANDOM", "java.util.Random is not cryptographically secure — use SecureRandom"),
        (r'catch\s*\(\s*Exception\s+\w+\s*\)\s*\{?\s*\}', "Medium", "bug", "JAVA_EMPTY_CATCH", "Empty catch block — exception silently swallowed"),
        (r'e\.printStackTrace\(\)', "Medium", "bug", "JAVA_PRINT_STACK", "printStackTrace() exposes internal stack trace — use proper logging"),
        (r'\.toUpperCase\(\)|\.toLowerCase\(\)(?!\s*\(Locale)', "Low", "bug", "JAVA_LOCALE", "String case conversion without Locale — may cause bugs in non-English environments"),
        (r'==\s*null|null\s*==', "Medium", "bug", "JAVA_NULL_CHECK", "Null check with == — consider using Objects.isNull() or Optional"),
        (r'FileWriter|FileOutputStream', "Medium", "bug", "JAVA_RESOURCE_LEAK", "File resource may not be closed — use try-with-resources"),
        (r'System\.out\.print', "Low", "style", "JAVA_SYSOUT", "System.out.print — use a logger instead"),
        (r'TODO|FIXME|HACK|XXX', "Low", "style", "JAVA_TODO", "TODO/FIXME comment found"),
        (r'public\s+\w+\s+\w+\s*\([^)]{150,}\)', "Low", "style", "JAVA_LONG_PARAMS", "Method has too many parameters — consider refactoring"),
        (r'while\s*\(\s*true\s*\)', "Medium", "bug", "JAVA_INFINITE_LOOP", "Potential infinite loop — ensure proper exit condition"),
        (r'throws\s+Exception\b', "Low", "style", "JAVA_THROWS_EXCEPTION", "Method declares 'throws Exception' — use specific exception types"),
        (r'new\s+URL\s*\(\s*"http://', "Medium", "security", "JAVA_HTTP_URL", "Insecure HTTP URL — use HTTPS"),
        (r'new\s+Socket\s*\(\s*"[\d\.]+\"', "Medium", "security", "JAVA_HARDCODED_IP", "Hardcoded IP address — use configuration instead"),
        (r'rand\.nextInt\s*\(\s*\d+\s*\)', "Medium", "security", "JAVA_WEAK_OTP", "Weak OTP/token generation — use SecureRandom"),
        (r'Base64\.getDecoder|Base64\.getEncoder', "Low", "security", "JAVA_BASE64", "Base64 is encoding, not encryption — do not use for securing sensitive data"),
        (r'getBytes\(\)', "Low", "bug", "JAVA_GETBYTES_NO_CHARSET", "getBytes() without charset — behavior varies by platform, specify UTF-8"),
    ]

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for line_num, line_content in enumerate(lines, start=1):
            for pattern, severity, category, rule_id, description in patterns:
                if re.search(pattern, line_content, re.IGNORECASE):
                    findings.append(StaticFinding(
                        file_path=file_path,
                        line=line_num,
                        end_line=line_num,
                        severity=severity,
                        rule_id=rule_id,
                        tool="java_pattern_scan",
                        description=description,
                        category=category,
                    ))
    except Exception as e:
        print(f"[java_pattern_scan] Skipped: {e}")
    return findings


# ── Dispatcher ──────────────────────────────────────────────────────────────────

def run_static_analysis(file_path: str, language: str) -> List[StaticFinding]:
    tool_fns = []

    if language == "python":
        tool_fns = [run_pylint, run_flake8, run_bandit, run_radon]
    elif language == "javascript":
        tool_fns = [run_js_pattern_scan]
    elif language == "java":
        tool_fns = [run_java_pattern_scan]

    all_findings: List[StaticFinding] = []

    with ThreadPoolExecutor(max_workers=max(len(tool_fns), 1)) as executor:
        futures = {executor.submit(fn, file_path): fn.__name__ for fn in tool_fns}
        for future in as_completed(futures):
            try:
                all_findings.extend(future.result())
            except Exception as e:
                print(f"[StaticAnalysis] Tool error: {e}")

    severity_order = {"High": 0, "Medium": 1, "Low": 2, "Info": 3}
    all_findings.sort(key=lambda f: severity_order.get(f.severity, 4))
    return all_findings[:50]  # increased cap to 50


def findings_to_dict(findings: List[StaticFinding]) -> list:
    return [
        {
            "file_path": f.file_path,
            "line": f.line,
            "end_line": f.end_line,
            "severity": f.severity,
            "rule_id": f.rule_id,
            "tool": f.tool,
            "description": f.description,
            "category": f.category,
        }
        for f in findings
    ]


# ── Quick test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "tests/sample_inputs/buggy_python.py"
    language = sys.argv[2] if len(sys.argv) > 2 else "python"

    findings = run_static_analysis(path, language)
    print(f"\n[Static Analysis] {len(findings)} findings for {path}\n")
    for f in findings:
        print(f"  [{f.severity}] {f.tool} | Line {f.line} | {f.rule_id} → {f.description}")

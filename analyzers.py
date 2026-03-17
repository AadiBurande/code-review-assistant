# analyzers.py
import subprocess
import json
import os
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

# ── Normalized Finding Schema ─────────────────────────────────────────────────

@dataclass
class StaticFinding:
    file_path: str
    line: int
    end_line: int
    severity: str          # Critical / High / Medium / Low / Info
    rule_id: str
    tool: str
    description: str
    category: str          # bug / security / style / performance

# ── Severity Normalizer ───────────────────────────────────────────────────────

def normalize_severity(raw: str) -> str:
    raw = raw.upper().strip()
    if raw in ("ERROR", "CRITICAL", "HIGH", "C"):
        return "High"
    elif raw in ("WARNING", "MEDIUM", "W"):
        return "Medium"
    elif raw in ("INFO", "LOW", "REFACTOR", "CONVENTION", "R", "I"):
        return "Low"
    return "Info"

# ── Python: pylint ────────────────────────────────────────────────────────────

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
                category="bug" if item.get("type") in ("error","fatal") else "style",
            ))
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[pylint] Skipped: {e}")
    return findings

# ── Python: flake8 ────────────────────────────────────────────────────────────

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

# ── Python: bandit (security) ─────────────────────────────────────────────────

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

# ── Python: radon (complexity) ────────────────────────────────────────────────

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
                if complexity >= 10:  # only flag high complexity
                    findings.append(StaticFinding(
                        file_path=file_path,
                        line=block.get("lineno", 0),
                        end_line=block.get("endline", 0),
                        severity="Medium" if complexity < 15 else "High",
                        rule_id="RADON_CC",
                        tool="radon",
                        description=f"Cyclomatic complexity {complexity} in '{block.get('name','')}' (threshold: 10)",
                        category="performance",
                    ))
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[radon] Skipped: {e}")
    return findings

# ── JavaScript: eslint ────────────────────────────────────────────────────────

def run_eslint(file_path: str) -> List[StaticFinding]:
    findings = []
    try:
        result = subprocess.run(
            ["npx", "eslint", file_path, "--format=json", "--no-eslintrc",
             "--rule", '{"no-unused-vars":"warn","no-undef":"warn","eqeqeq":"error"}'],
            capture_output=True, text=True, timeout=60, shell=True
        )
        raw = result.stdout.strip()
        if not raw:
            return findings
        data = json.loads(raw)
        for file_result in data:
            for msg in file_result.get("messages", []):
                findings.append(StaticFinding(
                    file_path=file_path,
                    line=msg.get("line", 0),
                    end_line=msg.get("endLine") or msg.get("line", 0),
                    severity=normalize_severity("error" if msg.get("severity") == 2 else "warning"),
                    rule_id=msg.get("ruleId") or "ESLINT",
                    tool="eslint",
                    description=msg.get("message", ""),
                    category="style",
                ))
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[eslint] Skipped: {e}")
    return findings

# ── Semgrep (cross-language security) ────────────────────────────────────────

def run_semgrep(file_path: str) -> List[StaticFinding]:
    findings = []
    try:
        result = subprocess.run(
            ["semgrep", "--config=auto", file_path, "--json", "--quiet"],
            capture_output=True, text=True, timeout=120
        )
        raw = result.stdout.strip()
        if not raw:
            return findings
        data = json.loads(raw)
        for item in data.get("results", []):
            meta = item.get("extra", {})
            findings.append(StaticFinding(
                file_path=file_path,
                line=item.get("start", {}).get("line", 0),
                end_line=item.get("end", {}).get("line", 0),
                severity=normalize_severity(meta.get("severity", "info")),
                rule_id=item.get("check_id", "SEMGREP"),
                tool="semgrep",
                description=meta.get("message", ""),
                category="security",
            ))
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[semgrep] Skipped: {e}")
    return findings

# ── Dispatcher: run correct tools per language ────────────────────────────────

async def run_static_analysis(file_path: str, language: str) -> List[StaticFinding]:
    """
    Runs all applicable static tools for the given language in parallel.
    Returns top 20 normalized findings sorted by severity.
    """
    loop = asyncio.get_event_loop()
    tasks = []

    if language == "python":
        tasks = [
            loop.run_in_executor(None, run_pylint,  file_path),
            loop.run_in_executor(None, run_flake8,  file_path),
            loop.run_in_executor(None, run_bandit,  file_path),
            loop.run_in_executor(None, run_radon,   file_path),
            loop.run_in_executor(None, run_semgrep, file_path),
        ]
    elif language == "javascript":
        tasks = [
            loop.run_in_executor(None, run_eslint,  file_path),
            loop.run_in_executor(None, run_semgrep, file_path),
        ]
    elif language == "java":
        tasks = [
            loop.run_in_executor(None, run_semgrep, file_path),
        ]

    results = await asyncio.gather(*tasks)

    # Flatten all findings
    all_findings: List[StaticFinding] = []
    for result in results:
        all_findings.extend(result)

    # Sort by severity and return top 20
    severity_order = {"High": 0, "Medium": 1, "Low": 2, "Info": 3}
    all_findings.sort(key=lambda f: severity_order.get(f.severity, 4))
    return all_findings[:20]


def findings_to_dict(findings: List[StaticFinding]) -> list:
    """Convert findings to plain dicts for JSON serialization / prompt injection."""
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


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "tests/sample_inputs/buggy_python.py"
    language = sys.argv[2] if len(sys.argv) > 2 else "python"

    findings = asyncio.run(run_static_analysis(path, language))
    print(f"\n[Static Analysis] {len(findings)} findings for {path}\n")
    for f in findings:
        print(f"  [{f.severity}] {f.tool} | Line {f.line} | {f.rule_id} → {f.description}")

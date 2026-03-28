# aggregator.py
import hashlib
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ── Severity Ordering ─────────────────────────────────────────────────────────

SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
SEVERITY_SCORE = {"Critical": 0, "High": 20, "Medium": 50, "Low": 80, "Info": 100}

# ── Scoring Weights ───────────────────────────────────────────────────────────

WEIGHTS = {"bug": 0.40, "security": 0.30, "performance": 0.15, "style": 0.15}

# ── Penalty Map (tightened for production accuracy) ───────────────────────────

PENALTY = {"Critical": 30, "High": 20, "Medium": 10, "Low": 4, "Info": 1}

# ── Pydantic Report Models ────────────────────────────────────────────────────

class Remediation(BaseModel):
    text: str
    code_snippet: str = ""


class ReportFinding(BaseModel):
    id: str
    file_path: str
    start_line: int
    end_line: int
    issue_type: str
    severity: str
    confidence: float
    description: str
    remediation: Remediation
    references: List[str] = []
    tags: List[str] = []
    internal_reasoning: str = ""


class FileReport(BaseModel):
    file_path: str
    language: str
    score: float
    total_findings: int
    findings: List[ReportFinding]


class ReportMetadata(BaseModel):
    project_name: str
    analyzed_at: str
    total_files: int
    total_findings: int
    language_summary: Dict[str, int]
    score: float
    verdict: str          # accept / needs_changes / reject
    sub_scores: Dict[str, float] = {}   # ✅ per-category scores computed on deduped findings


class FullReport(BaseModel):
    metadata: ReportMetadata
    files: List[FileReport]


# ── Deduplication ─────────────────────────────────────────────────────────────

def _fingerprint(finding: Dict) -> str:
    sig = (
        finding.get("file_path", "") +
        str(finding.get("start_line", 0)) +
        str(finding.get("end_line", 0)) +
        finding.get("issue_type", "") +
        "".join(
            c for c in finding.get("description", "").lower()
            if c.isalnum() or c == " "
        )[:60]
    )
    return hashlib.md5(sig.encode()).hexdigest()


def deduplicate(findings: List[Dict]) -> List[Dict]:
    seen: Dict[str, Dict] = {}
    for f in findings:
        fp = _fingerprint(f)
        if fp not in seen:
            seen[fp] = dict(f)
            seen[fp]["_count"] = 1
        else:
            existing = seen[fp]
            existing["_count"] += 1
            if SEVERITY_ORDER.get(f["severity"], 4) < SEVERITY_ORDER.get(existing["severity"], 4):
                existing["severity"] = f["severity"]
            if f.get("confidence", 0) > existing.get("confidence", 0):
                existing["confidence"] = f["confidence"]
            existing["tags"]       = list(set(existing.get("tags", [])       + f.get("tags", [])))
            existing["references"] = list(set(existing.get("references", []) + f.get("references", [])))
    return list(seen.values())


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_findings(findings: List[Dict]) -> float:
    """
    Compute 0–100 quality score using tightened penalties.
    Critical → -30, High → -20, Medium → -10, Low → -4, Info → -1
    """
    category_scores = {cat: 100.0 for cat in WEIGHTS}

    for f in findings:
        cat = f.get("issue_type", "bug")
        if cat not in category_scores:
            cat = "bug"
        penalty = PENALTY.get(f.get("severity", "Info"), 1)
        category_scores[cat] = max(0.0, category_scores[cat] - penalty)

    final_score = sum(
        category_scores[cat] * weight
        for cat, weight in WEIGHTS.items()
    )
    return round(final_score, 1)


def _compute_sub_scores(findings: List[Dict]) -> Dict[str, float]:
    """Compute per-category sub-scores from deduplicated findings."""
    cat_scores = {cat: 100.0 for cat in WEIGHTS}
    for f in findings:
        cat = f.get("issue_type", "bug")
        if cat not in cat_scores:
            cat = "bug"
        cat_scores[cat] = max(0.0, cat_scores[cat] - PENALTY.get(f.get("severity", "Info"), 1))
    return {k: round(v, 1) for k, v in cat_scores.items()}


def _verdict(score: float) -> str:
    """
    Tightened thresholds for production-grade accuracy.
    Accept only genuinely clean code.
    """
    if score >= 85:
        return "accept"
    elif score >= 60:
        return "needs_changes"
    else:
        return "reject"


# ── Report Builder ────────────────────────────────────────────────────────────

def build_report(
    pipeline_state: Dict,
    language: str = "python",
) -> FullReport:
    raw_findings: List[Dict] = pipeline_state.get("all_findings", [])
    project_name: str        = pipeline_state.get("project_name", "unnamed_project")

    # Deduplicate
    deduped = deduplicate(raw_findings)
    print(f"[Aggregator] After deduplication: {len(deduped)} unique finding(s) "
          f"(removed {len(raw_findings) - len(deduped)} duplicates)")

    # Sort: severity ASC, then confidence DESC, then file path
    deduped.sort(key=lambda f: (
        SEVERITY_ORDER.get(f.get("severity", "Info"), 4),
        -f.get("confidence", 0),
        f.get("file_path", ""),
    ))

    # Group by file
    files_map: Dict[str, List[Dict]] = {}
    for f in deduped:
        fp = f.get("file_path", "unknown")
        files_map.setdefault(fp, []).append(f)

    # Build per-file reports
    file_reports = []
    language_summary: Dict[str, int] = {}

    for file_path, file_findings in files_map.items():
        file_score = _score_findings(file_findings)
        lang = language
        language_summary[lang] = language_summary.get(lang, 0) + len(file_findings)

        report_findings = []
        for f in file_findings:
            report_findings.append(ReportFinding(
                id=str(uuid.uuid4()),
                file_path=f.get("file_path", file_path),
                start_line=f.get("start_line", 0),
                end_line=f.get("end_line", 0),
                issue_type=f.get("issue_type", "bug"),
                severity=f.get("severity", "Info"),
                confidence=round(f.get("confidence", 0.5), 2),
                description=f.get("description", ""),
                remediation=Remediation(
                    text=f.get("remediation", ""),
                    code_snippet=f.get("code_suggestion", ""),
                ),
                references=f.get("references", []),
                tags=f.get("tags", []),
                internal_reasoning=f.get("internal_reasoning") or "",
            ))

        file_reports.append(FileReport(
            file_path=file_path,
            language=lang,
            score=file_score,
            total_findings=len(report_findings),
            findings=report_findings,
        ))

    # ── Compute scores from deduplicated findings (single source of truth) ──
    overall_score = _score_findings(deduped)
    sub_scores    = _compute_sub_scores(deduped)   # ✅ uses same deduped set
    verdict       = _verdict(overall_score)

    metadata = ReportMetadata(
        project_name=project_name,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
        total_files=len(file_reports),
        total_findings=len(deduped),
        language_summary=language_summary,
        score=overall_score,
        verdict=verdict,
        sub_scores=sub_scores,    # ✅ attached to metadata, used by main.py
    )

    return FullReport(metadata=metadata, files=file_reports)


# ── JSON Export ───────────────────────────────────────────────────────────────

def save_json_report(report: FullReport, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)
    print(f"[Report] JSON saved → {output_path}")
    return output_path


# ── Markdown Export ───────────────────────────────────────────────────────────

def save_markdown_report(report: FullReport, output_path: str) -> str:
    lines = []
    m = report.metadata

    lines.append(f"# Code Review Report — {m.project_name}")
    lines.append(f"\n**Analyzed at:** {m.analyzed_at}")
    lines.append(f"**Overall Score:** `{m.score}/100` — **{m.verdict.upper()}**")
    lines.append(f"**Total Findings:** {m.total_findings} across {m.total_files} file(s)\n")

    # Sub-scores table
    if m.sub_scores:
        lines.append("## Category Scores")
        lines.append("| Category | Score |")
        lines.append("|---|---|")
        for cat, score in m.sub_scores.items():
            lines.append(f"| {cat.capitalize()} | `{score}/100` |")
        lines.append("")

    # Score legend — updated thresholds
    lines.append("## Score Guide")
    lines.append("| Verdict | Score Range |")
    lines.append("|---|---|")
    lines.append("| ✅ Accept         | 85–100 |")
    lines.append("| ⚠️ Needs Changes  | 60–84  |")
    lines.append("| ❌ Reject         | 0–59   |\n")

    for file_report in report.files:
        lines.append(f"---\n## 📄 `{file_report.file_path}`")
        lines.append(f"**File Score:** `{file_report.score}/100` | "
                     f"**Findings:** {file_report.total_findings}\n")

        for sev in ["Critical", "High", "Medium", "Low", "Info"]:
            sev_findings = [f for f in file_report.findings if f.severity == sev]
            if not sev_findings:
                continue

            emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡",
                     "Low": "🔵", "Info": "⚪"}.get(sev, "⚪")
            lines.append(f"### {emoji} {sev} ({len(sev_findings)})")

            for f in sev_findings:
                lines.append(f"\n#### [{f.issue_type.upper()}] Line {f.start_line}–{f.end_line}")
                lines.append(f"**ID:** `{f.id}`")
                lines.append(f"**Confidence:** {int(f.confidence * 100)}%")
                lines.append(f"\n> {f.description}\n")
                lines.append(f"**Remediation:** {f.remediation.text}")
                if f.remediation.code_snippet:
                    lines.append(f"\n```{file_report.language}")
                    lines.append(f.remediation.code_snippet)
                    lines.append("```")
                if f.tags:
                    lines.append(f"\n**Tags:** {', '.join(f'`{t}`' for t in f.tags)}")
                if f.references:
                    lines.append(f"\n**References:** {', '.join(f.references)}")
                lines.append("")

    content = "\n".join(lines)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Report] Markdown saved → {output_path}")
    return output_path


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from langgraph_pipeline import run_pipeline

    state = run_pipeline(
        source_path="tests/sample_inputs/buggy_python.py",
        project_name="test_project",
        language="python",
        project_context="Sample buggy Python script for pipeline testing.",
        debug=False,
    )

    report = build_report(state, language="python")

    print(f"\n{'='*60}")
    print(f"  PROJECT SCORE  : {report.metadata.score}/100")
    print(f"  VERDICT        : {report.metadata.verdict}")
    print(f"  UNIQUE FINDINGS: {report.metadata.total_findings}")
    print(f"  SUB-SCORES     : {report.metadata.sub_scores}")
    print(f"{'='*60}")

    save_json_report(report,     "reports/test_project_report.json")
    save_markdown_report(report, "reports/test_project_report.md")

    print("\nTop findings:")
    for fr in report.files:
        for f in fr.findings[:5]:
            print(f"  [{f.severity}] {f.issue_type.upper()} | "
                  f"Line {f.start_line} | {f.description[:70]}")

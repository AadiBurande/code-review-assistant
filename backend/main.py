# main.py
import os
import uuid
import shutil
import threading
import json
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from langgraph_pipeline import run_pipeline
from aggregator import build_report, save_markdown_report
from pdf_generator import generate_pdf_report

# ── Directory constants — outside backend/ so --reload never triggers ─────────
BASE_DIR    = Path(__file__).resolve().parent.parent  # project root
TEMP_DIR    = BASE_DIR / "temp_uploads"
REPORTS_DIR = BASE_DIR / "reports"

# ── Suppress noisy /status polling logs ───────────────────────────────────────
class SuppressStatusLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/status/" not in record.getMessage()

logging.getLogger("uvicorn.access").addFilter(SuppressStatusLogs())

# ── In-memory job store ────────────────────────────────────────────────────────
jobs: dict = {}

# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    print("[Server] Shutting down gracefully.")

app = FastAPI(title="AI Code Review Assistant", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Flatten report → frontend shape ───────────────────────────────────────────

def flatten_report(report, session_id: str, filename: str, language: str) -> dict:
    """
    Convert FullReport → flat dict for frontend consumption.
    sub_scores come directly from aggregator metadata (computed on deduped findings).
    No re-computation here — single source of truth.
    """
    all_findings = []
    for file_report in report.files:
        for f in file_report.findings:
            all_findings.append({
                "file_path":       f.file_path,
                "start_line":      f.start_line,
                "end_line":        f.end_line,
                "issue_type":      f.issue_type,
                "severity":        f.severity,
                "confidence":      f.confidence,
                "description":     f.description,
                "remediation":     f.remediation.text,
                "code_suggestion": f.remediation.code_snippet,
                "tags":            f.tags,
                "references":      f.references,
            })

    return {
        "job_id":          session_id,
        "filename":        filename,
        "language":        language,
        "overall_score":   report.metadata.score,
        "sub_scores":      report.metadata.sub_scores,
        "verdict":         report.metadata.verdict,
        "total_findings":  report.metadata.total_findings,
        "findings":        all_findings,
        "static_findings": [],
    }

# ── Background worker ──────────────────────────────────────────────────────────

def run_analysis_job(
    session_id:      str,
    source_path:     str,
    filename:        str,
    project_name:    str,
    language:        str,
    project_context: str,
    debug:           bool,
):
    # ✅ on_stage defined BEFORE try block — always in scope
    def on_stage(stage: str, message: str, progress: int):
        jobs[session_id].update({
            "stage":    stage,
            "message":  message,
            "progress": progress,
            "status":   "running",
        })

    try:
        on_stage("ingestion", "Starting pipeline…", 2)

        state = run_pipeline(
            source_path=source_path,
            project_name=project_name,
            language=language,
            project_context=project_context,
            debug=debug,
            status_callback=on_stage,
        )

        on_stage("aggregation", "Building report…", 96)

        report = build_report(state, language=language)
        flat   = flatten_report(report, session_id, filename, language)

        # ── Save JSON ──────────────────────────────────────────────────────────
        json_path = REPORTS_DIR / f"{session_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(flat, f, indent=2)
        print(f"[Report] JSON saved → {json_path}")

        # ── Save Markdown ──────────────────────────────────────────────────────
        save_markdown_report(report, str(REPORTS_DIR / f"{session_id}.md"))

        # ── Save PDF ───────────────────────────────────────────────────────────
        pdf_path = str(REPORTS_DIR / f"{session_id}.pdf")
        generate_pdf_report(report, pdf_path)

        jobs[session_id].update({
            "status":   "complete",
            "stage":    "aggregation",
            "progress": 100,
            "message":  "Analysis complete",
            "result": {
                "session_id":      session_id,
                "score":           report.metadata.score,
                "verdict":         report.metadata.verdict,
                "total_findings":  report.metadata.total_findings,
                "report_json":     f"/report/{session_id}/json",
                "report_markdown": f"/report/{session_id}/markdown",
                "report_pdf":      f"/report/{session_id}/pdf",
            },
        })

    except Exception as e:
        jobs[session_id].update({
            "status":  "failed",
            "message": str(e),
            "error":   str(e),
        })
        print(f"[Job Error] {session_id}: {e}")

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/analyze")
async def analyze_code(
    file:            UploadFile = File(...),
    project_name:    str        = Form("unnamed_project"),
    language:        str        = Form("python"),
    project_context: str        = Form(""),
    debug:           bool       = Form(False),
):
    print(f"[DEBUG] language='{language}' project_name='{project_name}'")

    allowed_extensions = {".zip", ".py", ".java", ".js", ".ts", ".jsx", ".tsx"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Allowed: {allowed_extensions}",
        )

    session_id = str(uuid.uuid4())
    temp_dir   = TEMP_DIR / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    upload_path = temp_dir / file.filename

    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if file_ext == ".zip":
        shutil.unpack_archive(str(upload_path), str(temp_dir))
        upload_path.unlink()
        source_path = str(temp_dir)
    else:
        source_path = str(upload_path)

    jobs[session_id] = {
        "status":   "pending",
        "stage":    "ingestion",
        "progress": 0,
        "message":  "Starting pipeline…",
        "result":   None,
        "error":    None,
    }

    threading.Thread(
        target=run_analysis_job,
        args=(session_id, source_path, file.filename,
              project_name, language, project_context, debug),
        daemon=True,
    ).start()

    return JSONResponse(content={
        "job_id":     session_id,
        "session_id": session_id,
        "filename":   file.filename,
        "language":   language,
        "status":     "pending",
        "message":    "Pipeline started",
    })


@app.get("/status/{session_id}")
def get_status(session_id: str):
    job = jobs.get(session_id)
    if not job:
        if (REPORTS_DIR / f"{session_id}.json").exists():
            return {
                "job_id":         session_id,
                "status":         "complete",
                "stage":          "aggregation",
                "progress":       100,
                "message":        "Analysis complete",
                "findings_count": 0,
            }
        raise HTTPException(status_code=404, detail="Session not found.")

    return {
        "job_id":         session_id,
        "status":         job["status"],
        "stage":          job.get("stage",    "ingestion"),
        "progress":       job.get("progress", 0),
        "message":        job.get("message",  ""),
        "findings_count": 0,
        "error":          job.get("error"),
    }


@app.get("/report/{session_id}/json")
def get_json_report(session_id: str):
    path = REPORTS_DIR / f"{session_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(str(path), media_type="application/json")


@app.get("/report/{session_id}/markdown")
def get_markdown_report(session_id: str):
    path = REPORTS_DIR / f"{session_id}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(str(path), media_type="text/markdown")


@app.get("/report/{session_id}/pdf")
def get_pdf_report(session_id: str):
    path = REPORTS_DIR / f"{session_id}.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF report not found.")
    return FileResponse(str(path), media_type="application/pdf")


@app.get("/report/{session_id}/sarif")
def get_sarif_report(session_id: str):
    json_path = REPORTS_DIR / f"{session_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")
    with open(json_path) as f:
        data = json.load(f)
    sarif = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {"driver": {"name": "CodeScan", "version": "1.0.0", "rules": []}},
            "results": [
                {
                    "ruleId": finding.get("issue_type", "unknown"),
                    "level":  "error" if finding.get("severity") in ["Critical", "High"] else "warning",
                    "message": {"text": finding.get("description", "")},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.get("file_path", "")},
                            "region": {"startLine": finding.get("start_line", 1)},
                        }
                    }],
                }
                for finding in data.get("findings", [])
            ],
        }],
    }
    return JSONResponse(content=sarif)


@app.delete("/session/{session_id}")
def cleanup_session(session_id: str):
    temp_dir = TEMP_DIR / session_id
    if temp_dir.exists():
        shutil.rmtree(str(temp_dir))
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found.")
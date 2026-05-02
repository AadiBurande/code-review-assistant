# main.py
import os
import uuid
import shutil
import threading
import json
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from langgraph_pipeline import run_pipeline
from aggregator import build_report, save_markdown_report
from pdf_generator import generate_pdf_report
from database import save_report, get_report, get_history
from github_integration import fetch_github_repo, validate_github_url

BASE_DIR    = Path(__file__).resolve().parent.parent
TEMP_DIR    = BASE_DIR / "temp_uploads"
REPORTS_DIR = BASE_DIR / "reports"


class SuppressStatusLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/status/" not in record.getMessage()


logging.getLogger("uvicorn.access").addFilter(SuppressStatusLogs())

jobs: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    print("[Server] Shutting down gracefully.")


app = FastAPI(title="AI Code Review Assistant", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Flatten report helper ─────────────────────────────────────────────────────

def flatten_report(report, session_id: str, filename: str, language: str) -> dict:
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


# ── Core analysis job ─────────────────────────────────────────────────────────

def run_analysis_job(
    session_id:      str,
    source_path:     str,
    filename:        str,
    project_name:    str,
    language:        str,
    project_context: str,
    debug:           bool,
):
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

        # ── Pull plagiarism result from pipeline state ────────────────────
        plagiarism = state.get("plagiarism_result")
        blocked    = plagiarism.get("blocked", False) if plagiarism else False

        report = build_report(state, language=language)
        flat   = flatten_report(report, session_id, filename, language)

        # ── Override score/verdict/findings if blocked by plagiarism ─────
        if blocked:
            flat["overall_score"]  = 0
            flat["verdict"]        = "reject"
            flat["total_findings"] = 0
            flat["findings"]       = []
            flat["sub_scores"]     = {
                "bug":         0,
                "security":    0,
                "performance": 0,
                "style":       0,
            }

        # ── Always include plagiarism_result in JSON ──────────────────────
        flat["plagiarism_result"] = plagiarism

        # ── Save JSON ─────────────────────────────────────────────────────
        json_path = REPORTS_DIR / f"{session_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(flat, f, indent=2)
        print(f"[Report] JSON saved → {json_path}")

        # ── Save Markdown ─────────────────────────────────────────────────
        save_markdown_report(report, str(REPORTS_DIR / f"{session_id}.md"))

        # ── Generate PDF (with plagiarism section if detected) ────────────
        pdf_path = str(REPORTS_DIR / f"{session_id}.pdf")
        generate_pdf_report(report, pdf_path, plagiarism_result=plagiarism)

        # ── Save to DB ────────────────────────────────────────────────────
        save_report(flat)

        # ── Mark job complete ─────────────────────────────────────────────
        jobs[session_id].update({
            "status":   "complete",
            "stage":    "aggregation",
            "progress": 100,
            "message":  "Blocked — plagiarism detected" if blocked else "Analysis complete",
            "plagiarism_result": plagiarism,
            "result": {
                "session_id":      session_id,
                "score":           flat["overall_score"],
                "verdict":         flat["verdict"],
                "total_findings":  flat["total_findings"],
                "blocked":         blocked,
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


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/")
def health_check():
    return {"status": "ok", "version": "1.1.0"}


# ── File upload route ─────────────────────────────────────────────────────────

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
        "source":   "upload",
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
        "source":     "upload",
    })


# ── GitHub URL validation endpoint ────────────────────────────────────────────

@app.get("/analyze/github/validate")
async def validate_github(
    url:   str,
    token: Optional[str] = None,
):
    result = validate_github_url(url=url, token=token or os.getenv("GITHUB_TOKEN"))
    if not result["valid"]:
        raise HTTPException(status_code=422, detail=result["message"])
    return JSONResponse(content=result)


# ── GitHub analysis request schema ────────────────────────────────────────────

class GitHubAnalyzeRequest(BaseModel):
    repo_url:        str
    branch:          Optional[str] = None
    project_name:    Optional[str] = None
    language:        Optional[str] = None
    project_context: str           = ""
    token:           Optional[str] = None
    debug:           bool          = False


# ── GitHub analysis route ─────────────────────────────────────────────────────

@app.post("/analyze/github")
async def analyze_github(req: GitHubAnalyzeRequest):
    session_id = str(uuid.uuid4())

    jobs[session_id] = {
        "status":   "pending",
        "stage":    "github_fetch",
        "progress": 0,
        "message":  "Fetching repository from GitHub…",
        "result":   None,
        "error":    None,
        "source":   "github",
        "repo_url": req.repo_url,
    }

    def github_job():
        jobs[session_id].update({
            "stage":    "github_fetch",
            "message":  "Fetching repository files from GitHub…",
            "progress": 5,
            "status":   "running",
        })

        token = req.token or os.getenv("GITHUB_TOKEN", "") or None

        fetch_result = fetch_github_repo(
            url=req.repo_url,
            token=token,
            temp_base=str(TEMP_DIR),
            session_id=session_id,
        )

        if not fetch_result.success:
            jobs[session_id].update({
                "status":  "failed",
                "message": fetch_result.error,
                "error":   fetch_result.error,
            })
            print(f"[GitHub] Fetch failed for {session_id}: {fetch_result.error}")
            return

        project_name = req.project_name or fetch_result.repo_name
        language     = req.language     or fetch_result.detected_language
        filename     = f"{fetch_result.owner}/{fetch_result.repo_name}"

        jobs[session_id].update({
            "stage":    "ingestion",
            "message":  f"GitHub fetch done ({fetch_result.file_count} files). Starting analysis…",
            "progress": 15,
            "status":   "running",
            "github_meta": {
                "owner":    fetch_result.owner,
                "repo":     fetch_result.repo_name,
                "branch":   fetch_result.branch,
                "files":    fetch_result.file_count,
                "size_kb":  fetch_result.total_bytes // 1024,
                "language": fetch_result.detected_language,
            },
        })

        print(f"[GitHub] Fetch complete → {fetch_result.file_count} files, "
              f"lang={language}, path={fetch_result.local_path}")

        run_analysis_job(
            session_id=session_id,
            source_path=fetch_result.local_path,
            filename=filename,
            project_name=project_name,
            language=language,
            project_context=req.project_context,
            debug=req.debug,
        )

    threading.Thread(target=github_job, daemon=True).start()

    return JSONResponse(content={
        "job_id":     session_id,
        "session_id": session_id,
        "repo_url":   req.repo_url,
        "status":     "pending",
        "message":    "GitHub pipeline started",
        "source":     "github",
    })


# ── Status endpoint ───────────────────────────────────────────────────────────

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

    response = {
        "job_id":         session_id,
        "status":         job["status"],
        "stage":          job.get("stage",    "ingestion"),
        "progress":       job.get("progress", 0),
        "message":        job.get("message",  ""),
        "findings_count": 0,
        "error":          job.get("error"),
        "source":         job.get("source",   "upload"),
    }

    if "github_meta" in job:
        response["github_meta"] = job["github_meta"]

    # ── Include plagiarism result in status once complete ─────────────────
    if job.get("plagiarism_result"):
        response["plagiarism_result"] = job["plagiarism_result"]

    return response


# ── Report endpoints ──────────────────────────────────────────────────────────

@app.get("/report/{session_id}/json")
def get_json_report(session_id: str):
    # Try DB first
    db_report = get_report(session_id)
    if db_report:
        return JSONResponse(content=db_report)

    # Fall back to local file
    path = REPORTS_DIR / f"{session_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return JSONResponse(content=data)


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
            "tool": {"driver": {"name": "CodeScan", "version": "1.1.0", "rules": []}},
            "results": [
                {
                    "ruleId":  finding.get("issue_type", "unknown"),
                    "level":   "error" if finding.get("severity") in ["Critical", "High"] else "warning",
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


@app.get("/history")
def get_scan_history(limit: int = 50):
    return JSONResponse(content=get_history(limit))


@app.delete("/session/{session_id}")
def cleanup_session(session_id: str):
    temp_dir = TEMP_DIR / session_id
    if temp_dir.exists():
        shutil.rmtree(str(temp_dir))
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found.")

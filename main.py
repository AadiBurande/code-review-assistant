# main.py
import os
import uuid
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from langgraph_pipeline import run_pipeline
from aggregator import build_report, save_json_report, save_markdown_report

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("temp_uploads", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    yield

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Code Review Assistant",
    description="Analyzes Python, Java, and JavaScript code for bugs, security, performance, and style issues.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Response Models ───────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    version: str

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_model=HealthResponse)
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/analyze")
async def analyze_code(
    file: UploadFile = File(...),
    project_name: str = "unnamed_project",
    language: str = "python",
    project_context: str = "",
    debug: bool = False,
):
    allowed_extensions = {".zip", ".py", ".java", ".js"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Allowed: {allowed_extensions}"
        )

    # Save uploaded file
    session_id = str(uuid.uuid4())
    temp_dir = Path("temp_uploads") / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    upload_path = temp_dir / file.filename

    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Extract ZIP if needed
    if file_ext == ".zip":
        shutil.unpack_archive(str(upload_path), str(temp_dir))
        upload_path.unlink()
        source_path = str(temp_dir)
    else:
        source_path = str(upload_path)

    # Run pipeline
    state = run_pipeline(
        source_path=source_path,
        project_name=project_name,
        language=language,
        project_context=project_context,
        debug=debug,
    )

    # Build and save report
    report = build_report(state, language=language)
    json_path = f"reports/{session_id}.json"
    md_path   = f"reports/{session_id}.md"
    save_json_report(report, json_path)
    save_markdown_report(report, md_path)

    return JSONResponse(content={
        "session_id": session_id,
        "score": report.metadata.score,
        "verdict": report.metadata.verdict,
        "total_findings": report.metadata.total_findings,
        "report_json": f"/report/{session_id}/json",
        "report_markdown": f"/report/{session_id}/markdown",
    })


@app.get("/report/{session_id}/json")
def get_json_report(session_id: str):
    path = Path(f"reports/{session_id}.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(str(path), media_type="application/json")


@app.get("/report/{session_id}/markdown")
def get_markdown_report(session_id: str):
    path = Path(f"reports/{session_id}.md")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(str(path), media_type="text/markdown")


@app.delete("/session/{session_id}")
def cleanup_session(session_id: str):
    temp_dir = Path("temp_uploads") / session_id
    if temp_dir.exists():
        shutil.rmtree(str(temp_dir))
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found.")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="AI Code Review Assistant")
    parser.add_argument("--host",   default="127.0.0.1")
    parser.add_argument("--port",   type=int, default=8000)
    parser.add_argument("--reload", action="store_true", default=True)
    args = parser.parse_args()

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)

# langgraph_pipeline.py
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import TypedDict, List, Dict, Any, Optional, Callable

from langgraph.graph import StateGraph, END

from loader import CodeDocumentLoader, CodeChunk
from analyzers import run_static_analysis, findings_to_dict
from agents import (
    run_bug_detection_agent,
    run_security_agent,
    run_performance_agent,
    run_style_agent,
    Finding,
)
from context_builder import build_context
from validators import validate_findings

load_dotenv()

# ── Shared Pipeline State ──────────────────────────────────────────────────────

class PipelineState(TypedDict):
    source_path:          str
    project_name:         str
    language:             str
    project_context:      str
    debug:                bool
    chunks:               List[Any]
    static_findings:      List[Dict]
    bug_findings:         List[Dict]
    security_findings:    List[Dict]
    performance_findings: List[Dict]
    style_findings:       List[Dict]
    all_findings:         List[Dict]
    _status_callback:     Optional[Any]


def _update(state: PipelineState, stage: str, message: str, progress: int):
    cb = state.get("_status_callback")
    if cb:
        cb(stage, message, progress)


def _rebuild_chunks(state: PipelineState) -> List[CodeChunk]:
    return [CodeChunk(**c) for c in state["chunks"]]


def _relevant_static(chunk: CodeChunk, static: List[Dict]) -> List[Dict]:
    """Return static findings relevant to this chunk, skipping malformed entries."""
    relevant = []
    for f in static:
        if not isinstance(f, dict):
            continue
        if "line" not in f:
            print(f"  [Pipeline] ✗ Malformed static finding skipped: keys={list(f.keys())[:5]}")
            continue
        if (
            f.get("file_path") == chunk.file_path
            and chunk.start_line <= f["line"] <= chunk.end_line
        ):
            relevant.append(f)
    return relevant


def _read_full_file(file_path: str, fallback: str) -> str:
    """Read the full source file for accurate line count validation."""
    try:
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return fallback


# ── Node 1: Ingest ─────────────────────────────────────────────────────────────

def ingest_node(state: PipelineState) -> PipelineState:
    _update(state, "ingestion", "Ingesting source files…", 5)
    print("\n[Pipeline] Stage 1: Ingesting source files...")
    loader = CodeDocumentLoader(
        source_path=state["source_path"],
        language_override=state.get("language"),
    )
    chunks = loader.load()
    print(f"[Pipeline] Loaded {len(chunks)} chunk(s).")
    _update(state, "ingestion", f"Loaded {len(chunks)} chunk(s).", 12)
    return {**state, "chunks": [c.__dict__ for c in chunks]}


# ── Node 2: Static Analysis ────────────────────────────────────────────────────

def static_analysis_node(state: PipelineState) -> PipelineState:
    _update(state, "static_analysis", "Running static analyzers…", 18)
    print("\n[Pipeline] Stage 2: Running static analyzers...")
    language   = state["language"]
    file_paths = list({c["file_path"] for c in state["chunks"]})

    all_static = []
    for fp in file_paths:
        findings = run_static_analysis(fp, language)
        dicts    = findings_to_dict(findings)
        valid    = [d for d in dicts if isinstance(d, dict) and "line" in d]
        if len(valid) != len(dicts):
            print(f"  [Pipeline] ✗ Dropped {len(dicts) - len(valid)} malformed static findings")
        all_static.extend(valid)

    print(f"[Pipeline] Static analysis complete: {len(all_static)} finding(s).")
    _update(state, "static_analysis", f"Static analysis: {len(all_static)} finding(s).", 25)
    return {**state, "static_findings": all_static}


# ── Node 3: Bug Detection Agent ────────────────────────────────────────────────

def bug_agent_node(state: PipelineState) -> PipelineState:
    _update(state, "bug_agent", "Running Bug Detection Agent…", 32)
    print("\n[Pipeline] Stage 3a: Running Bug Detection Agent...")
    chunks  = _rebuild_chunks(state)
    static  = state["static_findings"]
    debug   = state["debug"]

    all_findings = []
    for chunk in chunks:
        try:
            code_ctx         = build_context(chunk.content, chunk.file_path)
            enriched_context = f"{state['project_context']}\n\n{code_ctx}"
            relevant         = _relevant_static(chunk, static)
            raw              = run_bug_detection_agent(chunk, relevant, enriched_context, debug)
            raw_dicts        = [f.model_dump() for f in raw]
            # ✅ Use full file content for accurate line count
            full_code        = _read_full_file(chunk.file_path, chunk.content)
            validated        = validate_findings(raw_dicts, full_code)
            all_findings.extend(validated)
        except Exception as e:
            print(f"  [BugAgent] ✗ Chunk {chunk.file_path} failed: {e} — skipping")
            continue

    print(f"[BugAgent] {len(all_findings)} validated finding(s).")
    _update(state, "bug_agent", f"Bug agent: {len(all_findings)} finding(s).", 45)
    return {**state, "bug_findings": all_findings}


# ── Node 4: Security Agent ─────────────────────────────────────────────────────

def security_agent_node(state: PipelineState) -> PipelineState:
    _update(state, "security_agent", "Running Security Audit Agent…", 52)
    print("\n[Pipeline] Stage 3b: Running Security Audit Agent...")
    chunks  = _rebuild_chunks(state)
    static  = state["static_findings"]
    debug   = state["debug"]

    all_findings = []
    for chunk in chunks:
        try:
            code_ctx         = build_context(chunk.content, chunk.file_path)
            enriched_context = f"{state['project_context']}\n\n{code_ctx}"
            relevant         = _relevant_static(chunk, static)
            raw              = run_security_agent(chunk, relevant, enriched_context, debug)
            raw_dicts        = [f.model_dump() for f in raw]
            # ✅ Use full file content for accurate line count
            full_code        = _read_full_file(chunk.file_path, chunk.content)
            validated        = validate_findings(raw_dicts, full_code)
            all_findings.extend(validated)
        except Exception as e:
            print(f"  [SecurityAgent] ✗ Chunk {chunk.file_path} failed: {e} — skipping")
            continue

    print(f"[SecurityAgent] {len(all_findings)} validated finding(s).")
    _update(state, "security_agent", f"Security agent: {len(all_findings)} finding(s).", 62)
    return {**state, "security_findings": all_findings}


# ── Node 5: Performance Agent ──────────────────────────────────────────────────

def performance_agent_node(state: PipelineState) -> PipelineState:
    _update(state, "performance_agent", "Running Performance Agent…", 68)
    print("\n[Pipeline] Stage 3c: Running Performance Agent...")
    chunks  = _rebuild_chunks(state)
    static  = state["static_findings"]
    debug   = state["debug"]

    all_findings = []
    for chunk in chunks:
        try:
            code_ctx         = build_context(chunk.content, chunk.file_path)
            enriched_context = f"{state['project_context']}\n\n{code_ctx}"
            relevant         = _relevant_static(chunk, static)
            raw              = run_performance_agent(chunk, relevant, enriched_context, debug)
            raw_dicts        = [f.model_dump() for f in raw]
            # ✅ Use full file content for accurate line count
            full_code        = _read_full_file(chunk.file_path, chunk.content)
            validated        = validate_findings(raw_dicts, full_code)
            all_findings.extend(validated)
        except Exception as e:
            print(f"  [PerfAgent] ✗ Chunk {chunk.file_path} failed: {e} — skipping")
            continue

    print(f"[PerfAgent] {len(all_findings)} validated finding(s).")
    _update(state, "performance_agent", f"Performance agent: {len(all_findings)} finding(s).", 78)
    return {**state, "performance_findings": all_findings}


# ── Node 6: Style Agent ────────────────────────────────────────────────────────

def style_agent_node(state: PipelineState) -> PipelineState:
    _update(state, "style_agent", "Running Style Agent…", 82)
    print("\n[Pipeline] Stage 3d: Running Style Agent...")
    chunks  = _rebuild_chunks(state)
    static  = state["static_findings"]
    debug   = state["debug"]

    all_findings = []
    for chunk in chunks:
        try:
            code_ctx         = build_context(chunk.content, chunk.file_path)
            enriched_context = f"{state['project_context']}\n\n{code_ctx}"
            relevant         = _relevant_static(chunk, static)
            raw              = run_style_agent(chunk, relevant, enriched_context, debug)
            raw_dicts        = [f.model_dump() for f in raw]
            # ✅ Use full file content for accurate line count
            full_code        = _read_full_file(chunk.file_path, chunk.content)
            validated        = validate_findings(raw_dicts, full_code)
            all_findings.extend(validated)
        except Exception as e:
            print(f"  [StyleAgent] ✗ Chunk {chunk.file_path} failed: {e} — skipping")
            continue

    print(f"[StyleAgent] {len(all_findings)} validated finding(s).")
    _update(state, "style_agent", f"Style agent: {len(all_findings)} finding(s).", 90)
    return {**state, "style_findings": all_findings}


# ── Node 7: Aggregator ─────────────────────────────────────────────────────────

def aggregator_node(state: PipelineState) -> PipelineState:
    _update(state, "aggregation", "Aggregating all findings…", 95)
    print("\n[Pipeline] Stage 4: Aggregating all findings...")
    all_findings = (
        state.get("bug_findings",         []) +
        state.get("security_findings",    []) +
        state.get("performance_findings", []) +
        state.get("style_findings",       [])
    )
    print(f"[Aggregator] Total raw findings before deduplication: {len(all_findings)}")
    return {**state, "all_findings": all_findings}


# ── Build LangGraph ────────────────────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("ingest",            ingest_node)
    graph.add_node("static_analysis",   static_analysis_node)
    graph.add_node("bug_agent",         bug_agent_node)
    graph.add_node("security_agent",    security_agent_node)
    graph.add_node("performance_agent", performance_agent_node)
    graph.add_node("style_agent",       style_agent_node)
    graph.add_node("aggregator",        aggregator_node)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest",            "static_analysis")
    graph.add_edge("static_analysis",   "bug_agent")
    graph.add_edge("bug_agent",         "security_agent")
    graph.add_edge("security_agent",    "performance_agent")
    graph.add_edge("performance_agent", "style_agent")
    graph.add_edge("style_agent",       "aggregator")
    graph.add_edge("aggregator",        END)

    return graph.compile()


# ── Public Runner ──────────────────────────────────────────────────────────────

def run_pipeline(
    source_path:      str,
    project_name:     str = "unnamed_project",
    language:         str = "python",
    project_context:  str = "",
    debug:            bool = False,
    status_callback:  Optional[Callable[[str, str, int], None]] = None,
) -> PipelineState:

    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "source_path":          source_path,
        "project_name":         project_name,
        "language":             language,
        "project_context":      project_context,
        "debug":                debug,
        "chunks":               [],
        "static_findings":      [],
        "bug_findings":         [],
        "security_findings":    [],
        "performance_findings": [],
        "style_findings":       [],
        "all_findings":         [],
        "_status_callback":     status_callback,
    }

    print(f"\n{'='*60}")
    print(f"  AI Code Review Pipeline Starting")
    print(f"  Project : {project_name}")
    print(f"  Language: {language}")
    print(f"  Path    : {source_path}")
    print(f"{'='*60}")

    final_state = pipeline.invoke(initial_state)

    print(f"\n{'='*60}")
    print(f"  Pipeline Complete!")
    print(f"  Total findings: {len(final_state['all_findings'])}")
    print(f"{'='*60}\n")

    return final_state


# ── Quick Test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = run_pipeline(
        source_path="tests/sample_inputs/all_issues.py",
        project_name="test_project",
        language="python",
        debug=False,
    )
    print(f"\nAll Findings ({len(result['all_findings'])} total):")
    for f in result["all_findings"]:
        print(f"  [{f['severity']}] {f['issue_type'].upper()} | "
              f"Line {f['start_line']} | {f['description'][:80]}")
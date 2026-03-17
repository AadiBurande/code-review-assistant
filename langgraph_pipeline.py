# langgraph_pipeline.py
import asyncio
import os
from dotenv import load_dotenv
from typing import TypedDict, List, Dict, Any, Optional
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

load_dotenv()

# ── Shared Pipeline State ─────────────────────────────────────────────────────

class PipelineState(TypedDict):
    source_path: str
    project_name: str
    language: str
    project_context: str
    debug: bool
    chunks: List[Any]                  # List[CodeChunk]
    static_findings: List[Dict]        # normalized static analysis dicts
    bug_findings: List[Dict]
    security_findings: List[Dict]
    performance_findings: List[Dict]
    style_findings: List[Dict]
    all_findings: List[Dict]           # merged after aggregation


# ── Node 1: Ingest ────────────────────────────────────────────────────────────

def ingest_node(state: PipelineState) -> PipelineState:
    print("\n[Pipeline] Stage 1: Ingesting source files...")
    loader = CodeDocumentLoader(
        source_path=state["source_path"],
        language_override=state.get("language"),
    )
    chunks = loader.load()
    print(f"[Pipeline] Loaded {len(chunks)} chunk(s).")
    return {**state, "chunks": [c.__dict__ for c in chunks]}


# ── Node 2: Static Analysis ───────────────────────────────────────────────────

def static_analysis_node(state: PipelineState) -> PipelineState:
    print("\n[Pipeline] Stage 2: Running static analyzers...")
    source_path = state["source_path"]
    language = state["language"]

    # Collect all unique file paths from chunks
    file_paths = list({c["file_path"] for c in state["chunks"]})

    all_static = []
    for fp in file_paths:
        findings = asyncio.run(run_static_analysis(fp, language))
        all_static.extend(findings_to_dict(findings))

    print(f"[Pipeline] Static analysis complete: {len(all_static)} finding(s).")
    return {**state, "static_findings": all_static}


# ── Helper: rebuild CodeChunk from dict ──────────────────────────────────────

def _rebuild_chunks(state: PipelineState) -> List[CodeChunk]:
    chunks = []
    for c in state["chunks"]:
        chunk = CodeChunk(**c)
        chunks.append(chunk)
    return chunks


# ── Node 3: Bug Detection Agent ───────────────────────────────────────────────

def bug_agent_node(state: PipelineState) -> PipelineState:
    print("\n[Pipeline] Stage 3a: Running Bug Detection Agent...")
    chunks = _rebuild_chunks(state)
    static = state["static_findings"]
    debug = state["debug"]
    context = state["project_context"]

    all_findings = []
    for chunk in chunks:
        # Filter static findings relevant to this chunk's line range
        relevant = [
            f for f in static
            if f["file_path"] == chunk.file_path
            and chunk.start_line <= f["line"] <= chunk.end_line
        ]
        findings = run_bug_detection_agent(chunk, relevant, context, debug)
        all_findings.extend([f.model_dump() for f in findings])

    print(f"[BugAgent] {len(all_findings)} finding(s) detected.")
    return {**state, "bug_findings": all_findings}


# ── Node 4: Security Agent ────────────────────────────────────────────────────

def security_agent_node(state: PipelineState) -> PipelineState:
    print("\n[Pipeline] Stage 3b: Running Security Audit Agent...")
    chunks = _rebuild_chunks(state)
    static = state["static_findings"]
    debug = state["debug"]
    context = state["project_context"]

    all_findings = []
    for chunk in chunks:
        relevant = [
            f for f in static
            if f["file_path"] == chunk.file_path
            and chunk.start_line <= f["line"] <= chunk.end_line
        ]
        findings = run_security_agent(chunk, relevant, context, debug)
        all_findings.extend([f.model_dump() for f in findings])

    print(f"[SecurityAgent] {len(all_findings)} finding(s) detected.")
    return {**state, "security_findings": all_findings}


# ── Node 5: Performance Agent ─────────────────────────────────────────────────

def performance_agent_node(state: PipelineState) -> PipelineState:
    print("\n[Pipeline] Stage 3c: Running Performance Agent...")
    chunks = _rebuild_chunks(state)
    static = state["static_findings"]
    debug = state["debug"]
    context = state["project_context"]

    all_findings = []
    for chunk in chunks:
        relevant = [
            f for f in static
            if f["file_path"] == chunk.file_path
            and chunk.start_line <= f["line"] <= chunk.end_line
        ]
        findings = run_performance_agent(chunk, relevant, context, debug)
        all_findings.extend([f.model_dump() for f in findings])

    print(f"[PerfAgent] {len(all_findings)} finding(s) detected.")
    return {**state, "performance_findings": all_findings}


# ── Node 6: Style Agent ───────────────────────────────────────────────────────

def style_agent_node(state: PipelineState) -> PipelineState:
    print("\n[Pipeline] Stage 3d: Running Style Agent...")
    chunks = _rebuild_chunks(state)
    static = state["static_findings"]
    debug = state["debug"]
    context = state["project_context"]

    all_findings = []
    for chunk in chunks:
        relevant = [
            f for f in static
            if f["file_path"] == chunk.file_path
            and chunk.start_line <= f["line"] <= chunk.end_line
        ]
        findings = run_style_agent(chunk, relevant, context, debug)
        all_findings.extend([f.model_dump() for f in findings])

    print(f"[StyleAgent] {len(all_findings)} finding(s) detected.")
    return {**state, "style_findings": all_findings}


# ── Node 7: Aggregator ────────────────────────────────────────────────────────

def aggregator_node(state: PipelineState) -> PipelineState:
    print("\n[Pipeline] Stage 4: Aggregating all findings...")
    all_findings = (
        state.get("bug_findings", []) +
        state.get("security_findings", []) +
        state.get("performance_findings", []) +
        state.get("style_findings", [])
    )
    print(f"[Aggregator] Total raw findings: {len(all_findings)}")
    return {**state, "all_findings": all_findings}


# ── Build LangGraph ───────────────────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    # Register nodes
    graph.add_node("ingest",           ingest_node)
    graph.add_node("static_analysis",  static_analysis_node)
    graph.add_node("bug_agent",        bug_agent_node)
    graph.add_node("security_agent",   security_agent_node)
    graph.add_node("performance_agent",performance_agent_node)
    graph.add_node("style_agent",      style_agent_node)
    graph.add_node("aggregator",       aggregator_node)

    # Define edges (sequential for stability; parallel can be added later)
    graph.set_entry_point("ingest")
    graph.add_edge("ingest",            "static_analysis")
    graph.add_edge("static_analysis",   "bug_agent")
    graph.add_edge("bug_agent",         "security_agent")
    graph.add_edge("security_agent",    "performance_agent")
    graph.add_edge("performance_agent", "style_agent")
    graph.add_edge("style_agent",       "aggregator")
    graph.add_edge("aggregator",        END)

    return graph.compile()


# ── Public Runner ─────────────────────────────────────────────────────────────

def run_pipeline(
    source_path: str,
    project_name: str = "unnamed_project",
    language: str = "python",
    project_context: str = "",
    debug: bool = False,
) -> PipelineState:

    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "source_path": source_path,
        "project_name": project_name,
        "language": language,
        "project_context": project_context,
        "debug": debug,
        "chunks": [],
        "static_findings": [],
        "bug_findings": [],
        "security_findings": [],
        "performance_findings": [],
        "style_findings": [],
        "all_findings": [],
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


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = run_pipeline(
        source_path="tests/sample_inputs/buggy_python.py",
        project_name="test_project",
        language="python",
        project_context="A sample buggy Python script for testing the review pipeline.",
        debug=False,
    )

    print(f"\nAll Findings Summary ({len(result['all_findings'])} total):")
    for f in result["all_findings"]:
        print(f"  [{f['severity']}] {f['issue_type'].upper()} | "
              f"Line {f['start_line']} | {f['description'][:80]}")

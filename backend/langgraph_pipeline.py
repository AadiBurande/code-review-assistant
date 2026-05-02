# langgraph_pipeline.py
import os
import asyncio
import hashlib
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
from plagiarism_detector import detect_plagiarism, PlagiarismResult

load_dotenv()

# ── File Hash Cache ───────────────────────────────────────────────────────────
_STATIC_ANALYSIS_CACHE: Dict[str, List[Dict]] = {}

def _file_hash(file_path: str) -> str:
    try:
        return hashlib.md5(Path(file_path).read_bytes()).hexdigest()
    except OSError:
        return file_path


# ── Pipeline State ────────────────────────────────────────────────────────────

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
    plagiarism_result:    Optional[Dict]
    blocked:              bool
    _status_callback:     Optional[Any]


def _update(state, stage, message, progress):
    cb = state.get("_status_callback")
    if cb:
        cb(stage, message, progress)

def _rebuild_chunks(state):
    return [CodeChunk(**c) for c in state["chunks"]]

def _relevant_static(chunk, static):
    return [
        f for f in static
        if isinstance(f, dict) and "line" in f
        and f.get("file_path") == chunk.file_path
        and chunk.start_line <= f["line"] <= chunk.end_line
    ]

def _read_full_file(file_path, fallback):
    try:
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return fallback


# ── Node 0: Plagiarism Detection ──────────────────────────────────────────────

def plagiarism_node(state: PipelineState) -> PipelineState:
    _update(state, "plagiarism_check", "Checking for AI-generated or plagiarized code…", 3)
    print("\n[Pipeline] Stage 0: Plagiarism / AI-Generation Detection...")

    source_path = state["source_path"]
    language    = state.get("language", "python")

    try:
        p = Path(source_path)
        if p.is_file():
            code     = p.read_text(encoding="utf-8", errors="ignore")
            filename = p.name
        elif p.is_dir():
            exts  = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rb"}
            parts = []
            for fp in sorted(p.rglob("*")):
                if fp.suffix in exts and fp.is_file():
                    try:
                        parts.append(fp.read_text(encoding="utf-8", errors="ignore"))
                    except OSError:
                        pass
            code     = "\n".join(parts)
            filename = str(source_path)
        else:
            code = ""
            filename = str(source_path)
    except Exception as e:
        print(f"  [PlagiarismNode] Could not read source: {e}")
        code = ""
        filename = str(source_path)

    if not code.strip():
        return {**state, "plagiarism_result": None, "blocked": False}

    result = detect_plagiarism(code=code, filename=filename, language=language)

    result_dict = {
        "score":           result.score,
        "verdict":         result.verdict,
        "blocked":         result.blocked,
        "confidence":      result.confidence,
        "evidence":        result.evidence,
        "remedies":        result.remedies,
        "summary":         result.summary,
        "heuristic_score": result.heuristic_score,
        "llm_score":       result.llm_score,
        "details":         result.details,
    }

    if result.blocked:
        _update(state, "plagiarism_check",
                f"⚠️ BLOCKED — AI/Plagiarism score: {result.score:.0f}/100.", 100)
        print(f"\n[Pipeline] ⚠️ BLOCKED. Score={result.score:.0f}. Halting.")
        return {**state, "plagiarism_result": result_dict, "blocked": True}

    _update(state, "plagiarism_check",
            f"✔ Plagiarism check passed. Score: {result.score:.0f}/100.", 8)
    return {**state, "plagiarism_result": result_dict, "blocked": False}


def _should_continue(state: PipelineState) -> str:
    return "end" if state.get("blocked", False) else "ingest"


# ── Node 1: Ingest ────────────────────────────────────────────────────────────

def ingest_node(state: PipelineState) -> PipelineState:
    _update(state, "ingestion", "Ingesting source files…", 12)
    print("\n[Pipeline] Stage 1: Ingesting source files...")
    loader = CodeDocumentLoader(
        source_path=state["source_path"],
        language_override=state.get("language"),
    )
    chunks = loader.load()
    print(f"[Pipeline] Loaded {len(chunks)} chunk(s).")
    _update(state, "ingestion", f"Loaded {len(chunks)} chunk(s).", 18)
    return {**state, "chunks": [c.__dict__ for c in chunks]}


# ── Node 2: Static Analysis (with hash cache) ─────────────────────────────────

def static_analysis_node(state: PipelineState) -> PipelineState:
    _update(state, "static_analysis", "Running static analyzers…", 22)
    print("\n[Pipeline] Stage 2: Running static analyzers...")
    language   = state["language"]
    file_paths = list({c["file_path"] for c in state["chunks"]})

    all_static = []
    for fp in file_paths:
        cache_key = _file_hash(fp)
        if cache_key in _STATIC_ANALYSIS_CACHE:
            cached = _STATIC_ANALYSIS_CACHE[cache_key]
            print(f"  [StaticAnalysis] Cache hit for {fp} ({len(cached)} findings)")
            all_static.extend(cached)
            continue
        findings = run_static_analysis(fp, language)
        dicts    = findings_to_dict(findings)
        valid    = [d for d in dicts if isinstance(d, dict) and "line" in d]
        _STATIC_ANALYSIS_CACHE[cache_key] = valid
        all_static.extend(valid)

    print(f"[Pipeline] Static analysis: {len(all_static)} finding(s).")
    _update(state, "static_analysis", f"Static: {len(all_static)} finding(s).", 28)
    return {**state, "static_findings": all_static}


# ── Node 3: Parallel Agents ───────────────────────────────────────────────────

async def _run_all_agents_async(chunks, static, project_context, debug):
    import concurrent.futures
    loop     = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def _run(agent_fn, chunk):
        try:
            code_ctx = build_context(chunk.content, chunk.file_path)
            ctx      = f"{project_context}\n\n{code_ctx}"
            rel      = _relevant_static(chunk, static)
            raw      = agent_fn(chunk, rel, ctx, debug)
            raw_d    = [f.model_dump() for f in raw]
            full     = _read_full_file(chunk.file_path, chunk.content)
            return validate_findings(raw_d, full)
        except Exception as e:
            print(f"  [Agent] ✗ {chunk.file_path}: {e}")
            return []

    agents = [run_bug_detection_agent, run_security_agent,
              run_performance_agent,   run_style_agent]
    tasks  = [
        loop.run_in_executor(executor, _run, agent_fn, chunk)
        for agent_fn in agents
        for chunk    in chunks
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    n = len(chunks)
    def _flat(r_list):
        return [item for r in r_list if isinstance(r, list) for item in r]

    return (
        _flat(results[0*n : 1*n]),   # bug
        _flat(results[1*n : 2*n]),   # security
        _flat(results[2*n : 3*n]),   # performance
        _flat(results[3*n : 4*n]),   # style
    )


def parallel_agents_node(state: PipelineState) -> PipelineState:
    _update(state, "agents", "Running all review agents in parallel…", 35)
    print("\n[Pipeline] Stage 3: Running all 4 agents in parallel...")

    chunks = _rebuild_chunks(state)
    static = state["static_findings"]
    debug  = state["debug"]
    ctx    = state["project_context"]

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bug_f, sec_f, perf_f, styl_f = loop.run_until_complete(
            _run_all_agents_async(chunks, static, ctx, debug)
        )
        loop.close()
    except Exception as e:
        print(f"  [ParallelAgents] Async failed: {e}. Falling back to sequential.")
        bug_f, sec_f, perf_f, styl_f = _run_sequential_fallback(chunks, static, ctx, debug)

    total = len(bug_f) + len(sec_f) + len(perf_f) + len(styl_f)
    print(f"  Bug={len(bug_f)} | Security={len(sec_f)} | Perf={len(perf_f)} | Style={len(styl_f)}")
    _update(state, "agents", f"Agents complete: {total} total findings.", 85)

    return {
        **state,
        "bug_findings":         bug_f,
        "security_findings":    sec_f,
        "performance_findings": perf_f,
        "style_findings":       styl_f,
    }


def _run_sequential_fallback(chunks, static, ctx, debug):
    bug_f, sec_f, perf_f, styl_f = [], [], [], []
    for chunk in chunks:
        try:
            code_ctx = build_context(chunk.content, chunk.file_path)
            enriched = f"{ctx}\n\n{code_ctx}"
            rel      = _relevant_static(chunk, static)
            full     = _read_full_file(chunk.file_path, chunk.content)

            for agent_fn, lst in [
                (run_bug_detection_agent, bug_f),
                (run_security_agent,      sec_f),
                (run_performance_agent,   perf_f),
                (run_style_agent,         styl_f),
            ]:
                raw = agent_fn(chunk, rel, enriched, debug)
                lst.extend(validate_findings([f.model_dump() for f in raw], full))
        except Exception as e:
            print(f"  [Fallback] ✗ {chunk.file_path}: {e}")
    return bug_f, sec_f, perf_f, styl_f


# ── Node 4: Aggregator ────────────────────────────────────────────────────────

def aggregator_node(state: PipelineState) -> PipelineState:
    _update(state, "aggregation", "Aggregating all findings…", 92)
    print("\n[Pipeline] Stage 4: Aggregating findings...")
    all_findings = (
        state.get("bug_findings",         []) +
        state.get("security_findings",    []) +
        state.get("performance_findings", []) +
        state.get("style_findings",       [])
    )
    print(f"[Aggregator] Total: {len(all_findings)} findings before dedup.")
    return {**state, "all_findings": all_findings}


# ── Build Graph ───────────────────────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)
    graph.add_node("plagiarism_check", plagiarism_node)
    graph.add_node("ingest",           ingest_node)
    graph.add_node("static_analysis",  static_analysis_node)
    graph.add_node("parallel_agents",  parallel_agents_node)
    graph.add_node("aggregator",       aggregator_node)

    graph.set_entry_point("plagiarism_check")
    graph.add_conditional_edges(
        "plagiarism_check",
        _should_continue,
        {"ingest": "ingest", "end": END},
    )
    graph.add_edge("ingest",          "static_analysis")
    graph.add_edge("static_analysis", "parallel_agents")
    graph.add_edge("parallel_agents", "aggregator")
    graph.add_edge("aggregator",       END)
    return graph.compile()


# ── Public Runner ─────────────────────────────────────────────────────────────

def run_pipeline(
    source_path:     str,
    project_name:    str = "unnamed_project",
    language:        str = "python",
    project_context: str = "",
    debug:           bool = False,
    status_callback: Optional[Callable[[str, str, int], None]] = None,
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
        "plagiarism_result":    None,
        "blocked":              False,
        "_status_callback":     status_callback,
    }

    print(f"\n{'='*60}\n  Project: {project_name} | Language: {language}\n{'='*60}")
    final_state = pipeline.invoke(initial_state)

    if final_state.get("blocked"):
        pr = final_state.get("plagiarism_result", {})
        print(f"\n{'='*60}\n  BLOCKED | Score: {pr.get('score',0):.0f} | {pr.get('verdict')}\n{'='*60}\n")
    else:
        print(f"\n{'='*60}\n  Complete! Findings: {len(final_state['all_findings'])}\n{'='*60}\n")

    return final_state
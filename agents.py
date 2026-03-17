# agents.py
import json
import os
import time
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ValidationError, field_validator

from prompts import (
    BUG_DETECTION_PROMPT,
    SECURITY_AUDIT_PROMPT,
    PERFORMANCE_PROMPT,
    STYLE_PROMPT,
    FINDING_SCHEMA,
)

# ── Pydantic Schema for a Single Finding ─────────────────────────────────────

class Finding(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    issue_type: str
    severity: str
    confidence: float
    description: str
    remediation: str
    code_suggestion: str = ""
    tags: List[str] = []
    references: List[str] = []
    internal_reasoning: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        allowed = {"Critical", "High", "Medium", "Low", "Info"}
        return v if v in allowed else "Info"

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        return max(0.0, min(1.0, float(v)))

    @field_validator("issue_type")
    @classmethod
    def validate_issue_type(cls, v):
        allowed = {"bug", "performance", "security", "style"}
        return v if v in allowed else "bug"


# ── LLM Factory ──────────────────────────────────────────────────────────────

def get_llm(temperature: float = 0.1):
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4o"),
            temperature=temperature,
            max_tokens=4096,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    elif provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
            temperature=temperature,
            max_tokens=4096,
            api_key=os.getenv("GROQ_API_KEY"),
        )

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=os.getenv("MODEL_NAME", "gemini-2.0-flash"),
            temperature=temperature,
            max_output_tokens=4096,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M"),
            temperature=temperature,
            num_predict=4096,
        )

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


# ── Core Agent Runner ─────────────────────────────────────────────────────────

def run_agent(
    prompt_template,
    code_chunk,
    static_findings: List[Dict],
    project_context: str = "",
    debug: bool = False,
    temperature: float = 0.1,
) -> List[Finding]:

    llm = get_llm(temperature=temperature)

    static_text = "\n".join([
        f"  Line {f['line']} [{f['severity']}] {f['tool']}/{f['rule_id']}: {f['description']}"
        for f in static_findings
    ]) or "  No static findings for this chunk."

    prompt_text = prompt_template.format(
        filename=code_chunk.file_path,
        language=code_chunk.language,
        start_line=code_chunk.start_line,
        end_line=code_chunk.end_line,
        code_snippet=code_chunk.content,
        static_findings=static_text,
        project_context=project_context or "No project context provided.",
        schema=FINDING_SCHEMA,
    )

    # Call LLM with retry on rate limit
    raw_output = ""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = llm.invoke([HumanMessage(content=prompt_text)])
            raw_output = response.content.strip()
            break
        except Exception as e:
            err_str = str(e).lower()
            if "rate_limit" in err_str or "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                wait = 30 * (attempt + 1)
                print(f"  [RateLimit] Limit hit. Waiting {wait}s before retry {attempt+1}/{max_retries}...")
                time.sleep(wait)
                if attempt == max_retries - 1:
                    print(f"  [RateLimit] Max retries reached. Skipping chunk.")
                    return []
            else:
                print(f"  [LLM Error] {type(e).__name__}: {str(e)[:200]}")
                return []

    if not raw_output:
        return []

    # Strip markdown code fences if model wraps output
    if raw_output.startswith("```"):
        raw_output = raw_output.split("```")[1]
        if raw_output.startswith("json"):
            raw_output = raw_output[4:]
        raw_output = raw_output.strip()

    # Parse and validate JSON
    findings = []
    try:
        raw_list = json.loads(raw_output)
        if not isinstance(raw_list, list):
            print(f"[Agent] Warning: Expected JSON array, got {type(raw_list)}")
            return []

        for item in raw_list:
            if not item.get("file_path"):
                item["file_path"] = code_chunk.file_path

            if debug:
                item["internal_reasoning"] = f"[debug] chunk={code_chunk.chunk_id}"

            try:
                finding = Finding(**item)
                findings.append(finding)
            except ValidationError as e:
                print(f"[Agent] Validation error: {e}")

    except json.JSONDecodeError as e:
        print(f"[Agent] JSON parse error: {e}\nRaw output:\n{raw_output[:500]}")

    return findings


# ── Individual Agent Functions ────────────────────────────────────────────────

def run_bug_detection_agent(chunk, static_findings, project_context="", debug=False) -> List[Finding]:
    print(f"  [BugAgent] Analyzing {chunk.chunk_id} ...")
    return run_agent(BUG_DETECTION_PROMPT, chunk, static_findings, project_context, debug, temperature=0.1)

def run_security_agent(chunk, static_findings, project_context="", debug=False) -> List[Finding]:
    print(f"  [SecurityAgent] Analyzing {chunk.chunk_id} ...")
    return run_agent(SECURITY_AUDIT_PROMPT, chunk, static_findings, project_context, debug, temperature=0.0)

def run_performance_agent(chunk, static_findings, project_context="", debug=False) -> List[Finding]:
    print(f"  [PerfAgent] Analyzing {chunk.chunk_id} ...")
    return run_agent(PERFORMANCE_PROMPT, chunk, static_findings, project_context, debug, temperature=0.2)

def run_style_agent(chunk, static_findings, project_context="", debug=False) -> List[Finding]:
    print(f"  [StyleAgent] Analyzing {chunk.chunk_id} ...")
    return run_agent(STYLE_PROMPT, chunk, static_findings, project_context, debug, temperature=0.1)


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from loader import CodeDocumentLoader
    from analyzers import run_static_analysis, findings_to_dict
    import asyncio

    loader = CodeDocumentLoader("tests/sample_inputs/buggy_python.py")
    chunks = loader.load()

    static_findings = asyncio.run(
        run_static_analysis("tests/sample_inputs/buggy_python.py", "python")
    )
    static_dicts = findings_to_dict(static_findings)

    chunk = chunks[0]
    print(f"\nTesting Bug Detection Agent on: {chunk.chunk_id}\n")
    findings = run_bug_detection_agent(chunk, static_dicts, debug=True)

    print(f"\n--- {len(findings)} finding(s) returned ---")
    for f in findings:
        print(f"\n  [{f.severity}] {f.issue_type.upper()} | Lines {f.start_line}-{f.end_line}")
        print(f"  Description : {f.description}")
        print(f"  Remediation : {f.remediation}")
        print(f"  Suggestion  :\n{f.code_suggestion}")

# agents.py
import json
import os
import re
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
    file_path:          str
    start_line:         int
    end_line:           int
    issue_type:         str
    severity:           str
    confidence:         float
    description:        str
    remediation:        str
    code_suggestion:    str            = ""
    tags:               List[str]      = []
    references:         List[str]      = []
    internal_reasoning: Optional[str]  = None

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

# ── Required keys every valid finding must have ───────────────────────────────

REQUIRED_FINDING_KEYS = {
    "file_path", "start_line", "end_line", "issue_type",
    "severity", "confidence", "description", "remediation",
}

VALID_SEVERITIES  = {"Critical", "High", "Medium", "Low", "Info"}
VALID_ISSUE_TYPES = {"bug", "security", "performance", "style"}

# ── issue_type normalization map ──────────────────────────────────────────────

ISSUE_TYPE_NORM = {
    "bug":          "bug",
    "bugs":         "bug",
    "security":     "security",
    "sec":          "security",
    "vulnerability":"security",
    "vuln":         "security",
    "performance":  "performance",
    "perf":         "performance",
    "style":        "style",
    "lint":         "style",
    "info":         "style",
    "information":  "style",
}

# ── Static findings filter ────────────────────────────────────────────────────

# Flake8 rule codes that are pure style/formatting noise
# Bug and Security agents must NOT see these — they echo them as fake findings
FLAKE8_STYLE_CODES = {
    "E501",  # line too long
    "E221",  # multiple spaces before operator
    "E222",  # multiple spaces after operator
    "E225",  # missing whitespace around operator
    "E231",  # missing whitespace after ','
    "E241",  # multiple spaces after ','
    "E251",  # unexpected spaces around keyword / parameter equals
    "E261",  # at least two spaces before inline comment
    "E262",  # inline comment should start with '# '
    "E265",  # block comment should start with '# '
    "E266",  # too many leading '#' for block comment
    "E302",  # expected 2 blank lines
    "E303",  # too many blank lines
    "E305",  # expected 2 blank lines after end of function
    "E401",  # multiple imports on one line
    "E711",  # comparison to None
    "E712",  # comparison to True/False
    "W291",  # trailing whitespace
    "W292",  # no newline at end of file
    "W293",  # whitespace before ':'
    "W391",  # blank line at end of file
    "W503",  # line break before binary operator
    "W504",  # line break after binary operator
    "C901",  # function complexity (keep for perf agent only)
}

# Tags/descriptions that identify a static finding as style-only noise
STYLE_NOISE_DESC_FRAGMENTS = {
    "line too long",
    "multiple spaces",
    "trailing whitespace",
    "blank line",
    "whitespace",
    "indentation",
    "missing whitespace",
    "operator spacing",
}


def filter_static_for_agent(static_findings: List[Dict], agent_type: str) -> List[Dict]:
    """
    Controls which static findings are sent to each agent.

    - bug agent    : Bandit + Pylint logic errors only. No Flake8 style noise.
    - security agent: Bandit/Semgrep security findings only. No Flake8 noise.
    - performance  : Complexity (C901) + resource findings only.
    - style agent  : ALL findings including Flake8 (style agent should see these).
    """
    if agent_type == "style":
        return static_findings  # style agent gets everything

    filtered = []
    for f in static_findings:
        if not isinstance(f, dict):
            continue

        tool    = f.get("tool", "").lower()
        rule_id = f.get("rule_id", "").upper()
        desc    = f.get("description", "").lower()

        # ✅ Always exclude Flake8 E/W style codes from bug and security agents
        if rule_id in FLAKE8_STYLE_CODES:
            continue

        # ✅ Also exclude by description pattern (catches tools that don't emit rule_id)
        if any(frag in desc for frag in STYLE_NOISE_DESC_FRAGMENTS):
            continue

        if agent_type == "performance":
            # Perf agent only needs complexity + resource findings
            is_complexity = rule_id == "C901" or "complex" in desc
            is_resource   = any(w in desc for w in ["resource", "memory", "loop", "n+1", "query"])
            if not (is_complexity or is_resource):
                continue

        filtered.append(f)

    removed = len(static_findings) - len(filtered)
    if removed > 0:
        print(f"  [StaticFilter] Filtered {removed} noise finding(s) for {agent_type} agent "
              f"({len(filtered)} remaining)")

    return filtered


# ── Validate finding shape ────────────────────────────────────────────────────

def _is_valid_finding_shape(item: Any) -> bool:
    """
    Validate that an item looks like a real finding dict.
    Rejects malformed objects the LLM returns (e.g. echoed example variables).
    """
    if not isinstance(item, dict):
        print(f"  [Agent] ✗ Item is not a dict: {type(item)}")
        return False

    if not REQUIRED_FINDING_KEYS.issubset(item.keys()):
        missing = REQUIRED_FINDING_KEYS - item.keys()
        print(f"  [Agent] ✗ Finding missing keys: {missing} — raw keys: {list(item.keys())[:6]}")
        return False

    if not isinstance(item.get("start_line"), int) or not isinstance(item.get("end_line"), int):
        print(f"  [Agent] ✗ Non-integer line numbers: "
              f"start={item.get('start_line')} end={item.get('end_line')}")
        return False

    if item.get("severity") not in VALID_SEVERITIES:
        print(f"  [Agent] ✗ Invalid severity: '{item.get('severity')}'")
        return False

    if item.get("issue_type") not in VALID_ISSUE_TYPES:
        print(f"  [Agent] ✗ Invalid issue_type: '{item.get('issue_type')}'")
        return False

    if not isinstance(item.get("description"), str) or not item["description"].strip():
        print("  [Agent] ✗ Empty or non-string description")
        return False

    if not isinstance(item.get("remediation"), str) or not item["remediation"].strip():
        print("  [Agent] ✗ Empty or non-string remediation")
        return False

    # ✅ Block style-only tags reported as bug or security
    STYLE_ONLY_TAGS = {"line-length", "line_length", "operator-spacing",
                       "whitespace", "e501", "trailing-whitespace"}
    finding_tags = {t.lower() for t in item.get("tags", [])}
    if item.get("issue_type") in ("bug", "security") and finding_tags & STYLE_ONLY_TAGS:
        print(f"  [Agent] ✗ Style-only tags in {item.get('issue_type')} finding: {finding_tags}")
        return False

    return True


# ── LLM Factory ──────────────────────────────────────────────────────────────

def get_llm(temperature: float = 0.1):
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4o"),
            temperature=temperature,
            max_tokens=2048,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    elif provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
            temperature=temperature,
            max_tokens=2048,
            api_key=os.getenv("GROQ_API_KEY"),
        )

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=os.getenv("MODEL_NAME", "gemini-2.0-flash"),
            temperature=temperature,
            max_output_tokens=2048,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b-instruct-q4_K_M"),
            temperature=temperature,
            num_predict=2048,
        )

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


# ── Safe JSON Parser ──────────────────────────────────────────────────────────

def safe_parse_json(raw: str) -> list:
    """
    Attempts to parse a JSON array from LLM output.
    Recovers all complete objects if output is truncated.
    """
    raw = raw.strip()

    try:
        result = json.loads(raw)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        pass

    last_comma = raw.rfind("},")
    last_brace = raw.rfind("}")
    cut = max(last_comma + 1, last_brace + 1) if last_comma != -1 else last_brace + 1

    if cut > 0:
        recovered = raw[:cut].rstrip(",").strip() + "\n]"
        if not recovered.lstrip().startswith("["):
            recovered = "[\n" + recovered
        try:
            result = json.loads(recovered)
            print(f"  [Agent] JSON recovered: {len(result)} finding(s) from truncated output.")
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            pass

    objects = re.findall(r'\{[^{}]+\}', raw, re.DOTALL)
    if objects:
        recovered_list = []
        for obj_str in objects:
            try:
                recovered_list.append(json.loads(obj_str))
            except json.JSONDecodeError:
                continue
        if recovered_list:
            print(f"  [Agent] JSON regex-recovered: {len(recovered_list)} finding(s).")
            return recovered_list

    print(f"  [Agent] JSON parse failed. Raw preview:\n{raw[:300]}")
    return []


# ── Core Agent Runner ─────────────────────────────────────────────────────────

def run_agent(
    prompt_template,
    code_chunk,
    static_findings: List[Dict],
    project_context: str = "",
    debug: bool = False,
    temperature: float = 0.1,
    agent_type: str = "bug",      # ✅ NEW — used for static filtering
) -> List[Finding]:

    llm = get_llm(temperature=temperature)

    # ✅ Filter static findings BEFORE building the prompt
    filtered_static = filter_static_for_agent(static_findings, agent_type)

    static_lines = []
    for f in filtered_static:
        if not isinstance(f, dict):
            continue
        line    = f.get("line",        "?")
        severity= f.get("severity",    "Info")
        tool    = f.get("tool",        "unknown")
        rule_id = f.get("rule_id",     "unknown")
        desc    = f.get("description", "No description")
        static_lines.append(f"  Line {line} [{severity}] {tool}/{rule_id}: {desc}")

    static_text = "\n".join(static_lines) or "  No static findings for this chunk."

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
                print(f"  [RateLimit] Waiting {wait}s before retry {attempt+1}/{max_retries}...")
                time.sleep(wait)
                if attempt == max_retries - 1:
                    print("  [RateLimit] Max retries reached. Skipping chunk.")
                    return []
            else:
                print(f"  [LLM Error] {type(e).__name__}: {str(e)[:200]}")
                return []

    if not raw_output:
        return []

    if raw_output.startswith("```"):
        raw_output = raw_output.split("```")[1]
        if raw_output.startswith("json"):
            raw_output = raw_output[4:]
        raw_output = raw_output.strip()

    raw_list = safe_parse_json(raw_output)

    if not raw_list:
        return []

    findings = []
    for item in raw_list:
        # ✅ Normalize issue_type BEFORE shape validation
        if isinstance(item, dict):
            raw_type   = str(item.get("issue_type", "")).lower().strip()
            normalized = ISSUE_TYPE_NORM.get(raw_type, raw_type)
            if normalized != item.get("issue_type"):
                print(f"  [Agent] Normalized issue_type: '{item.get('issue_type')}' → '{normalized}'")
            item["issue_type"] = normalized

        if not _is_valid_finding_shape(item):
            continue

        if not item.get("file_path"):
            item["file_path"] = code_chunk.file_path

        if "references" in item and isinstance(item["references"], list):
            item["references"] = [
                r.split("/")[-1] if isinstance(r, str) and r.startswith("http") else r
                for r in item["references"]
            ][:2]

        if "tags" in item and isinstance(item["tags"], list):
            item["tags"] = item["tags"][:3]

        if debug:
            item["internal_reasoning"] = f"[debug] chunk={code_chunk.chunk_id}"

        try:
            finding = Finding(**item)
            findings.append(finding)
        except ValidationError as e:
            print(f"  [Agent] Pydantic validation error: {e}")
            continue

    print(f"  [Agent] {len(raw_list)} parsed → {len(findings)} valid finding(s)")
    return findings


# ── Individual Agent Functions ────────────────────────────────────────────────

def run_bug_detection_agent(chunk, static_findings, project_context="", debug=False) -> List[Finding]:
    print(f"  [BugAgent] Analyzing {chunk.chunk_id} ...")
    return run_agent(
        BUG_DETECTION_PROMPT, chunk, static_findings,
        project_context, debug, temperature=0.1, agent_type="bug"
    )

def run_security_agent(chunk, static_findings, project_context="", debug=False) -> List[Finding]:
    print(f"  [SecurityAgent] Analyzing {chunk.chunk_id} ...")
    return run_agent(
        SECURITY_AUDIT_PROMPT, chunk, static_findings,
        project_context, debug, temperature=0.0, agent_type="security"
    )

def run_performance_agent(chunk, static_findings, project_context="", debug=False) -> List[Finding]:
    print(f"  [PerfAgent] Analyzing {chunk.chunk_id} ...")
    return run_agent(
        PERFORMANCE_PROMPT, chunk, static_findings,
        project_context, debug, temperature=0.2, agent_type="performance"
    )

def run_style_agent(chunk, static_findings, project_context="", debug=False) -> List[Finding]:
    print(f"  [StyleAgent] Analyzing {chunk.chunk_id} ...")
    return run_agent(
        STYLE_PROMPT, chunk, static_findings,
        project_context, debug, temperature=0.1, agent_type="style"
    )


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from loader import CodeDocumentLoader
    from analyzers import run_static_analysis, findings_to_dict

    loader  = CodeDocumentLoader("tests/sample_inputs/buggy_python.py")
    chunks  = loader.load()

    static_findings = run_static_analysis("tests/sample_inputs/buggy_python.py", "python")
    static_dicts    = findings_to_dict(static_findings)

    chunk = chunks[0]
    print(f"\nTesting Bug Detection Agent on: {chunk.chunk_id}\n")
    findings = run_bug_detection_agent(chunk, static_dicts, debug=True)

    print(f"\n--- {len(findings)} finding(s) returned ---")
    for f in findings:
        print(f"\n  [{f.severity}] {f.issue_type.upper()} | Lines {f.start_line}-{f.end_line}")
        print(f"  Description : {f.description}")
        print(f"  Remediation : {f.remediation}")
        print(f"  Suggestion  :\n{f.code_suggestion}")
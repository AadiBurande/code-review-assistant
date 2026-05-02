# plagiarism_detector.py

"""
AI/Plagiarism Detection Module

Detects AI-generated or plagiarised code using a two-stage approach:
  1. Heuristic scorer  — fast, regex/AST-based signals
  2. LLM scorer        — context-aware forensic analysis

Scoring philosophy:
  - Heuristic score alone NEVER blocks. It is a weak signal used to weight the LLM.
  - LLM score is the primary signal. It is calibrated to flag ONLY strong AI patterns.
  - BLOCK_THRESHOLD is set conservatively (65) to avoid false positives on real code.
  - WARN_THRESHOLD  (45) shows a warning banner but lets the review proceed.
"""

import re
import json
import os
from dataclasses import dataclass, field
from typing import Optional, List


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class PlagiarismResult:
    score:           float
    verdict:         str          # "CLEAN" | "SUSPICIOUS" | "AI_GENERATED"
    blocked:         bool
    confidence:      float
    evidence:        List[str]
    remedies:        List[str]
    summary:         str
    heuristic_score: float
    llm_score:       float
    details:         dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "score":           round(self.score, 1),
            "verdict":         self.verdict,
            "blocked":         self.blocked,
            "confidence":      round(self.confidence, 2),
            "evidence":        self.evidence,
            "remedies":        self.remedies,
            "summary":         self.summary,
            "heuristic_score": round(self.heuristic_score, 1),
            "llm_score":       round(self.llm_score, 1),
            "details":         self.details,
        }


# ── Heuristic scorer ──────────────────────────────────────────────────────────
# Looks for STRUCTURAL signals of AI generation only.
# Human buggy code with TODOs, bad naming, etc. scores VERY low here.

def _heuristic_score(code: str, language: str) -> float:
    """
    Returns 0-100. High score = strong structural AI signals.

    IMPORTANT: This scorer is DELIBERATELY conservative.
    Common human patterns (TODOs, short names, inline comments, bare excepts)
    do NOT increase this score — those are normal developer habits.
    Only patterns that are statistically rare in human-written code are scored.
    """
    score = 0.0
    lines = code.split("\n")
    non_empty = [l for l in lines if l.strip()]
    total = len(non_empty) or 1

    # ── Strong AI signals ────────────────────────────────────────────────────

    # 1. Every single public function has a docstring (rare in real code)
    func_defs     = re.findall(r'^\s*def \w+\(', code, re.MULTILINE)
    docstrings    = re.findall(r'^\s*def \w+\([^)]*\):\s*\n\s*["\']', code, re.MULTILINE)
    if len(func_defs) >= 4 and len(docstrings) / max(len(func_defs), 1) > 0.85:
        score += 20  # >85% of functions have docstrings — very unusual in real code

    # 2. Perfect type annotations on ALL functions (rare outside well-maintained libs)
    if len(func_defs) >= 4:
        typed_funcs = re.findall(r'def \w+\([^)]*:\s*\w', code)
        if len(typed_funcs) / max(len(func_defs), 1) > 0.85:
            score += 15

    # 3. Suspiciously uniform comment density (every 3-5 lines has a comment — AI habit)
    comment_lines  = sum(1 for l in lines if re.match(r'\s*#', l))
    comment_ratio  = comment_lines / total
    if 0.25 < comment_ratio < 0.50 and len(func_defs) > 5:
        # Uniform spread of comments across many functions is an AI pattern
        score += 10

    # 4. Zero personal style markers (no prints for debug, no commented-out code,
    #    no version history comments, no author markers)
    has_debug_prints   = bool(re.search(r'print\s*\(.*debug|print\s*\(.*test', code, re.I))
    has_commented_code = bool(re.search(r'#\s*(if|for|while|return|def|class)\s+', code))
    has_author_marker  = bool(re.search(r'#\s*(author|written by|created by|@\w+)', code, re.I))
    if not has_debug_prints and not has_commented_code and not has_author_marker:
        if len(func_defs) >= 6:
            score += 8  # Large file with zero personal markers

    # 5. Section headers like "# ── Section Name ──────" (common AI formatting)
    section_headers = re.findall(r'#\s*[─\-═]{3,}.*[─\-═]{3,}', code)
    if len(section_headers) >= 3:
        score += 12

    # 6. All functions are ~5-15 lines with identical structure (AI tends to
    #    produce uniformly-sized, uniformly-structured functions)
    if len(func_defs) >= 5:
        func_blocks = re.split(r'\ndef ', code)
        lengths = [len(b.split("\n")) for b in func_blocks if b.strip()]
        if lengths:
            avg = sum(lengths) / len(lengths)
            variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
            if variance < 4 and avg < 12:  # Very uniform, very short
                score += 10

    # ── NEGATIVE signals — human code patterns that REDUCE AI suspicion ──────
    # These ensure real buggy/messy code doesn't get flagged.

    # TODO comments are a strong human signal
    todo_count = len(re.findall(r'#\s*TODO|#\s*FIXME|#\s*HACK|#\s*XXX', code, re.I))
    if todo_count >= 2:
        score -= 15

    # Inline explanatory comments ("# just building query inline") are human
    inline_excuse_comments = re.findall(
        r'#\s*(just|quick|temp|workaround|not sure|idk|might need|was giving|getting|disabled for now)',
        code, re.I
    )
    if len(inline_excuse_comments) >= 2:
        score -= 20  # Strong human signal — devs explain their shortcuts

    # Bare except, silent pass, unclosed files are human mistakes, not AI
    human_mistakes = len(re.findall(r'except\s*:', code)) + \
                     len(re.findall(r'except\s+Exception\s*:', code)) + \
                     len(re.findall(r'f\.write|f\.read', code))  # manual file IO
    if human_mistakes >= 3:
        score -= 15

    # Hardcoded credentials/secrets are a human mistake, not an AI pattern
    has_hardcoded = bool(re.search(r'(password|secret|key)\s*=\s*["\'][^"\']{4,}["\']', code, re.I))
    if has_hardcoded:
        score -= 10

    # Mixed naming conventions (some snake_case, some camelCase) = human
    has_camel = bool(re.search(r'\b[a-z]+[A-Z]\w+\b', code))
    has_snake  = bool(re.search(r'\b[a-z]+_[a-z]+\b', code))
    if has_camel and has_snake:
        score -= 5

    return max(0.0, min(100.0, score))


# ── LLM scorer ────────────────────────────────────────────────────────────────

PLAGIARISM_PROMPT = """You are a code forensics expert. Your job is to determine whether the code below was written by a real human developer, or was entirely generated by an AI assistant (ChatGPT, Copilot, Claude, etc.).

CRITICAL RULES — READ BEFORE SCORING:
1. Buggy code, insecure code, and messy code are STRONG HUMAN signals. Real developers write bad code. AI writes polished code.
2. TODO comments, FIXME notes, inline excuse comments ("# disabled for now", "# just doing this quick") are STRONG HUMAN signals.
3. Short variable names (i, j, h, f, q), single-letter loops, non-descriptive names are HUMAN signals.
4. Hardcoded secrets, SQL injection, command injection, bare excepts — these are HUMAN MISTAKES. AI avoids these.
5. Inconsistent style (some camelCase, some snake_case, mixed spacing) is a HUMAN signal.
6. Mixing concerns in one function, long functions that "do too much" = human code.
7. Commented-out code blocks, leftover debug prints, version history in comments = human.

WHAT COUNTS AS AI EVIDENCE (score high ONLY for these):
- Every public function has a perfectly-written docstring with proper Args/Returns sections
- All functions have complete type annotations (def foo(x: int, y: str) -> bool:)
- Section dividers like "# ── Section Name ──────────" throughout the file
- Suspiciously perfect implementations with zero hacks or shortcuts
- Overly verbose inline explanations of completely obvious code ("# increment counter by 1")
- No human traces: no TODOs, no inline excuses, no debugging artifacts, no hardcoded test values
- Uniform function structure: every function is 8-12 lines, same pattern, same quality level
- Generic but perfectly correct placeholder code: class UserManager, class DataProcessor with textbook implementations

SCORING GUIDE:
- 0-30:  Clearly human-written (has bugs, TODOs, hacks, inconsistencies, personal style)
- 31-50: Probably human, some AI-like patterns (common in experienced devs influenced by AI tools)
- 51-70: Mixed signals — may be partially AI-assisted
- 71-85: Strong AI signals, likely AI-generated with minor edits
- 86-100: Almost certainly fully AI-generated, no human traces

Code to analyze:
```{language}
{code}
```

File: {filename} | Lines: {loc}

Respond with ONLY this JSON (no markdown, no explanation):
{{
  "plagiarism_score": <integer 0-100>,
  "confidence": <float 0.0-1.0>,
  "verdict": "<CLEAN|SUSPICIOUS|AI_GENERATED>",
  "evidence": ["<specific signal found>", ...],
  "remedies": ["<actionable advice>", ...]
}}

verdict rules:
- CLEAN: score 0-50 (proceed with review)
- SUSPICIOUS: score 51-70 (warn but proceed)
- AI_GENERATED: score 71-100 (block review)
"""


def _count_lines(code: str) -> int:
    return len([l for l in code.split("\n") if l.strip()])


def _llm_score(code: str, filename: str, language: str) -> dict:
    try:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model="qwen2.5-coder:7b-instruct-q4_K_M",
            temperature=0.1,
        )
    except ImportError:
        from langchain_community.chat_models import ChatOllama
        llm = ChatOllama(
            model="qwen2.5-coder:7b-instruct-q4_K_M",
            temperature=0.1,
        )

    loc = _count_lines(code)
    prompt = PLAGIARISM_PROMPT.format(
        language=language, code=code, filename=filename, loc=loc
    )

    try:
        raw = llm.invoke(prompt).content.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$",          "", raw, flags=re.MULTILINE)
        return json.loads(raw)
    except Exception as e:
        print(f"  [PlagiarismLLM] LLM analysis failed: {e} — defaulting to 0")
        return {"plagiarism_score": 0, "confidence": 0.0,
                "verdict": "CLEAN", "evidence": [], "remedies": []}


# ── Thresholds ────────────────────────────────────────────────────────────────

BLOCK_THRESHOLD = 65.0   # Block pipeline — almost certainly AI-generated
WARN_THRESHOLD  = 50.0   # Show warning banner but allow review to proceed


# ── Score blending ────────────────────────────────────────────────────────────

def _blend(h_score: float, llm_score: float) -> float:
    """
    LLM is the primary signal (80% weight).
    Heuristic is a weak supporting signal (20% weight).
    This prevents the heuristic from blocking real code when LLM gives a low score.
    """
    return round(0.20 * h_score + 0.80 * llm_score, 1)


# ── Public API ────────────────────────────────────────────────────────────────

def detect_plagiarism(
    code:     str,
    filename: str,
    language: str,
) -> PlagiarismResult:

    loc = _count_lines(code)
    print(f"  [PlagiarismDetector] Analyzing {filename} ({loc} lines)...")

    # Stage 1 — heuristics
    h_score = _heuristic_score(code, language)
    print(f"  [PlagiarismDetector] Heuristic score: {h_score:.1f}/100")

    # Stage 2 — LLM (always runs; heuristic never blocks alone)
    llm_result  = _llm_score(code, filename, language)
    llm_score   = float(llm_result.get("plagiarism_score", 0))
    confidence  = float(llm_result.get("confidence", 0.5))
    evidence    = llm_result.get("evidence", [])
    remedies    = llm_result.get("remedies", [])
    print(f"  [PlagiarismDetector] LLM score: {llm_score:.1f}/100")

    # Blend scores
    final_score = _blend(h_score, llm_score)

    # Verdict
    if final_score >= BLOCK_THRESHOLD:
        verdict = "AI_GENERATED"
        blocked = True
    elif final_score >= WARN_THRESHOLD:
        verdict = "SUSPICIOUS"
        blocked = False   # ← SUSPICIOUS no longer blocks — just shows banner
    else:
        verdict = "CLEAN"
        blocked = False

    print(f"  [PlagiarismDetector] Final: {final_score:.1f} | {verdict} | Blocked: {blocked}")

    # Default remedies if LLM didn't provide any and it's flagged
    if not remedies and final_score >= WARN_THRESHOLD:
        remedies = [
            "Write the code yourself from scratch — do not submit AI-generated code directly.",
            "If AI was used for ideas, rewrite it completely in your own style.",
            "Remove all auto-generated docstrings and write your own explanations.",
            "Add your own debug statements, error handling, and personal coding patterns.",
            "If this is legitimate code, contact your reviewer to manually verify authorship.",
        ]

    # Summary
    if blocked:
        summary = (
            f"⚠️ Review BLOCKED. AI/Plagiarism score: {final_score:.0f}/100 "
            f"(threshold: {BLOCK_THRESHOLD:.0f}). Verdict: {verdict}. "
            f"The code exhibits strong AI-generation signals."
        )
    elif final_score >= WARN_THRESHOLD:
        summary = (
            f"⚠️ Review proceeding with warning. Score: {final_score:.0f}/100. "
            f"Verdict: {verdict}. Some AI-assisted patterns detected — review results carefully."
        )
    else:
        summary = (
            f"✔ Plagiarism check passed. Score: {final_score:.0f}/100. "
            f"Verdict: {verdict}. Code appears to be human-written."
        )

    return PlagiarismResult(
        score=final_score,
        verdict=verdict,
        blocked=blocked,
        confidence=confidence,
        evidence=evidence,
        remedies=remedies,
        summary=summary,
        heuristic_score=h_score,
        llm_score=llm_score,
        details={
            "heuristic_score":  h_score,
            "llm_score":        llm_score,
            "block_threshold":  BLOCK_THRESHOLD,
            "warn_threshold":   WARN_THRESHOLD,
            "language":         language,
            "filename":         filename,
            "loc":              loc,
        },
    )

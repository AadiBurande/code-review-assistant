<div align="center">

```
 ██████╗ ██████╗ ██████╗ ███████╗███████╗ ██████╗ █████╗ ███╗   ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗████╗  ██║
██║     ██║   ██║██║  ██║█████╗  ███████╗██║     ███████║██╔██╗ ██║
██║     ██║   ██║██║  ██║██╔══╝  ╚════██║██║     ██╔══██║██║╚██╗██║
╚██████╗╚██████╔╝██████╔╝███████╗███████║╚██████╗██║  ██║██║ ╚████║
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
```

### Drop your code. Get a verdict. Ship with confidence.

<br>

[![Python](https://img.shields.io/badge/Python-3.10+-3B82F6?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-00BFA5?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16+-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![LangChain](https://img.shields.io/badge/LangChain-Multi--Agent-7C3AED?style=for-the-badge&logo=chainlink&logoColor=white)](https://python.langchain.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-FF6B35?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br>

**4 AI agents &nbsp;·&nbsp; 1 quality score &nbsp;·&nbsp; zero excuses for shipping broken code**

<br>

</div>

---

## 🧠 What is CodeScan?

**CodeScan** is a full-stack, AI-powered code review platform that runs your source code through a **parallel multi-agent pipeline** — simultaneously hunting bugs, security holes, performance bottlenecks, and style violations — all in **under 60 seconds**.

You get a **quality score out of 100**, a clear `ACCEPT / REVIEW / REJECT` verdict, line-level findings with actionable fixes, and downloadable reports in JSON, Markdown, PDF, and SARIF.

> No meetings. No waiting. Just answers.

<br>

<div align="center">

|  | Feature | Details |
|--|---------|---------|
| ⚡ | **Parallel execution** | All 4 agents run simultaneously via `ThreadPoolExecutor` |
| 📊 | **Quality score** | Weighted 0–100 with per-agent sub-scores |
| 🧹 | **Smart deduplication** | Cross-agent merge — no duplicate noise |
| 📄 | **Multi-format reports** | JSON · Markdown · PDF · SARIF |
| 🌐 | **Real-time dashboard** | Pipeline tracker · findings panel · file risk heatmap |
| 🔌 | **Pluggable LLMs** | Ollama · Gemini · Groq · OpenAI — one-line swap |
| 🚫 | **AI/Plagiarism detection** | Heuristic + LLM scoring, configurable threshold |

</div>

---

## ⚡ The Pipeline

```
                        ┌─────────────────────┐
           YOUR CODE ──▶│   CodeScan Engine   │
                        └─────────┬───────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
       ┌─────────────┐   ┌─────────────────┐   ┌──────────────────┐
       │ 🐛 Bug Agent │   │ 🔒 Security Agent│   │  ⚡ Perf Agent   │
       │             │   │                 │   │                  │
       │ Logic errors│   │ OWASP Top 10    │   │ O(n²) loops      │
       │ Null deref  │   │ Injections      │   │ Memory leaks     │
       │ Off-by-one  │   │ Hardcoded keys  │   │ Blocking I/O     │
       └──────┬──────┘   └────────┬────────┘   └───────┬──────────┘
              └──────────────┬────┘                    │
                             │           ┌─────────────┘
                             ▼           ▼
                      ┌────────────────────┐
                      │   🎨 Style Agent   │
                      │                   │
                      │ PEP 8 · naming    │
                      │ Dead code · docs  │
                      └────────┬──────────┘
                               │
                ┌──────────────▼──────────────┐
                │    Aggregator + Dedup        │  ← no duplicate noise
                └──────────────┬──────────────┘
                               │
                ┌──────────────▼──────────────┐
                │   Score · Verdict           │
                │   Findings · Reports        │
                └─────────────────────────────┘
```

All 4 agents run **in parallel** — because waiting is for CI pipelines that don't respect your time.

---

## 🎯 What Gets Caught

<details>
<summary><b>🐛 Bug Detection</b> — click to expand</summary>
<br>

| Finding | Description |
|---------|-------------|
| Logic errors | Incorrect conditions, flipped comparisons, unreachable branches |
| Null dereferences | Unsafe access on potentially `None` values |
| Unhandled exceptions | Missing `try/except` on risky operations |
| Off-by-one | Fence-post errors in loops and slice indexing |
| Type mismatches | Operations on incompatible types |

</details>

<details>
<summary><b>🔒 Security Audit</b> — click to expand</summary>
<br>

| Finding | Description |
|---------|-------------|
| OWASP Top 10 | Full coverage of the industry-standard vulnerability list |
| SQL / command injection | String-concatenated queries and unsafe shell calls |
| Weak cryptography | MD5, SHA-1, ECB mode, hardcoded IVs |
| Hardcoded secrets | API keys, passwords, tokens baked into source code |
| CVEs | Known vulnerable dependency versions |

</details>

<details>
<summary><b>⚡ Performance</b> — click to expand</summary>
<br>

| Finding | Description |
|---------|-------------|
| O(n²) loops | Nested iterations that could use a set or dict |
| Memory leaks | Objects never released, ever-growing caches |
| Blocking I/O | Synchronous calls inside async contexts |
| N+1 DB queries | Queries inside loops — use batch fetch |
| Unnecessary allocations | Repeated object creation in hot paths |

</details>

<details>
<summary><b>🎨 Style & Quality</b> — click to expand</summary>
<br>

| Finding | Description |
|---------|-------------|
| PEP 8 | Spacing, line length, import ordering |
| Naming conventions | `snake_case`, `SCREAMING_SNAKE`, `PascalCase` violations |
| Dead code | Unused variables, functions, and imports |
| Missing docs | Public functions/classes with no docstring |
| Cyclomatic complexity | Functions too complex to reason about |

</details>

---

## 🛠️ Tech Stack

<details open>
<summary><b>⚙️ Backend</b></summary>
<br>

| Tool | Role |
|------|------|
| **FastAPI** | REST API + SSE streaming |
| **LangChain** | LLM abstraction layer |
| **ThreadPoolExecutor** | Parallel agent execution |
| **Pydantic** | Finding schema validation |
| **pylint / flake8** | Style static analysis |
| **bandit** | Security static scan |
| **radon** | Cyclomatic complexity |
| **semgrep** | Pattern-based vulnerability detection |
| **ReportLab** | PDF report generation |

</details>

<details open>
<summary><b>◈ Frontend</b></summary>
<br>

| Tool | Role |
|------|------|
| **Next.js 16** | App Router, SSR |
| **TypeScript** | End-to-end type safety |
| **Tailwind CSS** | Dark-first UI system |
| **SSE Hook** | Real-time pipeline tracking |

</details>

<details open>
<summary><b>🤖 LLM Providers</b></summary>
<br>

| Provider | Type | Notes |
|----------|------|-------|
| 🟢 **Ollama** | Local · free · private | **Recommended** |
| 🔵 **Google Gemini** | Cloud API | Fast, capable |
| 🟠 **Groq** | Cloud API | Ultra-fast inference |
| ⚪ **OpenAI** | Cloud API | GPT-4 series |

</details>

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version |
|-------------|---------|
| 🐍 Python | 3.10+ |
| 📦 Node.js | 18+ |
| 📜 Poetry | latest — [install here](https://python-poetry.org/docs/#installation) |
| 🤖 LLM backend | [Ollama](https://ollama.ai) *(free, local)* or an API key |

---

### Step 1 — Clone

```bash
git clone https://github.com/AadiBurande/code-review-assistant.git
cd code-review-assistant
```

### Step 2 — Backend setup

```bash
cd backend
poetry install
cp .env.example .env
```

Open `.env` and pick your LLM provider:

```env
# ── Pick ONE ──────────────────────────────────────────
LLM_PROVIDER=ollama          # free · runs locally · recommended
OLLAMA_MODEL=qwen2.5-coder:7b-instruct-q4_K_M

# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your_key_here

# LLM_PROVIDER=groq
# GROQ_API_KEY=your_key_here

# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_key_here
# ──────────────────────────────────────────────────────
```

### Step 3 — Frontend setup

```bash
cd ../frontend
npm install
```

### Step 4 — Launch

```bash
# Terminal 1 — API server
cd backend
poetry run uvicorn main:app --reload --port 8000 --reload-exclude "temp_uploads"

# Terminal 2 — Web dashboard
cd frontend
npm run dev
```

🎉 Open **[http://localhost:3000](http://localhost:3000)**

> **⚠️ Dev tip:** Always use `--reload-exclude "temp_uploads"`.
> Without it, Uvicorn's file watcher sees uploaded files being written mid-analysis and **restarts the server**, killing the pipeline.

---

## 📡 API Reference

<details>
<summary><b>POST /analyze — Submit a file for full multi-agent review</b></summary>
<br>

**Request**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `file` | `File` | ✅ | Source file or `.zip` project |
| `language` | `string` | ✅ | `python` · `javascript` · `java` |
| `project_name` | `string` | ❌ | Label for the report *(default: `unnamed_project`)* |

**Response**

```jsonc
{
  "job_id": "abc123",
  "score": 13.5,
  "verdict": "REJECT",              // "ACCEPT" | "REVIEW" | "REJECT"
  "project": "my_service",
  "language": "python",
  "findings": [
    {
      "agent": "security",
      "severity": "HIGH",           // "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO"
      "file": "app/auth.py",
      "line": 42,
      "message": "Hardcoded API key detected in variable `secret`",
      "suggestion": "Use os.environ or a secrets manager instead."
    }
  ],
  "summary": {
    "total": 38,
    "bugs": 13,
    "security": 12,
    "performance": 5,
    "style": 11
  },
  "reports": {
    "markdown_url": "/reports/abc123.md",
    "pdf_url":      "/reports/abc123.pdf",
    "sarif_url":    "/reports/abc123.sarif",
    "json_url":     "/reports/abc123.json"
  }
}
```

</details>

<details>
<summary><b>GET /status/{job_id} — Real-time pipeline status</b></summary>
<br>

```jsonc
{
  "job_id": "abc123",
  "status": "running",             // "queued" | "running" | "complete" | "failed"
  "stage": "security_agent",
  "progress": 60,                  // 0–100
  "message": "Running security audit...",
  "eta_seconds": 12
}
```

</details>

---

## 📁 Project Structure

```
code-review-assistant/
│
├── backend/
│   ├── main.py                    ← FastAPI app + all endpoints
│   ├── agents.py                  ← Bug / Security / Perf / Style agents
│   ├── langgraph_pipeline.py      ← Pipeline orchestration
│   ├── aggregator.py              ← Finding dedup + weighted scoring
│   ├── analyzers.py               ← Static analysis runners
│   ├── validators.py              ← Finding validation + noise filter
│   ├── prompts.py                 ← All agent system prompts
│   ├── pdf_generator.py           ← PDF report (ReportLab)
│   ├── .env.example               ← Environment variable template
│   └── tests/                    ← Integration + accuracy tests
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx               ← Upload landing page
│   │   ├── dashboard/[jobId]/     ← Real-time pipeline tracker
│   │   └── api/backend/           ← Next.js → FastAPI proxy
│   ├── components/
│   │   ├── upload/DropZone.tsx
│   │   ├── pipeline/PipelineTracker.tsx
│   │   ├── score/ScoreGauge.tsx
│   │   ├── findings/FindingsPanel.tsx
│   │   └── heatmap/FileHeatmap.tsx
│   └── lib/
│       ├── api.ts                 ← Typed API client
│       └── useAnalysisStatus.ts   ← SSE pipeline hook
│
├── temp_uploads/                  ← Auto-created · gitignored
└── reports/                       ← Auto-created · gitignored
```

---

## 📊 Sample Verdict

```
╔══════════════════════════════════════════════════════════╗
║             CODESCAN  —  ANALYSIS COMPLETE               ║
╠══════════════════════════════════════════════════════════╣
║  Project   :  my_service                                 ║
║  Language  :  Python                                     ║
║  Score     :  13.5 / 100               ❌  REJECT        ║
╠══════════════════════════════════════════════════════════╣
║  🐛  Bugs              13                                ║
║  🔒  Security          12                                ║
║  ⚡  Performance        5                                ║
║  🎨  Style             11                                ║
║  ─────────────────────────────────────────               ║
║  Total findings (deduped)   38                           ║
╚══════════════════════════════════════════════════════════╝

  TOP CRITICAL FINDINGS
  ────────────────────────────────────────────────────────
  [CRITICAL]  Line  42   Hardcoded API key in variable `secret`
  [HIGH]      Line  87   Unhandled IndexError — list may be empty
  [HIGH]      Line 103   SQL query via string concat → injection risk
  [MEDIUM]    Line  56   N+1 query inside loop — use batch fetch
  [MEDIUM]    Line  99   O(n²) nested loop — replace with set lookup
```

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama` · `gemini` · `groq` · `openai` |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b-instruct-q4_K_M` | Model name for Ollama |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `GROQ_API_KEY` | — | Groq Cloud API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `MAX_FILE_SIZE_MB` | `10` | Upload size limit |
| `PLAGIARISM_THRESHOLD` | `65` | Score above which submission is blocked |
| `TEMP_UPLOAD_DIR` | `temp_uploads` | Staging directory for uploads |
| `REPORTS_DIR` | `reports` | Output directory for generated reports |

---

## 🤝 Contributing

Bug reports, new agent ideas, and language support PRs are all welcome.

```bash
# 1. Fork and clone your fork

# 2. Create a feature branch
git checkout -b feat/add-rust-support

# 3. Make your changes + add tests

# 4. Push and open a PR
git push origin feat/add-rust-support
```

> Please open an **Issue** first for significant changes so we can align before you invest time building.

---

## 📄 License

MIT © [Aadi Burande](https://github.com/AadiBurande) · [Yash Tayade](https://github.com/YashTayade)

---

<div align="center">

<br>

```
[ CODESCAN ] — because code review shouldn't require a meeting
```

*Built with ⚡ FastAPI · ▲ Next.js · 🔗 LangChain · 🟢 Ollama*

<br>

</div>

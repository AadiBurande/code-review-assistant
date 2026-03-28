<div align="center">

```
 ██████╗ ██████╗ ██████╗ ███████╗███████╗ ██████╗ █████╗ ███╗   ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗████╗  ██║
██║     ██║   ██║██║  ██║█████╗  ███████╗██║     ███████║██╔██╗ ██║
██║     ██║   ██║██║  ██║██╔══╝  ╚════██║██║     ██╔══██║██║╚██╗██║
╚██████╗╚██████╔╝██████╔╝███████╗███████║╚██████╗██║  ██║██║ ╚████║
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
```

### *Drop your code. Get a verdict. Ship with confidence.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3B82F6?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-00BFA5?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16+-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-7C3AED?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain-ai.github.io/langgraph)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> **4 AI agents. 1 quality score. Zero excuses for shipping broken code.**

</div>

---

<div align="center">

## ╔══ THE VERDICT MACHINE ══╗

</div>

**CodeScan** is a full-stack, AI-driven code review platform that runs your source code through a **multi-agent LangGraph pipeline** — analysing bugs, security vulnerabilities, performance bottlenecks, and style violations *simultaneously*, in under 60 seconds.

You get a **quality score out of 100**, a clear **ACCEPT / REJECT verdict**, line-level findings with actionable fixes, and downloadable reports in JSON, Markdown, PDF, and SARIF.

```
                   YOU SUBMIT CODE
                         │
              ┌──────────▼──────────┐
              │  🔍 CodeScan begins │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    🐛 Bug           🔒 Security     ⚡ Performance
    Agent            Agent           Agent
         └───────────────┬───────────────┘
                         ▼
                   🎨 Style Agent
                         │
                         ▼
              ┌──────────────────────┐
              │  Aggregator + Dedup  │
              └──────────┬───────────┘
                         │
              ┌──────────▼───────────┐
              │  Score · Verdict     │
              │  Findings · Reports  │
              └──────────────────────┘
```

---

## 🎯 What Gets Caught

| Agent | Detects |
|-------|---------|
| 🐛 **Bug Detection** | Logic errors · null dereferences · unhandled exceptions · off-by-one |
| 🔒 **Security Audit** | OWASP Top 10 · CVEs · injection · weak crypto · hardcoded secrets |
| ⚡ **Performance** | O(n²) loops · memory leaks · blocking I/O · unnecessary DB calls |
| 🎨 **Style & Quality** | PEP 8 · naming conventions · dead code · missing docs · complexity |

**Plus:**
- 📊 Weighted **0–100 quality score** with per-agent sub-scores
- 🧹 **Cross-agent deduplication** — no noise, no duplicate findings
- 📄 **Multi-format reports** — JSON · Markdown · PDF · SARIF
- 🌐 **Real-time dashboard** — pipeline tracker, findings panel, file risk heatmap
- 🔌 **Pluggable LLM backends** — swap providers in one line of config

---

## 🛠 Tech Stack

```
┌─────────────────────────────────┐  ┌──────────────────────────────────┐
│           BACKEND               │  │            FRONTEND              │
│─────────────────────────────────│  │──────────────────────────────────│
│  FastAPI      — REST API        │  │  Next.js 16   — App Router       │
│  LangGraph    — Agent pipeline  │  │  TypeScript   — Type safety      │
│  LangChain    — LLM abstraction │  │  Tailwind CSS — Dark-first UI    │
│  pylint       — Style checks    │  └──────────────────────────────────┘
│  flake8       — Lint engine     │
│  bandit       — Security scan   │  ┌──────────────────────────────────┐
│  radon        — Complexity      │  │          LLM PROVIDERS           │
│  semgrep      — Pattern match   │  │──────────────────────────────────│
│  ReportLab    — PDF reports     │  │  🔵 Google Gemini                │
└─────────────────────────────────┘  │  🟠 Groq                         │
                                     │  🟢 Ollama  (local, free)        │
                                     │  ⚪ OpenAI                       │
                                     └──────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **Poetry** — [install here](https://python-poetry.org/docs/#installation)
- One LLM backend: [Ollama](https://ollama.ai) (free, local) or an API key

---

### Step 1 — Clone

```bash
git clone https://github.com/AadiBurande/code-review-assistant.git
cd code-review-assistant
```

### Step 2 — Backend

```bash
cd backend
poetry install
cp .env.example .env
```

Open `.env` and configure your LLM provider:

```env
# ── Pick ONE ──────────────────────────────
LLM_PROVIDER=ollama          # free, runs locally
OLLAMA_MODEL=codellama

# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your_key

# LLM_PROVIDER=groq
# GROQ_API_KEY=your_key

# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_key
# ──────────────────────────────────────────
```

### Step 3 — Frontend

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

> Open **[http://localhost:3000](http://localhost:3000)** 🎉

> ⚠️ **Dev tip:** Always pass `--reload-exclude "temp_uploads"` in development.
> Without it, Uvicorn's file watcher detects uploaded files being written and
> **restarts the server mid-pipeline**, killing the analysis.

---

## 📡 API Reference

### `POST /analyze`

Submit a file for full multi-agent review.

**Request**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `file` | `File` | ✅ | Source file or `.zip` project |
| `language` | `string` | ✅ | e.g. `python`, `javascript` |
| `project_name` | `string` | ❌ | Label for the report (default: `unnamed_project`) |

**Response**

```jsonc
{
  "score": 13.5,
  "verdict": "REJECT",               // "ACCEPT" | "REVIEW" | "REJECT"
  "project": "my_service",
  "language": "python",
  "findings": [
    {
      "agent": "security",
      "severity": "HIGH",            // HIGH | MEDIUM | LOW | INFO
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

---

### `GET /status/{job_id}`

Poll the real-time status of a running pipeline job.

```jsonc
{
  "job_id": "abc123",
  "status": "running",              // queued | running | complete | failed
  "stage": "security_agent",
  "progress": 60,                  // 0–100
  "eta_seconds": 12
}
```

---

## 📁 Project Structure

```
code-review-assistant/
│
├── backend/
│   ├── main.py                   ← FastAPI app + all endpoints
│   ├── langgraph_pipeline.py     ← LangGraph pipeline definition
│   ├── agents.py                 ← Bug / Security / Perf / Style agents
│   ├── aggregator.py             ← Finding dedup + weighted scoring
│   ├── analyzers.py              ← Static analysis runners
│   ├── validators.py             ← Finding validation + noise filtering
│   ├── pdf_generator.py          ← PDF report generation (ReportLab)
│   ├── prompts.py                ← All agent system prompts
│   ├── .env.example              ← Environment variable template
│   └── tests/                   ← Integration + accuracy tests
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx              ← Upload landing page
│   │   ├── dashboard/[jobId]/    ← Real-time pipeline tracker
│   │   └── api/backend/          ← Next.js → FastAPI proxy
│   ├── components/
│   │   ├── upload/DropZone.tsx
│   │   ├── pipeline/PipelineTracker.tsx
│   │   ├── score/ScoreGauge.tsx
│   │   ├── findings/FindingsPanel.tsx
│   │   └── heatmap/FileHeatmap.tsx
│   └── lib/
│       ├── api.ts                ← Typed API client
│       └── useAnalysisStatus.ts  ← Long-poll hook
│
├── temp_uploads/                 ← Auto-created · gitignored
└── reports/                      ← Auto-created · gitignored
```

---

## 📊 Sample Verdict

```
╔══════════════════════════════════════════════════════╗
║           CODESCAN  —  ANALYSIS COMPLETE             ║
╠══════════════════════════════════════════════════════╣
║  Project   :  my_service                             ║
║  Language  :  Python                                 ║
║  Score     :  13.5 / 100          ❌  REJECT         ║
╠══════════════════════════════════════════════════════╣
║  🐛  Bugs           13                               ║
║  🔒  Security       12                               ║
║  ⚡  Performance     5                               ║
║  🎨  Style          11                               ║
║  ─────────────────────                               ║
║  Total (deduped)    38 findings                      ║
╚══════════════════════════════════════════════════════╝

  TOP CRITICAL FINDINGS
  ─────────────────────────────────────────────────────
  [HIGH]   Line  42  Hardcoded API key in variable `secret`
  [HIGH]   Line  87  Unhandled IndexError — list may be empty
  [HIGH]   Line 103  SQL query built via string concat → SQLi risk
  [MED]    Line  56  N+1 query inside for-loop — batch instead
  [MED]    Line  99  O(n²) nested loop — use a set for O(n)
```

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama` · `gemini` · `groq` · `openai` |
| `OLLAMA_MODEL` | `codellama` | Model name for Ollama backend |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `GROQ_API_KEY` | — | Groq API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `MAX_FILE_SIZE_MB` | `10` | Upload size limit |
| `TEMP_UPLOAD_DIR` | `temp_uploads` | Staging dir for uploads |
| `REPORTS_DIR` | `reports` | Output dir for generated reports |

---

## 🤝 Contributing

Bug reports, new agent ideas, and language support PRs are all welcome.

```bash
# 1. Fork → clone your fork
# 2. Create a feature branch
git checkout -b feat/add-javascript-support

# 3. Make your changes + add tests
# 4. Push and open a PR
git push origin feat/add-javascript-support
```

Please open an **Issue** first for significant changes so we can align before you invest time coding.

---

## 📄 License

MIT © [Aadi Burande](https://github.com/AadiBurande)

---

<div align="center">

```
[ CODESCAN ] — because code review shouldn't require a meeting
```

*Built with 🤖 LangGraph · ⚡ FastAPI · 🌐 Next.js*

</div>

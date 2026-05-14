# CodeScan – AI-Powered Multi-Agent Code Review Platform

<div align="center">

```text
 ██████╗ ██████╗ ██████╗ ███████╗███████╗ ██████╗ █████╗ ███╗   ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗████╗  ██║
██║     ██║   ██║██║  ██║█████╗  ███████╗██║     ███████║██╔██╗ ██║
██║     ██║   ██║██║  ██║██╔══╝  ╚════██║██║     ██╔══██║██║╚██╗██║
╚██████╗╚██████╔╝██████╔╝███████╗███████║╚██████╗██║  ██║██║ ╚████║
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
```

### Drop your code. Get a verdict. Ship with confidence.

![Python](https://img.shields.io/badge/Python-3.10+-3B82F6?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-00BFA5?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16+-000000?style=for-the-badge&logo=next.js&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Multi--Agent-7C3AED?style=for-the-badge&logo=chainlink&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-FF6B35?style=for-the-badge&logo=ollama&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)

</div>

---

# 📌 Overview

**CodeScan** is a full-stack AI-powered code review platform designed to analyze source code using a **parallel multi-agent architecture**.

The platform simultaneously checks for:

- 🐛 Bugs & logical issues  
- 🔒 Security vulnerabilities  
- ⚡ Performance bottlenecks  
- 🎨 Code style & maintainability issues  

Within seconds, CodeScan generates:

- ✅ A quality score out of 100  
- ✅ ACCEPT / REVIEW / REJECT verdict  
- ✅ Line-level findings with fixes  
- ✅ Reports in JSON, Markdown, PDF, and SARIF formats  

The system combines **LLM-based reasoning** with **traditional static analysis tools** to provide faster and smarter code reviews.

---

# 🚀 Key Features

| Feature | Description |
|---|---|
| ⚡ Parallel Multi-Agent Execution | All AI agents run simultaneously using `ThreadPoolExecutor` |
| 📊 Quality Scoring | Generates weighted score from 0–100 |
| 🧹 Smart Deduplication | Removes duplicate findings across agents |
| 📄 Multi-Format Reports | JSON, Markdown, PDF, and SARIF |
| 🌐 Real-Time Dashboard | Live tracking of pipeline execution |
| 🔌 Multiple LLM Providers | Supports Ollama, Gemini, Groq, and OpenAI |
| 🚫 AI/Plagiarism Detection | Detects AI-generated or plagiarized code |
| 📈 File Risk Heatmap | Visualizes risky files and modules |

---

# 🧠 System Architecture

```text
                        ┌─────────────────────┐
           YOUR CODE ──▶│   CodeScan Engine   │
                        └─────────┬───────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼

       ┌─────────────┐   ┌─────────────────┐   ┌──────────────────┐
       │ 🐛 Bug Agent │   │ 🔒 Security Agent│   │ ⚡ Performance Agent │
       └──────┬──────┘   └────────┬────────┘   └──────────┬─────────┘
              │                   │                        │
              └──────────────┬────┴──────────────┬────────┘
                             ▼                   ▼

                    ┌──────────────────────┐
                    │ 🎨 Style Agent        │
                    └──────────┬───────────┘
                               │

                    ┌──────────▼───────────┐
                    │ Aggregator + Dedup   │
                    └──────────┬───────────┘
                               │

                    ┌──────────▼───────────┐
                    │ Score + Final Verdict │
                    └──────────────────────┘
```

---

# 🎯 What CodeScan Detects

## 🐛 Bug Detection

- Logic errors  
- Null reference issues  
- Unhandled exceptions  
- Off-by-one errors  
- Type mismatches  

---

## 🔒 Security Analysis

- OWASP Top 10 vulnerabilities  
- SQL Injection  
- Command Injection  
- Hardcoded secrets  
- Weak cryptography  
- Vulnerable dependencies (CVEs)  

---

## ⚡ Performance Analysis

- O(n²) nested loops  
- Memory leaks  
- Blocking I/O calls  
- N+1 database queries  
- Unnecessary object allocations  

---

## 🎨 Style & Maintainability

- PEP 8 violations  
- Naming convention issues  
- Dead code detection  
- Missing documentation  
- Cyclomatic complexity analysis  

---

# 🛠️ Tech Stack

## Backend

| Technology | Purpose |
|---|---|
| FastAPI | REST API & SSE Streaming |
| LangChain | LLM orchestration |
| ThreadPoolExecutor | Parallel execution |
| Pydantic | Schema validation |
| Bandit | Security scanning |
| Semgrep | Pattern-based vulnerability detection |
| Radon | Complexity analysis |
| Pylint / Flake8 | Style analysis |
| ReportLab | PDF report generation |

---

## Frontend

| Technology | Purpose |
|---|---|
| Next.js 16 | Frontend framework |
| TypeScript | Type safety |
| Tailwind CSS | UI styling |
| SSE Hooks | Real-time status updates |

---

## Supported LLM Providers

| Provider | Type |
|---|---|
| Ollama | Local |
| Google Gemini | Cloud |
| Groq | Cloud |
| OpenAI | Cloud |

---

# 📂 Project Structure

```text
code-review-assistant/
│
├── backend/
│   ├── main.py
│   ├── agents.py
│   ├── langgraph_pipeline.py
│   ├── aggregator.py
│   ├── analyzers.py
│   ├── validators.py
│   ├── prompts.py
│   ├── pdf_generator.py
│   └── tests/
│
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
│
├── temp_uploads/
└── reports/
```

---

# ⚙️ Installation & Setup

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ |
| Poetry | Latest |
| LLM Backend | Ollama or API Key |

---

## 1️⃣ Clone Repository

```bash
git clone https://github.com/AadiBurande/code-review-assistant.git
cd code-review-assistant
```

---

## 2️⃣ Backend Setup

```bash
cd backend
poetry install
cp .env.example .env
```

Configure `.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder:7b-instruct-q4_K_M
```

Alternative providers:

```env
# GEMINI_API_KEY=your_key
# GROQ_API_KEY=your_key
# OPENAI_API_KEY=your_key
```

---

## 3️⃣ Frontend Setup

```bash
cd ../frontend
npm install
```

---

## 4️⃣ Run the Application

### Backend

```bash
cd backend
poetry run uvicorn main:app --reload --port 8000 --reload-exclude "temp_uploads"
```

### Frontend

```bash
cd frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

---

# 📡 API Reference

## POST `/analyze`

Analyze uploaded source code.

### Request Fields

| Field | Type | Required |
|---|---|---|
| file | File | ✅ |
| language | String | ✅ |
| project_name | String | ❌ |

---

### Sample Response

```json
{
  "job_id": "abc123",
  "score": 13.5,
  "verdict": "REJECT",
  "project": "my_service",
  "language": "python",
  "findings": [],
  "summary": {
    "bugs": 13,
    "security": 12,
    "performance": 5,
    "style": 11
  }
}
```

---

## GET `/status/{job_id}`

Fetch real-time pipeline status.

```json
{
  "status": "running",
  "stage": "security_agent",
  "progress": 60
}
```

---

# 📊 Sample Output

```text
╔══════════════════════════════════════════════════════╗
║             CODESCAN ANALYSIS COMPLETE              ║
╠══════════════════════════════════════════════════════╣
║ Project   : my_service                              ║
║ Language  : Python                                  ║
║ Score     : 13.5 / 100   ❌ REJECT                  ║
╠══════════════════════════════════════════════════════╣
║ 🐛 Bugs           : 13                              ║
║ 🔒 Security       : 12                              ║
║ ⚡ Performance    : 5                               ║
║ 🎨 Style          : 11                              ║
╚══════════════════════════════════════════════════════╝
```

---

# ⚙️ Environment Variables

| Variable | Description |
|---|---|
| LLM_PROVIDER | Selected LLM provider |
| OLLAMA_MODEL | Ollama model name |
| GEMINI_API_KEY | Gemini API key |
| GROQ_API_KEY | Groq API key |
| OPENAI_API_KEY | OpenAI API key |
| MAX_FILE_SIZE_MB | Upload size limit |
| PLAGIARISM_THRESHOLD | AI detection threshold |
| TEMP_UPLOAD_DIR | Temporary upload folder |
| REPORTS_DIR | Generated reports folder |

---

# 🤝 Contributing

Contributions are welcome.

```bash
# Create feature branch
git checkout -b feature-name

# Push changes
git push origin feature-name
```

Please open an issue before making major changes.

---

# 📄 License

MIT License

© Aadi Burande, Yash Tayade & Rutuja Deshmukh

---

<div align="center">

### CodeScan — Because Code Review Shouldn't Require a Meeting

Built with ❤️ using FastAPI, Next.js, LangChain, and Ollama.

</div>

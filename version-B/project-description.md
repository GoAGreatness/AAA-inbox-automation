# AI-Powered Email Response Generator

## Project Summary

A full-stack, locally-deployed AI assistant that generates contextual email responses directly within Microsoft Outlook. Built for a government team managing a high-volume shared inbox for a ministry-hosted AI training program. The system integrates multiple AI providers, semantic search over historical emails, and a self-improving feedback loop — all while keeping every byte of data on-machine to meet government security requirements.

---

## The Problem & Value Proposition

**Problem:** A team managing a shared inbox received hundreds of repetitive inquiries about a ministry-hosted AI training program. Staff spent significant time manually crafting similar responses to recurring questions.

**Solution:** An AI assistant that:
- Reads the selected email directly from Outlook via a one-click toolbar button
- Retrieves semantically similar past emails and their responses as context
- Generates a professional, personalized draft — auto-populated in the browser, ready to copy
- Learns from every edit and rating the user provides, improving over time

**Value Delivered:**
- Reduces response drafting time from ~5 minutes to ~30 seconds per email
- Maintains consistency in tone and accuracy across team members
- Preserves institutional knowledge — approved responses feed back into the knowledge base automatically

---

## Technical Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.12, Flask, REST API, HTTPS/SSL |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) |
| **AI Providers** | Google Gemini (gemini-2.5-flash), Groq (llama-3.3-70b-versatile), GoA LLM cluster (gpt-oss-120b), Ollama (local LLM) |
| **Vector Database** | ChromaDB with sentence-transformers (all-MiniLM-L6-v2, 384-dim embeddings) |
| **Relational Database** | SQLite |
| **Microsoft Integration** | VBA macros, Outlook COM objects, Office.js (attempted) |
| **Scripting** | PowerShell, VBA |
| **DevOps** | Self-signed SSL certificates, local HTTPS servers |

---

## Architecture Overview

```
Outlook Desktop
  └─ VBA Macro (Quick Access Toolbar button)
       └─ Reads selected email via Outlook COM
       └─ URL-encodes subject/sender/body
       └─ Opens Chrome → https://localhost:3000
                              │
                    Web App (HTML/CSS/JS)
                    Reads URL params → auto-generates
                              │
                    POST /api/generate
                              │
               Flask Backend (Python)
                    ├─ Dynamic RAG depth (LLM-driven)
                    ├─ ChromaDB semantic search
                    ├─ AI provider dispatch
                    │     ├─ Gemini (default)
                    │     ├─ Groq (w/ model fallback)
                    │     ├─ GoA LLM cluster
                    │     └─ Ollama (local)
                    └─ Response returned to frontend
                              │
                    User edits → rates → copies
                              │
                    POST /api/feedback
                    ├─ Stores feedback in SQLite
                    ├─ Indexes response in ChromaDB
                    └─ analyze_edit_diff() → LLM extracts
                         style preferences → SQLite
                         user_preferences injected
                         into every future generation
```

---

## Key Features

### 1. Multi-Provider AI with Dynamic Routing
Four AI providers integrated via a unified OpenAI-compatible pattern:
- **Google Gemini** (gemini-2.5-flash) — default, free tier, fast
- **Groq** (llama-3.3-70b-versatile) — auto-falls back to 8b-instant on token limit errors
- **GoA LLM cluster** (gpt-oss-120b) — internal government model, ~1.5s generation
- **Ollama** — fully offline local fallback (llama3.2:3b)

User selects their provider in a Settings modal. All providers route through identical dispatch logic in `ai_service.py`.

### 2. LLM-Driven Dynamic RAG Depth
Before fetching similar emails, the system first asks the LLM to assess the incoming email's complexity and decide how many past examples it needs (between 5–20). Simpler emails fetch fewer examples; multi-question or complex emails fetch more. This avoids token waste on simple requests and ensures thorough context for complex ones.

### 3. Semantic Search with ChromaDB
Historical emails and their approved responses are stored as 384-dimensional vector embeddings using `sentence-transformers`. Every generation query runs a semantic similarity search, retrieving the most contextually relevant past email–response pairs — not just keyword matches.

### 4. Automatic Style Learning from Edits
When a user edits an AI-generated response before copying, `analyze_edit_diff()` sends both versions to the LLM and asks it to extract reusable style preferences (e.g. "avoid pleasantries", "use bullet points for multiple questions"). These are stored in a `user_preferences` SQLite table and injected into every future prompt, so the AI continuously adapts to the user's writing style without manual configuration.

### 5. Annotation-Based Preference System
Users can embed `[[notes]]` directly in responses to teach the system explicit preferences. The frontend strips annotations before copying to clipboard; the backend stores them in `user_preferences`. Both the annotation system and the automatic edit-diff analysis feed the same preference pool.

### 6. Writing Style & Extra Instructions
Users can select a writing style (standard, concise, detailed, step-by-step) and provide free-text per-generation instructions (e.g. "focus on the third question only"). Both are injected into the prompt alongside RAG context and stored preferences.

### 7. VBA + Web App Workflow (Enterprise Pivot)
The original Office.js manifest add-in was blocked silently by government Exchange policies (`ReadWriteMailbox` permission denied). Pivoted to a VBA macro + standalone Chrome web app: the macro reads the selected email via Outlook COM objects, URL-encodes the data, and opens Chrome with the web app. The page auto-generates a response on load — no extra clicks.

### 8. Background Email Import
A separate VBA toolbar button hands off to a PowerShell background script (`import_sent.ps1`) that imports sent emails into ChromaDB without freezing Outlook. Windows toast notifications confirm completion. A reminder nudge fires every 10 generations to keep the knowledge base growing.

### 9. Feedback Loop & Knowledge Base Growth
Every approved response (rated ≥ threshold) is automatically re-embedded into ChromaDB. Future generations retrieve it as context, creating a compounding improvement loop — the more the system is used, the better it gets.

### 10. Stop Generation
An `AbortController` allows users to cancel in-flight generation requests. Escape key also triggers cancellation. Provider errors surface as a persistent modal with a one-click "Open Settings" shortcut rather than dumping error text into the response box.

---

## Languages & Tools

**Languages:** Python, JavaScript (ES6+), HTML5, CSS3, VBA, PowerShell, SQL

**Frameworks/Libraries:** Flask, Flask-CORS, ChromaDB, sentence-transformers, requests, python-dotenv

**AI/ML:** Google Gemini API, Groq API, GoA LLM cluster, Ollama — all via OpenAI-compatible endpoints

**Tools:** Git, SQLite, self-signed SSL (OpenSSL), Outlook COM, Chrome DevTools

**Concepts Demonstrated:** REST API design, RAG architecture, vector embeddings, semantic search, multi-provider LLM routing, prompt engineering, feedback loops, CORS, HTTPS, enterprise integration, government security constraints

---

## Technical Highlights

| Highlight | Why It Matters |
|-----------|---------------|
| **4 AI providers, unified pattern** | Demonstrates provider-agnostic design and understanding of OpenAI-compatible APIs |
| **LLM-driven RAG depth selection** | Meta-use of the LLM to optimize its own context — shows advanced prompt engineering thinking |
| **Automatic style learning from diffs** | LLM analyzes its own output vs user edits to extract preferences — no manual configuration needed |
| **ChromaDB vector search** | Semantic similarity, not keyword matching — in-demand skill for AI applications |
| **Enterprise pivot decision** | When Office.js was blocked by government policy, independently diagnosed and pivoted to VBA + web app hybrid |
| **Full-stack ownership** | Python backend, JavaScript frontend, database design, API design, VBA + PowerShell scripting |
| **Government security constraints** | Fully local deployment, HTTPS everywhere, no data leaves the machine |
| **Groq model fallback** | 413 token-limit errors on the primary model automatically retry with a smaller model |

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/generate` | Generate AI response (RAG + LLM) |
| `POST` | `/api/feedback` | Store rating, index approved response, run edit diff |
| `GET` | `/api/stats` | Usage stats (total generated, avg rating, edit rate, vector store size) |
| `GET` | `/api/similar` | Semantic search for similar past emails |
| `GET/POST` | `/api/user-config` | Read/write user profile, provider preference, signature |

---

## Roadmap (Planned)

- **Dashboard** — knowledge base health panel, preference manager, writing stats, provider status indicator
- **Testing** — pytest (backend), Jest (frontend), Cypress (E2E), wired into GitHub Actions CI
- **Containerization** — Dockerfile + Docker Compose for consistent local and deployed environments
- **Deployment** — Azure App Service (Flask), Azure Static Web Apps (frontend), SQLite → PostgreSQL, New Relic observability
- **Response streaming** — token-by-token streaming from Gemini/Groq so users see text appear in real time

---

## Resume Bullet Points

- Built a full-stack AI email automation tool (Python/Flask + JavaScript) used in a government team environment, integrating four LLM providers (Gemini, Groq, GoA cluster, Ollama) via a unified OpenAI-compatible routing layer

- Implemented RAG (Retrieval-Augmented Generation) with ChromaDB vector search and sentence-transformers embeddings across 120+ historical emails; added LLM-driven dynamic context depth selection to optimize token usage per request

- Designed an automatic style-learning system that sends AI-generated vs user-edited responses to the LLM to extract reusable writing preferences, stored and injected into every future prompt

- Navigated a real enterprise constraint — Office.js add-in blocked by government Exchange policy — by independently pivoting to a VBA macro + standalone web app architecture with zero loss of functionality

- Delivered under strict government security requirements: fully local deployment, HTTPS for all communication, no email data transmitted externally

---

## Project Complexity

For a junior full-stack developer, this project demonstrates:

| Area | Level |
|------|-------|
| **Backend (Python/Flask/REST)** | Advanced |
| **Frontend (JS/HTML/CSS)** | Intermediate–Advanced |
| **AI/ML (RAG, embeddings, prompt engineering)** | Advanced for non-ML role |
| **Enterprise Integration (Outlook, VBA, COM)** | Advanced |
| **Multi-provider API design** | Intermediate–Advanced |
| **Security & compliance awareness** | Intermediate |

---

*Last Updated: 2026-04*

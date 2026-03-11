# Version B: Project Stack & Implementation Plan
## Outlook Web Add-in with Local Backend

## KNOWN ISSUES / FUTURE IMPROVEMENTS
1. **AI Context** - ✅ Fixed - model now replies as the logged-in user (first person, with signature)
2. **Shared Mailbox** - ✅ Fixed - VBA macro reads shared mailbox emails correctly (tested 2026-02-24)
3. **UI Customization** - ✅ Partial - Auto-generate toggle added to Settings + first-run setup (2026-02-26). More options possible.
   - **TODO**: Dynamic RAG context depth — currently fixed at 15 (bumped from 12, 2026-03-11). Future: LLM-driven selection — pre-prompt asks model to assess email complexity and return a count, then that count drives `find_similar_emails()`. Planned for branch `version-b-dev--feature--information-processing`.
   - **Bug**: "Always include signature" checkbox unchecking does not persist — `use_signature` not saving correctly. Fix in dedicated branch.
   - **Bug**: Copying a response with `[[annotations]]` strips all newlines/paragraph spacing. Only the annotation text should be removed, formatting should be preserved. Fix in dedicated branch.
4. **AI Provider Options** - ✅ Complete - GoA LLM cluster integrated alongside Ollama. User selects provider in Settings modal + first-run setup. Provider stored in user config, passed to ai_service.py which branches between _call_ollama() and _call_goa(). GoA uses OpenAI-compatible API. Tested: 1.5s generation time.
   - **TODO**: Obtain GoA CA cert to replace verify=False and suppress InsecureRequestWarning
   - **TODO**: Per-model annotation preferences (currently global — both models use all annotations, which is correct default). Future: allow user to configure per-model in Settings.
   - **TODO**: Clearing user profile should cascade to user_preferences and all associated metadata. Deferred until sessions/profiles are properly implemented.
5. **Sent Email Import** - ✅ Complete - Import is a standalone VBA button (decoupled from Generate). VBA hands off to background PowerShell script (import_sent.ps1) — no Outlook freeze. Windows toast notification confirms completion. First-run setup shows import reminder before generating. Post-generate reminder fires every 10 generations. RAG badge working.
6. **Sessions & Security** - Currently single-user (config stored locally). Future: proper user sessions, credentials, and secure config storage for multi-user deployment
7. **Office.js Add-in** - Manifest installs but add-in silently fails to appear in Outlook ribbon (GoA Exchange policy suspected). Replaced by VBA macro approach.
8. **Email Thread Awareness** - VBA reads full body (includes quoted thread) but doesn't parse each message separately. Future: intelligent thread parsing.
9. **Annotation-Based Preference Learning** - ✅ Complete - Future: allow user to view and edit stored preference notes in the Settings modal. - Users add `[[notes]]` in edited responses. Frontend extracts + strips them before copying. Annotations sent to backend, stored in `user_preferences` table (deduped). AI prompt includes all stored preferences on every generation.
10. **User Documentation Page** - Static page (with dropdowns/accordions) explaining all add-in features and how to use them. Linked from the web app footer. (SWE term: User Guide / Product Docs)

## ADMIN ACCESS TODO LIST (Completed 2026-02-12)
- [x] Trust SSL cert in machine store (via .z admin account)
- [x] Start ssh-agent service + add SSH key
- [ ] Add localhost to Trusted Sites in Internet Options (if still needed)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER WORKFLOW                            │
│  1. Open email in Outlook (Desktop/Web)                     │
│  2. Click "Generate Response" button in add-in ribbon       │
│  3. Add-in task pane opens with email context               │
│  4. Review AI-generated response in task pane               │
│  5. Edit if needed, then "Insert into Reply"                │
│  6. Send email directly from Outlook                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         OUTLOOK WEB ADD-IN (Frontend - Office.js)           │
│  • HTML/CSS/JavaScript (runs inside Outlook)                │
│  • Office.js API for email access                           │
│  • Task pane UI for response display/editing                │
│  • Ribbon button for triggering                             │
│  • Can read current email, compose replies                  │
└─────────────────────────────────────────────────────────────┘
                              │
                         HTTP Requests
                    (to localhost backend)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           BACKEND (Python Flask/FastAPI)                     │
│  ┌───────────────────────────────────────────────────┐      │
│  │  API Endpoints:                                   │      │
│  │  • POST /api/analyze-email   - Analyze email     │      │
│  │  • POST /api/generate        - Generate response │      │
│  │  • POST /api/feedback        - Store feedback    │      │
│  │  • GET  /api/similar         - Find similar      │      │
│  │  • GET  /api/stats           - Usage stats       │      │
│  └───────────────────────────────────────────────────┘      │
│                                                              │
│  ┌───────────────────────────────────────────────────┐      │
│  │  AI Response Generator:                           │      │
│  │  • Analyze email content from add-in              │      │
│  │  • Search similar past emails (vector search)     │      │
│  │  • Generate contextual response                   │      │
│  │  • Return formatted response to add-in            │      │
│  └───────────────────────────────────────────────────┘      │
│                                                              │
│  ┌───────────────────────────────────────────────────┐      │
│  │  Learning Module:                                 │      │
│  │  • Store approved responses                       │      │
│  │  • Track user edits for improvement               │      │
│  │  • Build knowledge base                           │      │
│  │  • Update embeddings with new data                │      │
│  └───────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              LOCAL STORAGE (SQLite)                          │
│  • emails table (analyzed emails, metadata)                 │
│  • responses table (generated + final responses)            │
│  • feedback table (user edits, ratings)                     │
│  • templates table (common response patterns)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         VECTOR STORE (ChromaDB) - Optional                   │
│  • Embeddings of historical emails                          │
│  • Semantic search for similar emails                       │
│  • RAG (Retrieval Augmented Generation)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend (Outlook Add-in)
- **Core**: HTML5, CSS3, JavaScript (ES6+)
- **Add-in Framework**: Office.js (Microsoft Office Add-ins API)
- **UI Framework**: Bootstrap 5 or Fluent UI (Microsoft's design system)
- **HTTP Client**: Fetch API or Axios
- **Build Tool**: Webpack or Vite (optional, for bundling)
- **Dev Server**: Webpack Dev Server or similar (for local testing)

### Backend (Local Service)
- **Framework**: Flask (lightweight) or FastAPI (modern, async)
- **Language**: Python 3.10+
- **Database**: SQLite3 (built-in, no installation needed)
- **Vector Store**: ChromaDB (simple, local) or FAISS
- **AI/ML Libraries**:
  - `anthropic` Python client (for Claude API)
  - `sentence-transformers` (for embeddings)
  - `langchain` (for RAG patterns - optional)
  - OR `ollama` Python client (for local LLM alternative)
- **CORS**: Flask-CORS (to allow add-in to call local API)
- **Other**:
  - `python-dotenv` (environment variables)
  - `pydantic` (data validation)

### Add-in Deployment
- **Manifest**: XML manifest file (defines add-in metadata)
- **Hosting**: Local development server (for testing)
- **SSL**: HTTPS required (self-signed cert for local dev)
- **Testing**: Office Add-in Debugging tools

### AI Options
**SELECTED: Ollama (Local LLM)** ✅
   - Fully offline
   - Free (no API costs)
   - Supports Llama, Mistral, etc.
   - Complete data privacy
   - Good enough for POC

**Alternative: Anthropic API** (If quality needs improvement)
   - Better responses
   - Faster
   - Requires API key + costs money

---

## Project File Structure

```
version-B/
├── project-stack.md                 # This file
├── README.md                        # Quick start guide
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .env                            # Actual config (not committed)
│
├── outlook-addin/                   # Outlook Add-in (Frontend)
│   ├── manifest.xml                # Add-in manifest (required)
│   ├── assets/
│   │   ├── icon-16.png            # Add-in icons (required)
│   │   ├── icon-32.png
│   │   ├── icon-64.png
│   │   └── icon-128.png
│   │
│   ├── src/
│   │   ├── taskpane/
│   │   │   ├── taskpane.html      # Main add-in UI
│   │   │   ├── taskpane.css       # Styles
│   │   │   └── taskpane.js        # Main logic
│   │   │
│   │   ├── commands/
│   │   │   └── commands.html      # Function commands
│   │   │   └── commands.js        # Button handlers
│   │   │
│   │   └── helpers/
│   │       ├── api-client.js      # Backend API calls
│   │       ├── office-utils.js    # Office.js helpers
│   │       └── ui-helpers.js      # UI utilities
│   │
│   └── webpack.config.js           # Build configuration (optional)
│
├── backend/
│   ├── app.py                      # Main Flask/FastAPI application
│   ├── config.py                   # Configuration management
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py               # API endpoints
│   │   └── models.py               # Request/response models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py           # Response generation
│   │   ├── vector_service.py       # Vector search/embeddings
│   │   └── database_service.py     # Database operations
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text_processing.py     # Text cleaning, preprocessing
│   │   └── prompt_templates.py    # AI prompt templates
│   │
│   └── data/
│       ├── database.db             # SQLite database (generated)
│       ├── chroma_db/              # Vector store (generated)
│       └── ssl/                    # Self-signed certs for HTTPS
│
├── scripts/
│   ├── setup.sh                    # Initial setup script (Linux/Mac)
│   ├── setup.bat                   # Initial setup script (Windows)
│   ├── generate-ssl-cert.sh        # Generate self-signed SSL cert
│   ├── sideload-addin.ps1         # PowerShell script to sideload add-in
│   └── import_historical.py        # Import past emails for training
│
└── tests/
    ├── test_ai_service.py
    ├── test_api.py
    └── test_addin.html             # Manual add-in testing
```

---

## Development Stages

### **Stage 1: Environment Setup** ✅
**Goal**: Get development environment ready

**Tasks**:
- [x] Install Node.js - NOT NEEDED (using Python serve.py instead)
- [x] Install Python 3.10+ and create virtual environment
- [x] Install Python dependencies
- [x] Install Yeoman and Office Add-in generator - SKIPPED (built add-in manually)
- [x] Get Anthropic API key OR install Ollama (Ollama installed)
- [x] Generate self-signed SSL certificate for local HTTPS
- [x] Test basic Flask app (HTTP working, HTTPS next)

**Deliverable**: Working dev environment with HTTPS backend

**Completed**: 2026-02-10

**Key Commands**:
```bash
# Python setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional: Office Add-in tools
npm install -g yo generator-office

# Generate SSL cert (for local HTTPS)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout backend/data/ssl/key.pem \
  -out backend/data/ssl/cert.pem
```

---

### **Stage 2: Basic Backend API** ✅ (Complete)
**Goal**: Create local backend service for AI generation

**Tasks**:
- [x] Create Flask/FastAPI app with HTTPS
- [x] Enable CORS for localhost origins
- [x] Set up SQLite database schema
- [x] Create API endpoint: `POST /api/generate`
- [x] Implement basic Ollama integration
- [x] Test /api/generate endpoint (Status 200, response received)
- [x] Add HTTPS support (self-signed cert working)

**Deliverable**: Backend API running on https://localhost:5000 ✅

**Completed**: 2026-02-11

**Database Schema (Initial)**:
```sql
CREATE TABLE emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_email TEXT,
    sender_name TEXT,
    subject TEXT,
    body TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER,
    generated_response TEXT,
    final_response TEXT,
    was_edited BOOLEAN DEFAULT 0,
    user_rating INTEGER,  -- 1-5 stars
    edit_notes TEXT,      -- What was changed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(id)
);

CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    template_text TEXT,
    usage_count INTEGER DEFAULT 0
);
```

---

### **Stage 3: Simple Outlook Add-in Shell** ✅ (Complete)
**Goal**: Create basic add-in that can read email

**Tasks**:
- [x] Create manifest.xml with proper configuration
- [x] Create basic taskpane.html with Office.js reference
- [x] Implement email reading with Office.js
- [x] Add "Generate Response" button
- [x] Display email subject/sender in task pane
- [x] Sideload add-in in Outlook for testing
- [x] Resolve SSL cert trust (admin access obtained)

**Completed**: 2026-02-12

**Deliverable**: Add-in loads in Outlook and can read current email

**Estimated Time**: 2-3 hours

**manifest.xml Key Parts**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:type="MailApp">
  <Id>GENERATE-UNIQUE-GUID-HERE</Id>
  <Version>1.0.0.0</Version>
  <ProviderName>Your Ministry Name</ProviderName>
  <DefaultLocale>en-US</DefaultLocale>
  <DisplayName DefaultValue="Email Response Generator"/>
  <Description DefaultValue="AI-powered email response assistant"/>

  <Hosts>
    <Host Name="Mailbox"/>
  </Hosts>

  <Requirements>
    <Sets>
      <Set Name="Mailbox" MinVersion="1.1"/>
    </Sets>
  </Requirements>

  <FormSettings>
    <Form xsi:type="ItemRead">
      <DesktopSettings>
        <SourceLocation DefaultValue="https://localhost:3000/taskpane.html"/>
      </DesktopSettings>
    </Form>
  </FormSettings>
</OfficeApp>
```

---

### **Stage 4: Connect Add-in to Backend** ✅ (Complete)
**Goal**: Send email content to backend and get response

**Tasks**:
- [x] Implement API client in add-in (fetch calls)
- [x] Send email content to `POST /api/generate`
- [x] Display loading state while generating
- [x] Show generated response in task pane
- [x] Add error handling for API failures (timeout, server down, etc.)

**Completed**: 2026-02-12
- [ ] Test end-to-end: email → backend → response display

**Deliverable**: Can generate and display AI responses in add-in

**Estimated Time**: 3-4 hours

**Sample API Call in Add-in**:
```javascript
async function generateResponse() {
  try {
    // Get current email
    const item = Office.context.mailbox.item;

    const emailData = {
      subject: item.subject,
      sender: item.from.emailAddress,
      body: item.body.getAsync() // Simplified
    };

    // Show loading
    showLoading();

    // Call local backend
    const response = await fetch('https://localhost:5000/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(emailData)
    });

    const result = await response.json();
    displayResponse(result.generated_response);

  } catch (error) {
    showError(error.message);
  }
}
```

---

### **Stage 5: Response Editing & Insertion** ✅ (Complete)
**Goal**: Allow user to edit and insert response into Outlook

**Tasks**:
- [x] Add editable textarea for generated response
- [x] Implement "Insert into Reply" button
- [x] Use Office.js to create/populate reply email
- [x] Add "Copy to Clipboard" fallback option
- [x] Star rating (1-5) with feedback loop
- [x] Auto-send feedback on insert (tracks edits)
- [ ] Style UI with Bootstrap or Fluent UI (deferred - user will work on personally)
- [ ] Add keyboard shortcuts for efficiency (deferred)

**Deliverable**: Full workflow from generation to insertion working ✅

**Completed**: 2026-02-12

**Office.js Reply Insertion**:
```javascript
async function insertResponse(responseText) {
  const item = Office.context.mailbox.item;

  // Create reply
  item.displayReplyForm({
    htmlBody: responseText
  });

  // Or set reply body directly
  const reply = item.getCompose();
  reply.body.setAsync(responseText, { coercionType: Office.CoercionType.Html });
}
```

---

### **Stage 6: AI Quality Improvements** ✅ (Complete)
**Goal**: Enhance response quality with context and learning

**Tasks**:
- [x] Set up ChromaDB for vector storage
- [x] Generate embeddings for historical responses (sentence-transformers)
- [x] Implement semantic search for similar emails (vector_service.py)
- [x] Enhance prompt with retrieved context (RAG in ai_service.py)
- [x] Create response quality rating UI (1-5 stars)
- [x] Store user feedback in database
- [x] Build email import pipeline (import_emails.py - parses .msg files)
- [x] 122 historical emails imported and indexed

**Deliverable**: Better response quality using RAG ✅

**Completed**: 2026-02-20

**Enhanced Prompt Template**:
```python
PROMPT_TEMPLATE = """You are an AI assistant helping respond to emails about a ministry-hosted AI training program.

Current Email:
From: {sender_name} <{sender_email}>
Subject: {subject}
Body: {body}

Similar Past Emails and Responses:
{similar_context}

Instructions:
1. Generate a professional, helpful response
2. Address all questions in the email
3. Match the tone of past responses
4. Keep it concise (2-3 paragraphs)
5. Include relevant program details

Response:"""
```

---

### **Stage 7: Learning & Feedback Loop** ✅ (Complete)
**Goal**: System learns from user edits

**Tasks**:
- [x] Track what users change in responses (was_edited, edit_notes in feedback)
- [x] Store approved final responses as examples (auto-learn in /api/feedback)
- [x] Re-embed and update vector store with new data (approved responses → ChromaDB)
- [x] Add statistics dashboard in backend (/api/stats with vector_store_count)
- [x] get_email_by_response_id() links responses back to original emails
- [ ] Analyze common edits to identify patterns (deferred - Stage 8)
- [ ] Create simple admin panel (deferred - Stage 8)

**Deliverable**: System improves over time with usage ✅

**Completed**: 2026-02-18

**How it works**: When user submits feedback via /api/feedback, the approved response is automatically added to ChromaDB vector store. Future generations will find this response as a similar example via RAG, improving quality over time. Stats endpoint tracks total generated, avg rating, edit rate, and vector store growth.

---

### **Stage 8: VBA + Chrome Web App (Add-in Replacement)** ✅ (Complete)
**Goal**: Replace broken Office.js add-in with a reliable Outlook → Chrome workflow

**Background**: Office.js manifest add-in was abandoned after GoA Exchange policies blocked
ReadWriteMailbox permission and Outlook silently rejected manifest installs. Pivoted to
VBA macro + standalone Chrome web app approach.

**Tasks**:
- [x] Create VBA macro (scripts/email_response_macro.vba) - reads selected email, opens Chrome
- [x] Create standalone web app (outlook-addin/src/webapp/index.html + webapp.js)
- [x] Auto-generate response on Chrome page load (no extra click needed)
- [x] RAG badge showing how many past emails were used as context
- [x] Animated loading bar during generation
- [x] Copy to clipboard + star rating + feedback loop (auto-learn still works)
- [x] Add macro button to Outlook Quick Access Toolbar

**Deliverable**: Click email → click toolbar button → Chrome opens → response auto-generates ✅

**Completed**: 2026-02-24

**How it works**: VBA macro reads the selected email from Outlook via COM, URL-encodes
the subject/sender/body, and opens Chrome with the webapp URL. The webapp reads those
URL params on load and immediately calls the backend to generate a response.

---

### **Stage 9: Polish & Production Readiness** ⏳
**Goal**: Make it robust and user-friendly

**Tasks**:
- [ ] EWS / Graph API for auto-importing sent emails (EWS blocked by GoA policy - needs Graph API)
- [ ] Add comprehensive error handling
- [ ] Implement logging (backend and add-in)
- [ ] Add offline detection and graceful degradation
- [ ] Create user documentation
- [ ] Performance optimization (caching, etc.)
- [ ] Security review (API keys, CORS, etc.)
- [ ] Package for deployment (if sharing with team)

**Deliverable**: Production-ready Version B

**Estimated Time**: 4-5 hours

---

## Key Technical Decisions

### Why Outlook Web Add-in?
**Decision**: Use Office.js Web Add-in (not COM add-in)

**Reasoning**:
- ✅ Cross-platform (Windows, Mac, Web)
- ✅ Modern web technologies (familiar stack)
- ✅ Easier to develop and maintain
- ✅ Can still run with local backend
- ✅ Microsoft's recommended approach

**Trade-off**: Requires local web service (HTTPS server on localhost)

---

### Local Backend Architecture
**Decision**: Python Flask/FastAPI on localhost with HTTPS

**Why HTTPS?**
- Office Add-ins REQUIRE HTTPS (even for localhost)
- Self-signed certificate acceptable for development
- Protects API communication

**Why Python Backend?**
- Easy AI/ML library integration
- Fast development
- Good for text processing and embeddings
- Can be replaced/upgraded later

---

### AI Provider Selection
**Decision**: Start with Anthropic API, allow Ollama fallback

**Anthropic API (Claude)**:
- ✅ Better quality
- ✅ Faster responses
- ✅ Easier setup
- ✅ Cost-effective (~$0.001/email with Haiku)
- ❌ Requires internet
- ❌ Sends data externally (review privacy policy)

**Ollama (Local)**:
- ✅ Fully offline
- ✅ Free after setup
- ✅ Complete data privacy
- ❌ Slower responses
- ❌ Requires more powerful hardware
- ❌ Model quality varies

**Recommendation**: Start with Anthropic API for POC, add Ollama option if privacy is strict requirement.

---

## Environment Variables (.env)

```env
# Backend Server
FLASK_ENV=development
FLASK_HOST=localhost
FLASK_PORT=5000
SSL_CERT_PATH=./backend/data/ssl/cert.pem
SSL_KEY_PATH=./backend/data/ssl/key.pem

# CORS (allow add-in to call API)
CORS_ORIGINS=https://localhost:3000,https://outlook.office365.com

# AI Configuration
AI_PROVIDER=ollama  # Using local Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b  # or mistral:7b, llama2, etc.

# Database
DATABASE_PATH=./backend/data/database.db
VECTOR_DB_PATH=./backend/data/chroma_db

# Add-in (for manifest)
ADDIN_HOST=https://localhost:3000

# Security
SECRET_KEY=your_secret_key_here
DEBUG=True
```

---

## API Endpoints Specification

### POST /api/analyze-email
Analyze incoming email (optional, for categorization)
```json
Request:
{
  "subject": "Question about training dates",
  "sender": "john@example.com",
  "body": "When is the next session?"
}

Response:
{
  "category": "training-schedule",
  "sentiment": "neutral",
  "requires_response": true
}
```

### POST /api/generate
Generate response for an email
```json
Request:
{
  "subject": "Question about training dates",
  "sender_name": "John Doe",
  "sender_email": "john@example.com",
  "body": "When is the next training session?"
}

Response:
{
  "response_id": "uuid-here",
  "generated_response": "Dear John,\n\nThank you for your interest...",
  "confidence": 0.87,
  "similar_emails_count": 3,
  "generation_time_ms": 1234
}
```

### POST /api/feedback
Store feedback on generated response
```json
Request:
{
  "response_id": "uuid-here",
  "final_response": "Dear John,\n\n[edited version]...",
  "was_edited": true,
  "user_rating": 4,
  "edit_notes": "Added specific date"
}

Response:
{
  "success": true,
  "message": "Feedback stored"
}
```

### GET /api/similar?text=...
Find similar historical emails
```json
Response:
{
  "similar": [
    {
      "subject": "Training schedule inquiry",
      "similarity": 0.92,
      "date": "2026-01-15"
    }
  ]
}
```

### GET /api/stats
Usage statistics
```json
Response:
{
  "total_generated": 150,
  "avg_rating": 4.2,
  "edit_rate": 0.35,
  "time_saved_hours": 12.5
}
```

---

## Dependencies

### Python (requirements.txt)

```txt
# Web Framework
flask==3.0.0
flask-cors==4.0.0
# OR
# fastapi==0.109.0
# uvicorn==0.27.0

# AI/ML
ollama==0.1.6                  # Ollama client for local LLM

langchain==0.1.0               # Optional: LLM orchestration
langchain-community==0.0.10    # Community integrations
chromadb==0.4.22               # Vector database
sentence-transformers==2.2.2   # Embeddings

# Database
# (sqlite3 is built-in)

# Utilities
python-dotenv==1.0.0           # Environment variables
pydantic==2.5.0                # Data validation
beautifulsoup4==4.12.2         # HTML parsing (if needed)

# Development
pytest==7.4.3                  # Testing
black==23.12.1                 # Code formatting
```

### Node.js (package.json - Optional)

```json
{
  "name": "email-response-addin",
  "version": "1.0.0",
  "scripts": {
    "start": "webpack serve --mode development",
    "build": "webpack --mode production"
  },
  "devDependencies": {
    "webpack": "^5.89.0",
    "webpack-cli": "^5.1.4",
    "webpack-dev-server": "^4.15.1"
  }
}
```

---

## Add-in Sideloading (Testing)

### Windows Outlook Desktop:
1. Save manifest.xml to network share or OneDrive
2. Open Outlook → File → Manage Add-ins → Custom Add-ins
3. Select "Add from file" → browse to manifest.xml

### Outlook Web:
1. Settings → View all Outlook settings → Mail → Customize actions
2. Manage add-ins → My add-ins → Custom Add-ins → Add from file

### Mac Outlook:
1. Save manifest.xml locally
2. ~/Library/Containers/com.microsoft.Outlook/Data/Documents/wef/

**Note**: You'll need to trust the self-signed SSL certificate in your browser/system.

---

## Security Considerations

### Data Privacy:
- ✅ All data stored locally (SQLite)
- ✅ Backend runs on localhost only
- ⚠️ If using Anthropic API: email content sent to Claude servers
- ✅ HTTPS for all communication
- ✅ No external database

### CORS Configuration:
```python
from flask_cors import CORS

CORS(app, origins=[
    'https://localhost:3000',  # Development
    'https://outlook.office365.com',  # Outlook Web
    'https://outlook.office.com'
])
```

### API Key Security:
- ✅ Store in .env file (not committed)
- ✅ Backend validates requests
- ✅ Add rate limiting if needed

---

## Testing Strategy

### Backend Testing:
```bash
# Test API is running
curl -k https://localhost:5000/api/stats

# Test response generation
curl -k -X POST https://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"subject":"Test","sender_email":"test@example.com","body":"Test email"}'
```

### Add-in Testing:
1. Sideload manifest in Outlook
2. Open any email
3. Click add-in button
4. Verify task pane opens
5. Test generate → edit → insert workflow

### Manual Test Checklist:
- [ ] Add-in loads in Outlook
- [ ] Can read email content
- [ ] Backend API responds
- [ ] Response generates successfully
- [ ] Can edit response
- [ ] Can insert into reply
- [ ] Handles errors gracefully
- [ ] Works offline (with appropriate error)

---

## Migration Path to Production

### Phase 1: Single User POC (Current)
- Local backend on user's machine
- Sideloaded add-in
- SQLite database

### Phase 2: Team Deployment
- Deploy backend to internal server
- Centralized database
- Add-in manifest hosted internally
- Admin deployment via Microsoft 365 admin

### Phase 3: Enhanced Features
- Multi-user support
- Centralized learning
- Advanced analytics
- Integration with other systems

---

## Common Issues & Solutions

### Issue: "Add-in won't load - SSL error"
**Solution**: Trust self-signed certificate
```bash
# Windows: Add cert to Trusted Root
certutil -addstore -user Root backend/data/ssl/cert.pem

# Mac: Add to Keychain and trust
```

### Issue: "CORS error when calling API"
**Solution**:
- Ensure CORS enabled in Flask
- Check CORS_ORIGINS includes add-in URL
- Verify HTTPS (not HTTP)

### Issue: "Office.js not defined"
**Solution**:
- Ensure Office.js script tag in HTML
- Wait for Office.initialize before running code

### Issue: "Anthropic API rate limit"
**Solution**:
- Implement request throttling
- Add retry logic with exponential backoff
- Consider switching to Haiku model (higher limits)

---

## Success Metrics

### POC Success Criteria:
- [ ] Add-in loads reliably in Outlook
- [ ] Can generate contextually relevant responses
- [ ] Response quality acceptable (>80% usable without major edits)
- [ ] Workflow faster than manual responses
- [ ] Stable for 1 week of testing
- [ ] User satisfaction rating >4/5

### Performance Targets:
- Response generation: < 5 seconds
- Add-in load time: < 2 seconds
- API response time: < 3 seconds
- Backend memory usage: < 500MB

---

## Risk Mitigation

### Risk: SSL Certificate Issues
**Mitigation**:
- Provide clear setup instructions
- Include certificate trust scripts
- Test on multiple machines

### Risk: AI Quality Too Low
**Mitigation**:
- Start with Claude 3.5 Sonnet (better quality)
- Gather user feedback early
- Build good prompt templates
- Use RAG with historical context

### Risk: Add-in Compatibility Issues
**Mitigation**:
- Test on multiple Outlook versions
- Use Office.js baseline requirement set
- Provide fallback for older clients

### Risk: Backend Crashes
**Mitigation**:
- Comprehensive error handling
- Logging for debugging
- Auto-restart script
- Graceful degradation in add-in

---

## Next Immediate Steps

1. **Validate Requirements**
   - Confirm Outlook version (Desktop/Web/Mac?)
   - Get Anthropic API key (or decide on Ollama)
   - Ensure can install Python packages

2. **Set Up Environment**
   - Create Python virtual environment
   - Generate SSL certificate
   - Test basic Flask HTTPS server

3. **Start Stage 1**
   - Get "Hello World" backend running
   - Create minimal manifest.xml
   - Sideload add-in successfully

---

## Advantages of Version B (vs Version G)

| Feature | Version B (Add-in) | Version G (Web App) |
|---------|-------------------|---------------------|
| **Integration** | ✅ Native in Outlook | ❌ Separate window |
| **Email Access** | ✅ Direct via Office.js | ❌ Must fetch separately |
| **Send Email** | ✅ Direct insertion | ❌ Copy-paste required |
| **User Experience** | ✅ Seamless workflow | ⚠️ Context switching |
| **Setup Complexity** | ⚠️ Add-in + backend | ✅ Just backend |
| **Cross-platform** | ✅ Win/Mac/Web | ✅ Browser-based |
| **Email Fetching** | ✅ Not needed | ❌ Must implement |

**Bottom Line**: Version B provides better user experience but slightly more complex setup.

---

## Comparison with Version I

**Version I** (mentioned in project-breakdown.md): Hybrid approach combining Python backend with Office add-in.

**Version B** (this document): IS essentially Version I, but starting simpler:
- Same architecture
- Lighter initial implementation
- Can scale to full Version I features

---

**Current Status**: Planning Complete ✅ | Starting Development
**Next Stage**: Stage 1 - Environment Setup

---

## Confirmed Decisions (2026-02-10)

### Environment
- **Python**: 3.12.0 ✅
- **Node.js**: Not installed yet (needed for add-in later)
- **OS**: Windows (PowerShell)
- **Outlook**: Desktop version with shared mailbox access ✅

### Technical Stack
- **AI Provider**: Ollama (local LLM) - no API costs ✅
- **Email Access**: OAuth with delegated access (Option B from planning)
  - Fallback: Manual email export for testing (Option C)
- **Testing**: Mock emails/threads (no real email data initially) ✅
- **Build Order**: Backend first, then add-in ✅

### Testing Strategy
- Use mock email data for development
- Real Outlook testing later when add-in ready
- Desktop Outlook only (web version not accessible without admin)

---

---

## Data Store Cleanup (2026-03-11)
- SQLite `sent_emails` table renamed to `sent_emails_legacy` — superseded by ChromaDB. Not actively written to or read from.
- `historical_emails` stat now reads from ChromaDB collection count (was reading empty SQLite table).
- `scripts/check_sent_emails.py` updated to query ChromaDB directly — lists all emails individually with drill-down by index or ID.
- `find_similar_emails()` default bumped to `n_results=15`.

**Last Updated**: 2026-03-11
**Version**: 1.0
**Route**: B (Outlook Web Add-in with Local Backend)

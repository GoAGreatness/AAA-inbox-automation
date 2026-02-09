# Version G: Project Stack & Implementation Plan

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER WORKFLOW                            │
│  1. Open localhost:5000 in browser                          │
│  2. View fetched emails needing responses                   │
│  3. Click "Generate Response" for selected email            │
│  4. Review AI-generated response                            │
│  5. Edit if needed, then Copy to Outlook                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               FRONTEND (Web UI - Localhost)                  │
│  • HTML/CSS/JavaScript                                       │
│  • Bootstrap for responsive UI                               │
│  • Displays emails, generated responses                      │
│  • Simple, clean interface                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                         HTTP Requests
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           BACKEND (Python Flask/FastAPI)                     │
│  ┌───────────────────────────────────────────────────┐      │
│  │  API Endpoints:                                   │      │
│  │  • GET  /api/emails          - Fetch emails       │      │
│  │  • POST /api/generate        - Generate response  │      │
│  │  • POST /api/mark-sent       - Mark as handled    │      │
│  │  • GET  /api/stats           - Dashboard stats    │      │
│  └───────────────────────────────────────────────────┘      │
│                                                              │
│  ┌───────────────────────────────────────────────────┐      │
│  │  Email Service Module:                            │      │
│  │  • Connect to shared inbox                        │      │
│  │  • Fetch unread/new emails                        │      │
│  │  • Parse email content, metadata                  │      │
│  │  • Store in local database                        │      │
│  └───────────────────────────────────────────────────┘      │
│                                                              │
│  ┌───────────────────────────────────────────────────┐      │
│  │  AI Response Generator:                           │      │
│  │  • Analyze email content                          │      │
│  │  • Search similar past emails (vector search)     │      │
│  │  • Generate contextual response                   │      │
│  │  • Use local LLM or pattern matching              │      │
│  └───────────────────────────────────────────────────┘      │
│                                                              │
│  ┌───────────────────────────────────────────────────┐      │
│  │  Learning Module:                                 │      │
│  │  • Store approved responses                       │      │
│  │  • Build knowledge base                           │      │
│  │  • Improve future suggestions                     │      │
│  └───────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              LOCAL STORAGE (SQLite)                          │
│  • emails table (id, subject, from, body, timestamp, etc.)  │
│  • responses table (email_id, generated_response, etc.)     │
│  • templates table (category, template_text)                │
│  • history table (for learning from approved responses)     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         VECTOR STORE (ChromaDB/FAISS) - Optional             │
│  • Embeddings of historical emails                          │
│  • Semantic search for similar emails                       │
│  • RAG (Retrieval Augmented Generation)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              EMAIL SOURCE (Shared Inbox)                     │
│  • Microsoft Graph API (if available)                       │
│  • OR IMAP connection                                       │
│  • OR Exchange Web Services                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend
- **Framework**: Flask (lightweight) or FastAPI (modern, async)
- **Language**: Python 3.10+
- **Email Access**:
  - `msal` library (for Microsoft Graph API)
  - OR `imaplib` (for IMAP)
  - OR `exchangelib` (for Exchange)
- **Database**: SQLite3 (built-in, no installation needed)
- **Vector Store**: ChromaDB (simple, local) or FAISS
- **AI/ML Libraries**:
  - `sentence-transformers` (for embeddings)
  - `langchain` (for RAG patterns)
  - `ollama` Python client (for local LLM)
- **Other**:
  - `python-dotenv` (environment variables)
  - `pydantic` (data validation)

### Frontend
- **Core**: HTML5, CSS3, JavaScript (ES6+)
- **UI Framework**: Bootstrap 5 (responsive, clean)
- **HTTP Client**: Fetch API (native browser)
- **Optional**: Alpine.js or Vue.js (if we need reactivity)

### Local AI Options
1. **Ollama** (recommended for POC)
   - Easy to install
   - Supports Llama, Mistral, etc.
   - Good performance on consumer hardware

2. **LM Studio** (alternative)
   - GUI for model management
   - Works well on Windows

3. **Pattern-Based** (fallback)
   - Rule-based response generation
   - If AI setup is challenging initially

---

## Project File Structure

```
version-G/
├── project-stack.md                 # This file
├── README.md                        # Quick start guide
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .env                            # Actual config (not committed)
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
│   │   ├── email_service.py        # Email fetching logic
│   │   ├── ai_service.py           # Response generation
│   │   ├── vector_service.py       # Vector search/embeddings
│   │   └── database_service.py     # Database operations
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── email_parser.py         # Email parsing utilities
│   │   └── text_processing.py     # Text cleaning, preprocessing
│   │
│   └── data/
│       ├── database.db             # SQLite database (generated)
│       ├── chroma_db/              # Vector store (generated)
│       └── models/                 # Downloaded AI models
│
├── frontend/
│   ├── index.html                  # Main page
│   ├── css/
│   │   └── styles.css              # Custom styles
│   ├── js/
│   │   ├── app.js                  # Main application logic
│   │   ├── api.js                  # API client
│   │   └── ui.js                   # UI helpers
│   └── assets/
│       └── favicon.ico
│
├── scripts/
│   ├── setup.sh                    # Initial setup script (Linux/Mac)
│   ├── setup.bat                   # Initial setup script (Windows)
│   ├── import_historical.py        # Import past emails for training
│   └── test_email_connection.py   # Test email access
│
└── tests/
    ├── test_email_service.py
    ├── test_ai_service.py
    └── test_api.py
```

---

## Development Stages

### **Stage 1: Environment Setup** ⏳
**Goal**: Get development environment ready

**Tasks**:
- [ ] Create virtual environment
- [ ] Install Python dependencies
- [ ] Set up email access credentials
- [ ] Test email connection (Graph API or IMAP)
- [ ] Install Ollama and download a model (e.g., Mistral 7B)

**Deliverable**: Working dev environment with email access

**Estimated Time**: 1-2 hours

---

### **Stage 2: Basic Backend - Email Fetching** ⏳
**Goal**: Fetch and store emails from shared inbox

**Tasks**:
- [ ] Create Flask/FastAPI app skeleton
- [ ] Implement email service (Graph API or IMAP)
- [ ] Set up SQLite database schema
- [ ] Create API endpoint: `GET /api/emails`
- [ ] Test fetching and storing emails

**Deliverable**: Backend can fetch emails and store in database

**Estimated Time**: 3-4 hours

**Database Schema (Initial)**:
```sql
CREATE TABLE emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE,
    subject TEXT,
    sender_email TEXT,
    sender_name TEXT,
    body TEXT,
    received_date TIMESTAMP,
    needs_response BOOLEAN DEFAULT 1,
    response_generated BOOLEAN DEFAULT 0,
    is_handled BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER,
    generated_response TEXT,
    was_edited BOOLEAN DEFAULT 0,
    final_response TEXT,
    was_approved BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(id)
);
```

---

### **Stage 3: Basic Frontend** ⏳
**Goal**: Display emails in a web interface

**Tasks**:
- [ ] Create HTML structure for email list
- [ ] Style with Bootstrap
- [ ] Implement JavaScript to fetch and display emails
- [ ] Add basic routing/navigation
- [ ] Test end-to-end: backend → frontend

**Deliverable**: Can view fetched emails in browser at localhost:5000

**Estimated Time**: 2-3 hours

---

### **Stage 4: Simple Response Generation (Pattern-Based)** ⏳
**Goal**: Generate basic responses without AI (MVP)

**Tasks**:
- [ ] Create response templates for common questions
- [ ] Implement keyword matching
- [ ] Create API endpoint: `POST /api/generate`
- [ ] Add "Generate Response" button in UI
- [ ] Display generated response in UI

**Deliverable**: Basic response generation working (rule-based)

**Estimated Time**: 3-4 hours

**Why Start Simple?**
- Validates the workflow before adding AI complexity
- Faster to test and iterate
- Can collect templates from actual responses

---

### **Stage 5: AI-Powered Response Generation** ⏳
**Goal**: Integrate local LLM for intelligent responses

**Tasks**:
- [ ] Set up Ollama integration
- [ ] Create prompt templates for response generation
- [ ] Implement context gathering (similar past emails)
- [ ] Replace pattern-based with AI-based generation
- [ ] Add loading states in UI
- [ ] Test with various email types

**Deliverable**: AI-generated responses working

**Estimated Time**: 4-6 hours

**Sample Prompt Template**:
```
You are an assistant helping respond to emails about a ministry-hosted AI training program.

Incoming Email:
From: {sender_name} <{sender_email}>
Subject: {subject}
Body: {body}

Similar Past Exchanges:
{similar_emails_and_responses}

Generate a professional, helpful response that:
1. Addresses the sender's questions
2. Maintains a friendly, professional tone
3. Follows the style of past responses
4. Keeps it concise (2-3 paragraphs max)

Response:
```

---

### **Stage 6: Vector Search & RAG** ⏳
**Goal**: Find similar past emails for better context

**Tasks**:
- [ ] Set up ChromaDB
- [ ] Generate embeddings for historical emails
- [ ] Implement semantic search
- [ ] Integrate with response generation
- [ ] Add "Similar Emails" view in UI

**Deliverable**: Response generation uses relevant historical context

**Estimated Time**: 3-4 hours

---

### **Stage 7: Learning & Feedback Loop** ⏳
**Goal**: Improve responses based on user edits

**Tasks**:
- [ ] Add "Edit Response" functionality in UI
- [ ] Track what users change in responses
- [ ] Store approved responses as training examples
- [ ] Re-train/update embeddings with new data
- [ ] Add statistics/analytics dashboard

**Deliverable**: System learns from user feedback

**Estimated Time**: 4-5 hours

---

### **Stage 8: Polish & Production Readiness** ⏳
**Goal**: Make it robust and user-friendly

**Tasks**:
- [ ] Add error handling throughout
- [ ] Implement logging
- [ ] Add email refresh/sync functionality
- [ ] Create user documentation
- [ ] Add configuration UI (settings page)
- [ ] Performance optimization
- [ ] Security review (no data leaks)

**Deliverable**: Production-ready Version G

**Estimated Time**: 5-6 hours

---

## Key Technical Decisions

### Email Access Method
**Decision Point**: How to connect to shared inbox?

**Options**:
1. **Microsoft Graph API** (Recommended)
   - Modern, well-documented
   - Requires Azure app registration
   - Best for Office 365/Exchange Online

2. **IMAP**
   - Universal, works with most email providers
   - Simpler setup (just username/password)
   - Good fallback option

3. **Exchange Web Services (EWS)**
   - Older technology
   - Being deprecated by Microsoft
   - Use only if Graph API not available

**We'll implement**: Start with what you have access to, design for easy switching

---

### Local LLM Selection
**Decision Point**: Which local model to use?

**Recommended Models** (via Ollama):
1. **Mistral 7B** - Good balance of quality and speed
2. **Llama 3 8B** - Strong performance, slightly slower
3. **Phi-3 Mini** - Very fast, good for simple responses

**Fallback**: Rule-based templates if AI setup issues

---

### Frontend Framework
**Decision Point**: Plain JavaScript vs framework?

**We'll use**: Plain JavaScript + Bootstrap
- Keeps it simple
- Easy to understand and modify
- Sufficient for this use case
- Easier transition to Version I (Outlook add-in)

---

## Environment Variables (.env)

```env
# Email Configuration
EMAIL_TYPE=graph  # Options: graph, imap, ews
EMAIL_ADDRESS=shared-inbox@ministry.gov
EMAIL_PASSWORD=your_password  # For IMAP

# Microsoft Graph (if using)
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# Application
FLASK_ENV=development
FLASK_PORT=5000
DEBUG=True

# AI Configuration
AI_PROVIDER=ollama  # Options: ollama, pattern-based
OLLAMA_MODEL=mistral:7b
OLLAMA_URL=http://localhost:11434

# Database
DATABASE_PATH=./backend/data/database.db
VECTOR_DB_PATH=./backend/data/chroma_db

# Security
SECRET_KEY=your_secret_key_here
```

---

## API Endpoints Specification

### GET /api/emails
Fetch emails needing responses
```json
Response:
{
  "emails": [
    {
      "id": 1,
      "subject": "Question about AI training dates",
      "sender_name": "John Doe",
      "sender_email": "john@example.com",
      "body": "When is the next training session?",
      "received_date": "2026-02-09T10:30:00Z",
      "needs_response": true,
      "response_generated": false
    }
  ],
  "total": 5,
  "unhandled": 5
}
```

### POST /api/generate
Generate response for an email
```json
Request:
{
  "email_id": 1
}

Response:
{
  "response_id": 1,
  "generated_response": "Dear John,\n\nThank you for your interest...",
  "confidence": 0.87,
  "similar_emails": [
    {"subject": "Training schedule inquiry", "relevance": 0.92}
  ]
}
```

### POST /api/mark-sent
Mark email as handled
```json
Request:
{
  "email_id": 1,
  "response_id": 1,
  "final_response": "Dear John,\n\n[edited version]...",
  "was_edited": true
}

Response:
{
  "success": true,
  "message": "Email marked as handled"
}
```

### GET /api/stats
Dashboard statistics
```json
Response:
{
  "total_emails": 150,
  "handled": 145,
  "pending": 5,
  "response_quality_avg": 4.2,
  "time_saved_hours": 12.5
}
```

---

## Dependencies (requirements.txt)

```txt
# Web Framework
flask==3.0.0
flask-cors==4.0.0

# Email Libraries
msal==1.26.0                    # Microsoft Graph authentication
requests==2.31.0                # HTTP requests
exchangelib==5.1.0              # For EWS (if needed)

# Database
SQLAlchemy==2.0.25              # Optional ORM (or use sqlite3 directly)

# AI/ML
langchain==0.1.0                # LLM orchestration
langchain-community==0.0.10     # Community integrations
chromadb==0.4.22                # Vector database
sentence-transformers==2.2.2    # Embeddings
ollama==0.1.6                   # Ollama client

# Utilities
python-dotenv==1.0.0            # Environment variables
pydantic==2.5.0                 # Data validation
python-dateutil==2.8.2          # Date parsing
beautifulsoup4==4.12.2          # HTML parsing (for emails)
lxml==5.1.0                     # XML parsing

# Development
pytest==7.4.3                   # Testing
black==23.12.1                  # Code formatting
```

---

## Migration Path to Version I

**Design Considerations**:
- Keep backend API generic (not tied to web UI)
- Use RESTful endpoints (easy to call from Outlook add-in)
- Separate business logic from presentation
- Document API clearly

**When Moving to Version I**:
1. Keep entire backend as-is
2. Replace frontend/ with Outlook add-in
3. Add-in calls same API endpoints
4. Minimal backend changes needed

**Shared Components**:
- ✅ Email service
- ✅ AI service
- ✅ Database
- ✅ Vector store
- ✅ API endpoints

**Version I Only Adds**:
- Office.js add-in manifest
- Add-in HTML/JS (replaces web UI)
- Direct email sending (no copy-paste)

---

## Success Metrics

### POC Success Criteria:
- [ ] Can fetch emails from shared inbox
- [ ] Can generate contextually relevant responses
- [ ] Response quality acceptable (>80% usable without major edits)
- [ ] Workflow is faster than manual responses
- [ ] System is stable for 1 week of testing

### Performance Targets:
- Email fetch: < 5 seconds for 50 emails
- Response generation: < 10 seconds per email
- UI responsiveness: < 1 second for most actions

---

## Risk Mitigation

### Risk: Email Access Issues
**Mitigation**:
- Test connection early (Stage 1)
- Support multiple access methods (Graph, IMAP)
- Have IT support contact ready

### Risk: AI Quality Too Low
**Mitigation**:
- Start with pattern-based (Stage 4)
- Test multiple models
- Allow manual templates as fallback

### Risk: Performance Issues
**Mitigation**:
- Start with small dataset
- Implement caching
- Use smaller AI models if needed

### Risk: Security Concerns
**Mitigation**:
- All data stays local
- No external API calls (except to local Ollama)
- Encrypt sensitive data at rest
- Clear audit trail

---

## Next Immediate Steps

1. **Validate Email Access**
   - Determine which protocol (Graph API, IMAP, EWS)
   - Get credentials/permissions
   - Test connection with simple script

2. **Set Up Environment**
   - Create Python virtual environment
   - Install Ollama
   - Download AI model

3. **Start Stage 1**
   - Create basic project structure
   - Get first email fetched and displayed

---

**Current Status**: Planning Complete ✅
**Next Stage**: Stage 1 - Environment Setup
**Ready to Start**: Awaiting user confirmation to proceed

---

**Last Updated**: 2026-02-09
**Version**: 1.0

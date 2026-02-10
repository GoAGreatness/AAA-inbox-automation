# Version B: Outlook Add-in Email Response Generator

Outlook Desktop Add-in with local Python backend for AI-powered email response generation.

## Quick Start

### 1. Backend Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env

# Install and start Ollama (if not installed)
# Download from: https://ollama.ai
ollama serve
ollama pull llama3.2:3b

# Run backend
python backend/app.py
```

### 2. Add-in Setup (later)
- Node.js installation required
- Details in version-stack.md

## Project Structure
- `backend/` - Python Flask API
- `outlook-addin/` - Office.js add-in
- `scripts/` - Setup and utility scripts
- `tests/` - Test files

## Documentation
See `version-stack.md` for complete technical documentation.

## Status
- ✅ Planning complete
- 🔨 Backend development in progress
- ⏳ Add-in pending

**Last Updated**: 2026-02-10

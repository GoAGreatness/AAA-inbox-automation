FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching — only reinstalls if requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Data directory must exist for SQLite + ChromaDB (actual data is volume-mounted at runtime)
RUN mkdir -p backend/data/ssl backend/data/chroma_db

EXPOSE 5000

# Run from inside backend/ so relative service imports resolve correctly
WORKDIR /app/backend
CMD ["python", "app.py"]

#!/bin/bash
# Development server startup script

set -e

echo "🚀 Starting Local Knowledge Base (Development Mode)"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if database is initialized
if [ ! -f "data/knowledge.db" ]; then
    echo "🗄️  Initializing database..."
    python -m app.cli init
fi

# Run FastAPI server (when implemented)
echo "⚠️  Web server not yet implemented (Phase 1)"
echo "💡 Use CLI for now: python -m app.cli --help"

# For future:
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

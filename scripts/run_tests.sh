#!/bin/bash
# Test runner script

set -e

echo "🧪 Running Local Knowledge Base Tests"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run pytest with coverage
pytest -v \
    --cov=app \
    --cov-report=html \
    --cov-report=term \
    --cov-report=term-missing \
    "$@"

echo ""
echo "✅ Tests complete!"
echo "📊 Coverage report: htmlcov/index.html"

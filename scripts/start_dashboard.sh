#!/usr/bin/env bash
# ==============================================================================
# UniHack Industrial Product Intelligence & PIM Dashboard Launcher
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

echo "=============================================================================="
echo "🚀 Starting UniHack Industrial Product Intelligence & PIM Dashboard"
echo "=============================================================================="

# 1. Check Python Virtual Environment
if [ -d ".venv" ]; then
    PYTHON_BIN=".venv/bin/python"
    UVICORN_BIN=".venv/bin/uvicorn"
else
    PYTHON_BIN="python3"
    UVICORN_BIN="uvicorn"
fi

# 2. Verify / Build Frontend if dist does not exist
if [ ! -d "src/frontend/dist" ]; then
    echo "📦 Building React + TypeScript frontend bundle..."
    cd src/frontend
    npm install --silent
    npm run build
    cd "$PROJECT_ROOT"
fi

# 3. Print Dashboard URLs
echo ""
echo "🌐 Web Dashboard:       http://localhost:${PORT}"
echo "📚 OpenAPI Swagger UI:  http://localhost:${PORT}/docs"
echo "🔍 Health Check API:    http://localhost:${PORT}/api/health"
echo "📊 Catalog Products:    http://localhost:${PORT}/api/products"
echo ""
echo "✨ Pre-loading 1,000 catalog items in-memory..."

# 4. Launch FastAPI Uvicorn Server (Serving REST API + SPA Frontend)
exec $PYTHON_BIN -m uvicorn src.backend.main:app --host "$HOST" --port "$PORT"

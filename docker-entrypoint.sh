#!/bin/sh
set -e

echo "========================================="
echo "ElderGen Container Starting..."
echo "========================================="
echo "Working directory: $(pwd)"
echo "Python version: $(python --version 2>&1)"
echo "PORT: ${PORT:-8000}"
echo "========================================="

# Test import to catch errors early
echo "Testing Python imports..."
python -c "from app.config import settings; print('Config loaded OK')" || {
    echo "❌ Failed to import config"
    exit 1
}

echo "Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

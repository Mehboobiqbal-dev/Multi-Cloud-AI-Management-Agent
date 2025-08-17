#!/bin/bash

# Railway-specific start script
echo "🚀 Starting Multi-Cloud AI Management Backend on Railway..."

# Set production environment
export ENVIRONMENT=production
export DEBUG=false
export RELOAD=false

# Wait for database to be ready (Railway handles this automatically)
echo "⏳ Waiting for database connection..."
sleep 2

# Validate required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL is not set"
    exit 1
fi

if [ -z "$SESSION_SECRET" ]; then
    echo "❌ ERROR: SESSION_SECRET is not set"
    exit 1
fi

if [ -z "$GEMINI_API_KEYS" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ ERROR: Neither GEMINI_API_KEYS nor GEMINI_API_KEY is set"
    exit 1
fi

echo "✅ Environment validation passed"

# Run database initialization script
echo "⚙️ Initializing database..."
python init_db_script.py

# Start the application with production settings
echo "📡 Starting FastAPI server on port ${PORT:-10000}..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --workers ${WORKERS:-2} --no-reload --log-level info
#!/bin/bash

# Railway-specific start script
echo "🚀 Starting Multi-Cloud AI Management Backend on Railway..."

# Wait for database to be ready (Railway handles this automatically)
echo "⏳ Waiting for database connection..."

# Start the application
echo "📡 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 
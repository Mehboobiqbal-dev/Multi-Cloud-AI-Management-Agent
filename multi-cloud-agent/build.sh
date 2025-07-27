#!/bin/bash

# Production build script for Multi-Cloud AI Management Agent

echo "🚀 Starting production build..."

# Build backend
echo "📦 Building backend..."
cd backend
docker build -t multi-cloud-backend .
cd ..

# Build frontend
echo "📦 Building frontend..."
cd frontend
docker build -t multi-cloud-frontend .
cd ..

echo "✅ Build completed successfully!"

# Optional: Run with docker-compose
if [ "$1" = "--run" ]; then
    echo "🐳 Starting services with docker-compose..."
    docker-compose up -d
fi 
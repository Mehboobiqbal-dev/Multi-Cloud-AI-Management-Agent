#!/bin/bash

# Start backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to start
sleep 5

# Serve frontend
cd ../frontend
npx http-server build -p 3000

#!/bin/bash

# Start backend with proper configuration for Railway
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1

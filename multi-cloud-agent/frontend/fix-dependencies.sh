#!/bin/bash

echo "🔧 Fixing frontend dependencies..."

# Remove node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Clear npm cache
npm cache clean --force

# Install dependencies
npm install

echo "✅ Dependencies fixed! You can now run 'npm start'" 
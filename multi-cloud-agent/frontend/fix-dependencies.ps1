# Fix frontend dependencies for Windows

Write-Host "🔧 Fixing frontend dependencies..." -ForegroundColor Yellow

# Remove node_modules and package-lock.json
if (Test-Path "node_modules") {
    Remove-Item -Recurse -Force "node_modules"
    Write-Host "Removed node_modules" -ForegroundColor Green
}

if (Test-Path "package-lock.json") {
    Remove-Item "package-lock.json"
    Write-Host "Removed package-lock.json" -ForegroundColor Green
}

# Clear npm cache
npm cache clean --force

# Install dependencies
npm install

Write-Host "✅ Dependencies fixed! You can now run 'npm start'" -ForegroundColor Green 
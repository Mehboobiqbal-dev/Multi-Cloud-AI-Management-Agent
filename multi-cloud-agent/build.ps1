# Production build script for Multi-Cloud AI Management Agent (Windows)

Write-Host "🚀 Starting production build..." -ForegroundColor Green

# Build backend
Write-Host "📦 Building backend..." -ForegroundColor Yellow
Set-Location backend
docker build -t multi-cloud-backend .
Set-Location ..

# Build frontend
Write-Host "📦 Building frontend..." -ForegroundColor Yellow
Set-Location frontend
docker build -t multi-cloud-frontend .
Set-Location ..

Write-Host "✅ Build completed successfully!" -ForegroundColor Green

# Optional: Run with docker-compose
if ($args[0] -eq "--run") {
    Write-Host "🐳 Starting services with docker-compose..." -ForegroundColor Blue
    docker-compose up -d
} 
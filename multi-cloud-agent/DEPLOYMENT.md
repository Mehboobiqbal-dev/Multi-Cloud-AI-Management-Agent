# Multi-Cloud AI Management Agent - Deployment Guide

## Overview

This guide covers deploying the Multi-Cloud AI Management Agent to Railway (backend) and Vercel (frontend).

## Architecture

- **Backend**: FastAPI application deployed on Railway with PostgreSQL
- **Frontend**: React application deployed on Vercel
- **Database**: PostgreSQL (Railway managed)

## Railway Backend Deployment

### 1. Prerequisites
- Railway account
- PostgreSQL database provisioned on Railway

### 2. Environment Variables
Set these in Railway dashboard:

```bash
# Database (Railway will provide this)
DATABASE_URL=postgresql://...

# Security
SESSION_SECRET=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Gemini AI
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL_NAME=gemini-pro

# Environment
ENVIRONMENT=production
FORCE_HTTPS=true

# CORS (optional)
ALLOW_ALL_ORIGINS=false
```

### 3. Deployment Steps
1. Connect your GitHub repository to Railway
2. Select the `multi-cloud-agent` directory
3. Railway will automatically detect the Dockerfile in `backend/`
4. Set environment variables in Railway dashboard
5. Deploy

## Vercel Frontend Deployment

### 1. Prerequisites
- Vercel account
- Railway backend URL

### 2. Environment Variables
Set these in Vercel dashboard:

```bash
REACT_APP_API_URL=https://your-railway-backend-url.up.railway.app
REACT_APP_SUPABASE_URL=your-supabase-url
REACT_APP_SUPABASE_ANON_KEY=your-supabase-anon-key
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id
```

### 3. Deployment Steps
1. Connect your GitHub repository to Vercel
2. Set root directory to `multi-cloud-agent/frontend`
3. Set build command: `npm run build`
4. Set output directory: `build`
5. Set environment variables in Vercel dashboard
6. Deploy

## Local Development

### 1. Clone and Setup
```bash
git clone <your-repo>
cd multi-cloud-agent
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp env.example .env
# Edit .env with your values
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cp env.example .env.local
# Edit .env.local with your values
npm start
```

### 4. Docker Compose (Full Stack)
```bash
# From multi-cloud-agent directory
docker-compose up -d
```

## Health Checks

### Backend Health Endpoints
- `GET /healthz` - Basic health check
- `GET /readyz` - Readiness check

### Frontend Health
- Vercel automatically provides health checks
- Frontend serves static files via CDN

## Troubleshooting

### CORS Issues
1. Ensure backend CORS origins include your Vercel domain
2. Check that `ALLOW_ALL_ORIGINS` is set correctly
3. Verify environment variables are set in both Railway and Vercel

### Database Connection Issues
1. Verify `DATABASE_URL` is set correctly in Railway
2. Check that PostgreSQL is provisioned and running
3. Ensure database migrations have run

### Build Issues
1. Check that all dependencies are in `requirements.txt` (backend)
2. Verify `package.json` has all required dependencies (frontend)
3. Ensure build scripts are correct

### Environment Variables
1. Double-check all required variables are set
2. Verify variable names match exactly (case-sensitive)
3. Restart services after changing environment variables

## Monitoring

### Railway Backend
- Use Railway dashboard for logs and metrics
- Monitor `/healthz` endpoint for uptime
- Check database connection status

### Vercel Frontend
- Use Vercel dashboard for analytics and logs
- Monitor build status and deployment history
- Check for any build errors

## Security Considerations

1. **Environment Variables**: Never commit secrets to version control
2. **CORS**: Configure origins properly for production
3. **HTTPS**: Enable HTTPS enforcement in production
4. **Database**: Use strong passwords and connection strings
5. **API Keys**: Rotate keys regularly and use least privilege

## Performance Optimization

### Backend
- Use connection pooling for database
- Implement caching where appropriate
- Monitor memory usage and scale accordingly

### Frontend
- Optimize bundle size with code splitting
- Use CDN for static assets
- Implement proper caching headers

## Support

For deployment issues:
1. Check Railway and Vercel documentation
2. Review logs in respective dashboards
3. Verify environment variables are set correctly
4. Test locally before deploying 
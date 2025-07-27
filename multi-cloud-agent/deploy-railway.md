# Railway Deployment Guide - Fix CORS Issues

## Immediate Steps to Fix CORS

### 1. Commit and Push Changes
```bash
git add .
git commit -m "Fix CORS configuration for Railway deployment"
git push origin main
```

### 2. Railway Dashboard Steps
1. Go to your Railway dashboard
2. Select your backend project
3. Go to "Variables" tab
4. Add/Update these environment variables:

```bash
ENVIRONMENT=production
ALLOW_ALL_ORIGINS=true
FORCE_HTTPS=true
```

### 3. Trigger Redeploy
1. In Railway dashboard, go to "Deployments" tab
2. Click "Deploy" to trigger a new deployment
3. Wait for deployment to complete (usually 2-3 minutes)

### 4. Verify Deployment
1. Check the deployment logs in Railway
2. Test the health endpoint: `https://your-railway-url.up.railway.app/healthz`
3. Should return: `{"status": "ok"}`

### 5. Test CORS
After deployment, test if CORS is working:
1. Open browser developer tools
2. Go to your Vercel frontend
3. Try to sign up/login
4. Check Network tab for CORS errors

## Alternative: Quick Fix

If you want to test immediately, you can temporarily set:
```bash
ALLOW_ALL_ORIGINS=true
ENVIRONMENT=development
```

This will allow all origins and should fix the CORS issue immediately.

## Troubleshooting

### If CORS still fails:
1. Check Railway logs for any startup errors
2. Verify environment variables are set correctly
3. Wait 2-3 minutes for changes to propagate
4. Clear browser cache and try again

### If backend won't start:
1. Check Railway logs for Python errors
2. Verify all required environment variables are set
3. Check if DATABASE_URL is correct

## Environment Variables Checklist

Make sure these are set in Railway:
- ✅ `DATABASE_URL` (Railway provides this)
- ✅ `SESSION_SECRET` (your secret key)
- ✅ `GOOGLE_CLIENT_ID` (your Google OAuth client ID)
- ✅ `GOOGLE_CLIENT_SECRET` (your Google OAuth client secret)
- ✅ `GEMINI_API_KEY` (your Gemini API key)
- ✅ `ENVIRONMENT=production`
- ✅ `ALLOW_ALL_ORIGINS=true` (temporarily for testing)
- ✅ `FORCE_HTTPS=true` 
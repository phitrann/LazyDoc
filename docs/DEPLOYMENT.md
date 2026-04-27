# Deployment Guide

This document covers deploying LazyDoc to Vercel, which hosts both the Next.js frontend and FastAPI backend.

## Architecture Overview

LazyDoc is a full-stack application deployed as two separate Vercel projects:

- **Frontend**: Next.js React application (JavaScript/TypeScript)
- **Backend**: FastAPI Python application

The frontend makes HTTP requests to the backend via the `BACKEND_INTERNAL_URL` environment variable.

## Quick Start: Deploy from Scratch

This section walks you through deploying LazyDoc to Vercel for the first time. Estimated time: **10-15 minutes**.

### Step 1: Prerequisites

Before starting, ensure you have:

- **Vercel CLI**: Install from https://vercel.com/download
- **Node.js 18+**: Required for the Vercel CLI and frontend builds
- **Python 3.9+**: Required for backend dependencies
- **Git**: Version control (the repo should already be initialized)
- **GitHub account** (optional): For pushing code to GitHub
- **Vercel account**: Sign up free at https://vercel.com

Verify installations:
```bash
vercel --version          # Should show Vercel CLI version
node --version            # Should show Node.js 18+
python --version          # Should show Python 3.9+
```

### Step 2: Authenticate with Vercel CLI

```bash
vercel login
```

This opens a browser window to authenticate. After completing login, the CLI will be connected to your Vercel account.

**Verify authentication:**
```bash
vercel whoami
# Output: your-vercel-username (or your organization)
```

### Step 3: Check Vercel Teams

If you belong to multiple teams, identify which team to deploy to:

```bash
vercel teams list
# Output: Lists your available teams with slugs
```

Take note of the team slug (e.g., `foxxyhcmus-projects`). Use `--scope <team-slug>` in all subsequent commands if deploying to a team rather than your personal account.

### Step 4: Prepare the Repository

Clone or navigate to the LazyDoc repository:

```bash
cd /path/to/LazyDoc
git status  # Verify you're in the right directory
```

The repository should have this structure:
```
LazyDoc/
├── frontend/
│   ├── package.json
│   ├── next.config.mjs
│   └── src/
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   └── main.py
│   └── tests/
└── docs/
```

### Step 5: Deploy Backend First

The backend must be deployed before the frontend, since the frontend needs the backend URL.

```bash
# Navigate to backend directory
cd backend

# Deploy to Vercel
vercel deploy --prod -y --no-wait --scope foxxyhcmus-projects
```

**Expected output:**
```
Linked to foxxyhcmus-projects/backend (created .vercel and added it to .gitignore)
Deploying foxxyhcmus-projects/backend
Inspect: https://vercel.com/foxxyhcmus-projects/backend/xxxxxx [xsx]
Production: https://backend-xxxxxx-foxxyhcmus-projects.vercel.app [xs]
https://backend-xxxxxx-foxxyhcmus-projects.vercel.appNote: Deployment is still processing...
```

**Save the backend URL** (e.g., `https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app`). You'll need it in the next steps.

### Step 6: Wait for Backend to Build

Backend deployments typically take 30-60 seconds to complete. Wait before proceeding:

```bash
sleep 40

# Verify backend is ready
vercel inspect https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app --format json | jq '.readyState'
# Should output: "READY"
```

If not ready, wait another 20 seconds and check again.

### Step 7: Configure Frontend Environment Variable

The frontend needs to know where to reach the backend. Set the `BACKEND_INTERNAL_URL` environment variable:

```bash
cd ../frontend

# Replace the URL with your backend URL from Step 5
BACKEND_URL="https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app"

# Add to Vercel project
echo "$BACKEND_URL" | vercel env add BACKEND_INTERNAL_URL --scope foxxyhcmus-projects production
```

**Verification:**
```bash
vercel env ls --scope foxxyhcmus-projects
# Should list BACKEND_INTERNAL_URL with your backend URL
```

### Step 8: Deploy Frontend

Now deploy the frontend with the backend URL configured:

```bash
# In the frontend directory
vercel deploy --prod -y --no-wait --scope foxxyhcmus-projects
```

**Expected output:**
```
Deploying foxxyhcmus-projects/frontend
Inspect: https://vercel.com/foxxyhcmus-projects/frontend/yyyyyy [xs]
Production: https://frontend-yyyyyy-foxxyhcmus-projects.vercel.app [xs]
https://frontend-yyyyyy-foxxyhcmus-projects.vercel.appNote: Deployment is still processing...
```

**Save the frontend URL** for the next step.

### Step 9: Wait for Frontend to Build

Frontend deployments typically take 20-40 seconds. Wait for completion:

```bash
sleep 40

# Verify frontend is ready
vercel inspect https://frontend-yyyyyy-foxxyhcmus-projects.vercel.app --format json | jq '.readyState'
# Should output: "READY"
```

### Step 10: Verify Deployments

Check that both deployments are operational:

```bash
# Check backend health
curl -s https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app/docs 2>&1 | head -20
# Should return HTML documentation page (or 200 OK)

# Check frontend can reach backend
# (May show auth page if deployment protection is enabled)
curl -s https://frontend-yyyyyy-foxxyhcmus-projects.vercel.app/ 2>&1 | grep -o "Authentication Required\|GitHub URL" | head -1
```

### Step 11: Access Your Deployment

Navigate to your frontend URL:

```
https://frontend-yyyyyy-foxxyhcmus-projects.vercel.app
```

**If you see "Authentication Required":**

The Vercel team has deployment protection enabled. You have three options:

**Option A: Disable Deployment Protection (Recommended)**
1. Go to https://vercel.com/foxxyhcmus-projects/settings/deploymentProtection
2. Disable the toggle
3. Wait ~2 minutes
4. Refresh the page

**Option B: Use CLI to Access**
```bash
vercel curl https://frontend-yyyyyy-foxxyhcmus-projects.vercel.app/
```

**Option C: Use Bypass Token**
Ask your team admin for the deployment protection bypass token, then append it to the URL as a query parameter.

### Step 12: Test the Application

Once you can access the frontend:

1. **Enter a GitHub repository URL** in the input field (e.g., `https://github.com/vercel/next.js`)
2. **Click "Generate Report"**
3. **Wait for analysis** (30-90 seconds depending on repo size)
4. **Verify the report generates** with overview, structure, activity, and insights

If you see "Backend service is unavailable", check:
- Backend is deployed and ready (Step 6)
- `BACKEND_INTERNAL_URL` is set correctly on frontend (Step 7)
- Frontend was redeployed after setting env var (Step 8)

### Step 13: (Optional) Deploy via Git Push

Set up automatic deployments from GitHub:

1. **Connect Vercel to GitHub**:
   ```bash
   vercel link --repo --scope foxxyhcmus-projects
   ```

2. **Verify connection**:
   - Frontend and backend should appear in Vercel dashboard
   - New commits to `main` will automatically trigger deployments

3. **Test by pushing code**:
   ```bash
   git add .
   git commit -m "test: automatic deployment"
   git push origin main
   ```

---

## Complete Deployment Command Summary

Here's the entire deployment from scratch as a single sequence:

```bash
# 1. Navigate to repo
cd /path/to/LazyDoc

# 2. Login to Vercel
vercel login

# 3. Deploy backend
cd backend
BACKEND_URL=$(vercel deploy --prod -y --no-wait --scope foxxyhcmus-projects 2>&1 | grep "Production:" | awk '{print $NF}' | tr -d '\n')
echo "Backend URL: $BACKEND_URL"

# 4. Wait for backend to build
sleep 45

# 5. Deploy frontend with backend URL
cd ../frontend
echo "$BACKEND_URL" | vercel env add BACKEND_INTERNAL_URL --scope foxxyhcmus-projects production
vercel deploy --prod -y --no-wait --scope foxxyhcmus-projects
FRONTEND_URL=$(vercel list --json --scope foxxyhcmus-projects | jq -r '.deployments[0].url')
echo "Frontend URL: $FRONTEND_URL"

# 6. Wait for frontend to build
sleep 40

# 7. Verify both are ready
echo "Backend status:"
vercel inspect $BACKEND_URL --format json | jq '.readyState'
echo "Frontend status:"
vercel inspect $FRONTEND_URL --format json | jq '.readyState'

# 8. Access application
echo "Your app is ready at: https://$FRONTEND_URL"
```

---

## Deployment URLs



### Production Deployments

| Component | Project Name | URL | Status |
|-----------|--------------|-----|--------|
| Frontend | `frontend` | `https://frontend-5qv42b9ls-foxxyhcmus-projects.vercel.app` | ✓ READY |
| Backend | `backend` | `https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app` | ✓ READY |

### Legacy Deployments

The original `lazydoc` project on Vercel is not actively used. The split frontend/backend deployment is the current architecture.

## Environment Variables

### Frontend Project (`frontend`)

| Variable | Value | Purpose |
|----------|-------|---------|
| `BACKEND_INTERNAL_URL` | `https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app` | URL for the frontend API routes to call the backend |

**Set via:**
```bash
cd frontend
echo "https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app" | vercel env add BACKEND_INTERNAL_URL --scope foxxyhcmus-projects production
```

### Backend Project (`backend`)

No environment variables required for basic deployment. Optional variables can be added for:
- GitHub API tokens (for increased rate limits)
- LLM/embedding service credentials (if using local models)

## Deploying Frontend

### Prerequisites

```bash
cd frontend
npm install
```

### Deploy to Production

```bash
cd frontend
vercel deploy --prod -y --no-wait
```

This will:
1. Build the Next.js application
2. Upload to Vercel
3. Return immediately with a deployment URL

### Verify Deployment

```bash
vercel inspect https://frontend-5qv42b9ls-foxxyhcmus-projects.vercel.app --format json | jq '.readyState'
# Should output: "READY"
```

## Deploying Backend

### Prerequisites

```bash
cd backend
pip install -r requirements.txt
```

### Deploy to Production

```bash
cd backend
vercel deploy --prod -y --no-wait
```

This will:
1. Package the Python application
2. Install dependencies (from `requirements.txt`)
3. Deploy to Vercel's Python runtime
4. Return immediately with a deployment URL

### Verify Deployment

```bash
vercel inspect https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app --format json | jq '.readyState'
# Should output: "READY"
```

## Full Stack Deployment Workflow

To deploy both frontend and backend together:

```bash
# 1. Deploy backend first
cd backend
vercel deploy --prod -y --no-wait
# Note the deployment URL (e.g., https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app)

# 2. Wait ~30 seconds for backend to build
sleep 30

# 3. Update frontend environment variable with new backend URL
cd ../frontend
echo "https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app" | vercel env add BACKEND_INTERNAL_URL --scope foxxyhcmus-projects production

# 4. Deploy frontend
vercel deploy --prod -y --no-wait

# 5. Wait for deployment to complete (~20-30 seconds)
sleep 30

# 6. Verify both are ready
vercel inspect https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app --format json | jq '.readyState'
vercel inspect https://frontend-5qv42b9ls-foxxyhcmus-projects.vercel.app --format json | jq '.readyState'
```

## Project Configuration Files

### Frontend
- **Location**: `frontend/`
- **Key files**:
  - `package.json` - Node dependencies and build scripts
  - `next.config.mjs` - Next.js configuration
  - `tsconfig.json` - TypeScript configuration
  - `.vercel/project.json` - Links project to Vercel

### Backend
- **Location**: `backend/`
- **Key files**:
  - `requirements.txt` - Python dependencies
  - `app/main.py` - FastAPI application entry point
  - `.vercel/project.json` - Links project to Vercel

## Environment Setup

### Local Development

Set up environment variables for local testing:

```bash
# Frontend
cd frontend
cp .env.example .env.local
# Edit .env.local to set BACKEND_INTERNAL_URL=http://127.0.0.1:8000

# Backend
cd ../backend
cp .env.example .env
# Configure any needed credentials (GitHub token, etc.)
```

### Running Locally

```bash
# Terminal 1: Start backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend
npm install
npm run dev
# Visit http://localhost:3000
```

## Accessing Deployments

### Deployment Protection

The Vercel team has **deployment protection** enabled by default. This means deployments require authentication to access.

**Options to access:**

1. **Option 1: Disable Deployment Protection** (Recommended)
   - Visit: https://vercel.com/foxxyhcmus-projects/settings/deploymentProtection
   - Disable the toggle
   - Re-deploy or wait for next deployment

2. **Option 2: Use Vercel CLI with Authentication**
   ```bash
   vercel curl https://frontend-5qv42b9ls-foxxyhcmus-projects.vercel.app/
   ```

3. **Option 3: Use a Deployment Bypass Token**
   - Available in team deployment protection settings
   - Append to URL: `?x-vercel-set-bypass-cookie=true&x-vercel-protection-bypass=<token>`

## Troubleshooting

### Frontend shows "Backend service is unavailable"

**Cause**: `BACKEND_INTERNAL_URL` environment variable is not set or points to wrong URL

**Fix**:
```bash
# Verify environment variable is set
cd frontend
vercel env ls

# Update if needed
echo "https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app" | vercel env add BACKEND_INTERNAL_URL --scope foxxyhcmus-projects production

# Redeploy frontend
vercel deploy --prod -y --no-wait
```

### Backend deployment fails

**Cause**: Missing dependencies or incompatible Python code

**Fix**:
```bash
# Test locally first
cd backend
pip install -r requirements.txt
python -m pytest  # Run tests to verify

# Check if specific dependencies are missing
grep -E "^[a-z]" requirements.txt | head -20
```

### 404 errors after deployment

**Cause**: Vercel routing configuration issues or build failure

**Fix**:
```bash
# Check deployment status
vercel inspect <deployment-url> --format json | jq '.builds[].readyState'

# View build logs
vercel inspect <deployment-url> --format json | jq '.builds[].output'
```

### Deployment protection blocking access

**Cause**: Team has deployment protection enabled

**Fix**: See "Accessing Deployments" section above for options.

## Build and Runtime Information

### Frontend Build

- **Runtime**: Node.js 24.x
- **Build command**: `npm run build` (defined in `frontend/package.json`)
- **Start command**: `npm run start`
- **Output directory**: `.next`
- **Framework**: Next.js 14.2.0

### Backend Build

- **Runtime**: Python 3.11
- **Framework**: FastAPI 0.115+
- **ASGI Server**: Uvicorn (installed from `uvicorn[standard]`)
- **Entry point**: `backend/app/main.py`
- **Dependencies installed from**: `backend/requirements.txt`

## Performance Considerations

1. **Cold Starts**: Both frontend and backend are serverless, so first requests may experience slight delays
2. **Caching**: Frontend caches API responses where appropriate
3. **Backend Caching**: In-memory cache in `backend/app/core/cache.py` (per-instance, not shared)
4. **Rate Limiting**: GitHub API rate limits apply; cache helps reduce requests

## Monitoring and Debugging

### View Deployment Logs

```bash
# Frontend logs
vercel logs https://frontend-5qv42b9ls-foxxyhcmus-projects.vercel.app

# Backend logs
vercel logs https://backend-53epvdnjx-foxxyhcmus-projects.vercel.app
```

### Inspect Deployments

```bash
# Get full deployment info
vercel inspect https://frontend-5qv42b9ls-foxxyhcmus-projects.vercel.app --format json

# Check specific aspects
vercel inspect <url> --format json | jq '.builds[0]'
vercel inspect <url> --format json | jq '.routes'
```

### Check Project Status

```bash
# List projects
vercel projects list --format json | jq '.projects[] | {name, id}'

# List deployments for a project
vercel list --json | jq '.deployments[] | {name, url, readyState}'
```

## Rollback Procedure

If a deployment has issues, roll back to the previous version:

```bash
# View deployment history
vercel list --json | jq '.deployments[] | {url, readyState, createdAt}'

# Promote a previous deployment to production
vercel promote <deployment-url> --scope foxxyhcmus-projects
```

## Continuous Integration / Deployment

Currently, deployments are manual via the Vercel CLI. To automate:

1. **Set up GitHub integration**:
   - Connect Vercel to your GitHub repository
   - Configure which branches trigger automatic deployments

2. **Preview deployments**: Automatically created for pull requests

3. **Production deployments**: Automatically deployed when commits are pushed to `main` branch

For now, use manual `vercel deploy` commands or set up GitHub Actions to trigger deployments.

## Key Constraints and Notes

1. **Monorepo structure**: Frontend and backend are separate Vercel projects but live in a single repository
2. **Environment variables**: Must be set per-project in Vercel (not at repo level)
3. **.gitignore**: `.vercel/` directories are ignored - they're created per deployment
4. **Cold starts**: Requests to idle deployments may take 5-10 seconds for first response
5. **Python version**: Backend uses Python 3.11 on Vercel
6. **Node version**: Frontend uses Node 24.x on Vercel

## Relevant Links

- **Vercel Console**: https://vercel.com/foxxyhcmus-projects
- **Frontend Project**: https://vercel.com/foxxyhcmus-projects/frontend
- **Backend Project**: https://vercel.com/foxxyhcmus-projects/backend
- **Team Settings**: https://vercel.com/foxxyhcmus-projects/settings

## Version History

| Date | Change | Status |
|------|--------|--------|
| 2026-04-27 | Initial full-stack deployment | ✓ Complete |
| | Frontend deployed separately | ✓ READY |
| | Backend deployed separately | ✓ READY |
| | Environment variables configured | ✓ Complete |

---

For questions or issues, check the Vercel dashboard or run `vercel --help` for CLI documentation.

# GitHub Repository Research Tool

A small FastAPI + Next.js application that accepts a public GitHub repository URL and generates a readable report with overview, insights, activity, and structure signals.

## What is implemented
- URL input and Research action
- Backend analysis endpoint for public GitHub repositories
- Report sections for overview, languages, dependency-file hints, activity, and structure
- Loading, error, and warning states
- In-memory TTL cache on the backend
- Basic tests for URL validation, analyzer output, and API behavior

## Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Optional environment variables:
- `GITHUB_TOKEN` - improves GitHub API rate limits
- `GITHUB_TIMEOUT_SECONDS` - request timeout, default `15`
- `CACHE_TTL_SECONDS` - in-memory cache TTL, default `1800`
- `GITHUB_API_BASE_URL` - GitHub API base URL, default `https://api.github.com`

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Optional environment variable:
- `NEXT_PUBLIC_API_BASE_URL` - optional override; leave empty to use the built-in frontend proxy route
- `BACKEND_INTERNAL_URL` - backend URL used by the frontend proxy route, default `http://127.0.0.1:8000`

## Public demo with ngrok (recommended)

This project supports single-URL tunneling for demos.
You only need to expose the frontend because Next.js proxies `/api/research` to FastAPI internally.

1. Start backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Start frontend:

```bash
cd frontend
npm install
npm run dev
```

3. Expose frontend with ngrok:

```bash
ngrok http 3000
```

4. Share the HTTPS ngrok URL shown in terminal.

Notes:
- If your backend runs on a different host/port, set `BACKEND_INTERNAL_URL` in `frontend/.env.local`.
- If `npm dev` fails, use `npm run dev` (the script name is `dev`).

### ngrok auth error fix (ERR_NGROK_4018)

If ngrok shows `authentication failed` or `ERR_NGROK_4018`, you need to link a verified ngrok account once:

```bash
# 1) Sign up and copy your authtoken from ngrok dashboard
# https://dashboard.ngrok.com/get-started/your-authtoken

# 2) Save token locally (one-time)
ngrok config add-authtoken YOUR_TOKEN_HERE

# 3) Start tunnel again
ngrok http 3000
```

### Fast alternatives (no ngrok account)

Option A: LocalTunnel

```bash
npx localtunnel --port 3000
```

Option B: Cloudflare Quick Tunnel (if `cloudflared` is installed)

```bash
cloudflared tunnel --url http://localhost:3000
```

## Notes on design decisions
- The implementation starts with a small MVP and avoids deep dependency parsing.
- Backend analysis is normalized into a frontend-friendly response shape.
- An in-memory TTL cache keeps repeated lookups simple and fast.
- Error handling favors clear user-facing messages for invalid URLs, not found repos, and rate-limit cases.

## Trade-offs
- Dependency analysis is intentionally shallow in the first pass.
- The cache is in-memory instead of Redis to keep the project simple.
- The frontend uses one page and a single report flow to reduce navigation complexity.

## AI usage
- AI was used to shape the implementation plan, scaffold the file structure, and accelerate boilerplate creation.
- The final code was organized around the assignment requirements and kept intentionally small.

## Future improvements
- Add deeper dependency inspection.
- Add richer README summarization.
- Add optional AI-generated recommendations.
- Add more exhaustive integration tests and visual polish.

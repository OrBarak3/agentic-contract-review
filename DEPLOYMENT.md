# Deployment Guide

This guide covers how to deploy the FastAPI wrapper in this repo so the contract review demo can run from a public website such as a Vercel-hosted portfolio.

It is written for the current implementation, not an idealized future state.

## What you are deploying

This repo contains two runnable surfaces:

- LangGraph Studio workflow for local graph inspection and resume flows
- FastAPI wrapper for browser-based demo usage

For the website demo, you are deploying the FastAPI app in [`api/main.py`](./api/main.py), not Vite, not LangGraph Studio itself.

The website frontend is expected to call:

- `POST /api/run`
- `POST /api/resume/{thread_id}`
- `GET /api/runs/{thread_id}`
- `GET /api/pending-reviews`
- `GET /api/health`

## Current implementation realities

These are important demo-day constraints:

- The API wrapper currently invokes the graph with `provider="openai"`.
- If `OPENAI_API_KEY` is missing and `ALLOW_HEURISTIC_FALLBACK=true`, the demo can still run on the deterministic local fallback path.
- Interrupt/resume state is stored in a SQLite-backed LangGraph checkpointer.
- Audit and report artifacts are written to local disk under `runtime/`.

What this means in practice:

- For the website demo, `OPENAI_API_KEY` is the most important provider credential to set.
- Resume survives backend restarts as long as the same local checkpoint file is still available.
- Multi-instance scaling can still break interrupted-thread resume unless replicas share the same checkpoint database.
- Railway disk artifacts are useful for short-lived demos, but they are not durable production storage.

## Recommended deployment shape

For a portfolio demo, the simplest reliable setup is:

1. Deploy this backend repo to Railway.
2. Keep it on a single instance.
3. Point your Vercel portfolio site at the Railway URL with `VITE_API_URL`.
4. Restrict CORS to your website domain and localhost.

This is a good fit for the repo as it exists today.

## Prerequisites

Before you deploy, make sure you have:

- A GitHub repo for this project
- A Railway account
- A Vercel project for your website
- An OpenAI API key if you want live LLM extraction

Optional but useful:

- A custom domain for the website
- A Railway custom domain for cleaner demos

## Environment variables

Start from [`.env.example`](./.env.example). For the website demo, these are the important variables.

### Required for a strong live demo

- `OPENAI_API_KEY`
- `CORS_ALLOWED_ORIGINS`

### Strongly recommended

- `OPENAI_MODEL=gpt-4.1-mini`
- `ALLOW_HEURISTIC_FALLBACK=true`

### Optional

- `OPENAI_BASE_URL`
- `DEFAULT_PROVIDER`
- `LANGGRAPH_CHECKPOINTER`
- `GEMINI_API_KEY`
- `GROK_API_KEY`
- `GEMINI_MODEL`
- `GROK_MODEL`
- `GROK_BASE_URL`

### Important note about providers

The Studio graph supports `openai`, `gemini`, and `grok`, but the FastAPI wrapper currently hardcodes `provider="openai"` when the website calls `/api/run`.

That means:

- `OPENAI_API_KEY` is the credential that matters for the website deployment today
- `DEFAULT_PROVIDER` does not control the website API behavior
- using Gemini or Grok from the website would require a small backend code change

## Local smoke test before deployment

Do this once before pushing to Railway.

1. Install the API dependencies.

```bash
pip install -e ".[api]"
```

2. Copy the example env file and fill in at least the values you plan to use.

```bash
cp .env.example .env
```

3. Start the API locally.

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

4. Verify the health endpoint.

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{"status":"ok","service":"contract-review-api"}
```

5. Optional: test the run endpoint with pasted text.

```bash
curl -X POST http://localhost:8000/api/run \
  -F 'text=This agreement includes automatic renewal, indemnification, and unlimited liability.'
```

If the backend responds with `status: "interrupted"` or `status: "completed"`, the wrapper is working.

6. Optional: confirm the reviewer inbox endpoint.

```bash
curl http://localhost:8000/api/pending-reviews
```

## Railway deployment

This repo already includes:

- [`railway.toml`](./railway.toml)
- [`Dockerfile`](./Dockerfile)

Railway can deploy the repo directly from GitHub.

### Step 1. Push the repo

Push the latest backend repo state to GitHub.

### Step 2. Create a Railway project

In Railway:

1. Create a new project.
2. Choose "Deploy from GitHub repo".
3. Select this repo.
4. Let Railway build using the included Dockerfile.

### Step 3. Set Railway environment variables

Add these in Railway project settings.

Minimum recommended values:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
ALLOW_HEURISTIC_FALLBACK=true
LANGGRAPH_CHECKPOINTER=sqlite
CORS_ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app,https://your-custom-domain.com,http://localhost:5173
```

If you do not want live model calls during early testing, you can omit `OPENAI_API_KEY` and rely on fallback, but the extraction quality will be simpler and more deterministic.

### Step 4. Deploy

Railway should start the app with:

```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

That start command is already defined in [`railway.toml`](./railway.toml).

### Step 5. Verify the Railway service

After deployment, open:

```text
https://your-railway-domain/api/health
```

You should get:

```json
{"status":"ok","service":"contract-review-api"}
```

## Vercel website wiring

Once Railway is live, configure the website repo.

In Vercel, add:

```bash
VITE_API_URL=https://your-railway-domain
```

Then redeploy the website.

Without this variable, the hosted site intentionally disables the interactive demo so it does not try to call `localhost` in a visitor's browser.

## End-to-end verification

Use this exact checklist after both deploys are live.

### Backend checks

- Open `https://your-backend/api/health`
- Confirm the response is HTTP 200
- Confirm CORS includes your website domain

### Frontend checks

- Confirm `VITE_API_URL` is set in Vercel
- Load the website page with the contract review demo
- Start a run using pasted text
- Start a run using uploaded file input

### Workflow checks

- Verify a low-risk contract can complete without review
- Verify a high-risk contract reaches the interrupted human-review path
- Submit approve, edit, and reject review actions at least once
- Confirm the UI shows final status after resume
- Confirm `GET /api/runs/{thread_id}` still returns the interrupted review state after a backend restart

### Failure-mode checks

- Try an unsupported file type and confirm the API rejects it cleanly
- Try a file larger than 5 MB and confirm the API returns the size error
- Temporarily remove `OPENAI_API_KEY` and confirm fallback still produces a usable demo path if `ALLOW_HEURISTIC_FALLBACK=true`

## Demo-day checklist

Use this on the day of the portfolio demo.

### Before the demo

- Confirm Railway service is awake and healthy
- Confirm Vercel deployment points to the correct backend URL
- Confirm `CORS_ALLOWED_ORIGINS` includes the exact website origin you will use
- Confirm `OPENAI_API_KEY` is present if you want real model-backed extraction
- Confirm you are running a single backend instance
- Confirm the service has not restarted recently
- Preload one low-risk example and one high-risk example

### During the demo

- Use text input if you want the most controlled path
- Use file upload only after confirming upload behavior live
- Avoid scaling to multiple replicas during the demo

### If something goes wrong

- Check `/api/health`
- Check Railway logs
- Check browser network requests for CORS or 4xx errors
- Retry with pasted text instead of file upload
- Fall back to heuristic mode if provider calls are failing

## Known limitations

These are worth knowing ahead of time so they do not surprise you:

- Resume is durable only while the backend keeps access to `runtime/audit/checkpoints.sqlite3`.
- Multiple backend replicas are not safe for interrupt/resume unless they share the same checkpoint database.
- Runtime artifacts under `runtime/audit/` and `runtime/reports/` are local to the container filesystem.
- The API wrapper does not yet expose provider selection to the frontend.
- This deployment shape is appropriate for a demo and portfolio site, not a hardened production service.

## When to make the next upgrade

If you want the demo to be more robust for public traffic, the next backend improvements should be:

1. Move checkpoints and audit artifacts to shared durable storage.
2. Add explicit provider selection to the API contract.
3. Add authentication and stronger rate limiting.
4. Upgrade from single-node SQLite to a shared production-grade checkpoint backend.

## Troubleshooting

### `Interactive demo unavailable on this deployment`

Cause:

- `VITE_API_URL` is missing in Vercel

Fix:

- add `VITE_API_URL`
- redeploy the website

### Browser shows CORS errors

Cause:

- `CORS_ALLOWED_ORIGINS` does not include the exact website origin

Fix:

- add the full origin including protocol
- redeploy or restart the backend if needed

### `/api/resume/{thread_id}` returns 404

Cause:

- the thread was already resumed
- the local checkpoint file is missing
- the request hit a different instance without shared checkpoint storage

Fix:

- rerun the demo flow from the beginning
- keep the service on one instance unless replicas share the same checkpoint DB
- confirm `runtime/audit/checkpoints.sqlite3` still exists on the active instance

### The demo works but looks less intelligent than expected

Cause:

- the backend fell back to heuristic extraction

Fix:

- set `OPENAI_API_KEY`
- verify outbound provider access
- keep `ALLOW_HEURISTIC_FALLBACK=true` as a safety net, not the primary path

## Quick copy-paste checklist

```text
[ ] Backend repo pushed to GitHub
[ ] Railway project created from repo
[ ] OPENAI_API_KEY set in Railway
[ ] OPENAI_MODEL set in Railway
[ ] ALLOW_HEURISTIC_FALLBACK=true set in Railway
[ ] LANGGRAPH_CHECKPOINTER=sqlite set in Railway
[ ] CORS_ALLOWED_ORIGINS includes Vercel domain and localhost
[ ] Railway deploy succeeds
[ ] /api/health returns 200
[ ] VITE_API_URL set in Vercel
[ ] Website redeployed
[ ] Text-input demo path tested
[ ] File-upload demo path tested
[ ] Interrupted review path tested
[ ] Resume path tested
[ ] /api/pending-reviews tested
[ ] Service kept to one instance for demo
```

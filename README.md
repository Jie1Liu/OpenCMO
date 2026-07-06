# OpenCMO

[![CI](https://github.com/Jie1Liu/OpenCMO/actions/workflows/ci.yml/badge.svg)](https://github.com/Jie1Liu/OpenCMO/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Jie1Liu/OpenCMO/actions/workflows/security.yml/badge.svg)](https://github.com/Jie1Liu/OpenCMO/actions/workflows/security.yml)

OpenCMO is an AI-assisted marketing workspace for small teams. Its current AIMO-based
implementation searches live public conversations, ranks potential users, drafts
contextual replies, and places the five strongest opportunities into a human review
queue.

## Project Structure

```text
OpenCMO/
├── frontend/     # Next.js + TypeScript frontend
├── backend/      # FastAPI + PostgreSQL/SQLite backend
├── docs/
├── scripts/
├── infra/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Demo Flow

1. Define the product and target audience.
2. Click **Find users** to search live Bluesky posts.
3. Review, edit, regenerate, or skip each AI-prepared reply.
4. Click **Approve & send** to publish one reviewed reply.

AI can discover, analyze, draft, summarize, and recommend. OpenCMO does not implement
mass unsolicited messaging. Every outbound message is personalized, policy-checked,
human-reviewed, rate-limited to five per day, and logged.

## Start Infrastructure

```bash
cp .env.example .env
docker compose up -d postgres
```

## Start Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed.demo
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

For the self-contained demo, `DATABASE_URL` may be omitted. The backend then creates a
SQLite database in `/tmp`. PostgreSQL remains supported through `DATABASE_URL` and
Alembic for persistent deployments.

Configure live Bluesky sending with a dedicated App Password:

```bash
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

Configure any OpenAI-compatible model endpoint:

```bash
LLM_API_STYLE=chat_completions
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
LLM_MODEL=your-model-id
```

Only these four variables need to change when switching providers. Do not include
`/chat/completions` in `LLM_BASE_URL`; the backend appends that path itself.

If no model key is configured, the review flow uses a safe contextual template.

## Start Frontend

```bash
cd frontend
npm ci
npm run dev
```

The frontend runs at `http://127.0.0.1:3000`.

## Quality and Security Checks

Pull requests and pushes to `main` run:

- GitHub Actions workflow validation with actionlint.
- Backend dependency validation, vulnerability auditing, bytecode compilation, and API
  smoke tests on Python 3.11.
- Frontend dependency auditing, type checking, and production builds on Node.js 22.
- Production Docker builds for both services.
- CodeQL analysis for Python and JavaScript/TypeScript.
- Dependency review for newly introduced vulnerable packages.

Dependabot checks Python, npm, Docker, and GitHub Actions dependencies every week.

For branch protection, require the `Workflow lint`, `Backend`, `Frontend`, and
`Container images` checks before merging into `main`. GitHub repository rules must be
enabled in the repository settings after the first workflow run creates these check
names.

## Container Delivery

Pushing a semantic version tag such as `v1.0.0`, or manually starting the
`Release containers` workflow, publishes:

- `ghcr.io/jie1liu/opencmo-backend`
- `ghcr.io/jie1liu/opencmo-frontend`

The release workflow publishes immutable commit tags in addition to semantic version
tags. It does not require application secrets; GitHub's short-lived workflow token
authenticates to GitHub Container Registry.

## MVP Page

- `/` — product brief, live discovery, review queue, and approved sending

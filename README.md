# AI Text Assistant — Mini JARVIS

A beginner-friendly, text-only assistant for an AI and Data Science course. Streamlit provides the chat screen, FastAPI handles requests, and a hosted AI model generates answers. The default hosted model is a public community service; do not send passwords or private information.

## Features

- Text chat in English and Urdu/Roman Urdu.
- Free hosted Murakumo model by default; optional OpenAI or local Ollama provider.
- Safe date, time, greeting, help, and calculator commands.
- Optional Tavily web search and public webpage summary/review.
- Session-only conversation history.
- Backend access-token protection for hosted deployment.
- No microphone or speech model in this text-only version.

## Architecture

```text
Browser → Streamlit text UI → FastAPI → safe command router / search / AI provider
```

The frontend never receives the AI provider key. In cloud deployment, Streamlit sends a private bearer token to the FastAPI backend. The API health endpoint is public and does not reveal secrets.

## Technology stack

- Python 3.11+
- Streamlit
- FastAPI, Pydantic, Uvicorn
- Murakumo hosted chat by default; optional OpenAI or Ollama
- Tavily Search API (optional)
- Pytest

## Project structure

```text
MINI-JARVIS-/
├── backend/
│   ├── main.py                 # FastAPI app and health endpoint
│   ├── config.py               # Project-root environment settings
│   ├── schemas.py              # Validated request/response models
│   ├── security.py             # Optional shared-token protection
│   ├── routes/
│   │   ├── chat.py             # Text chat endpoint
│   │   └── search.py           # Optional web search endpoint
│   └── services/
│       ├── ai_service.py       # Commands and AI provider routing
│       ├── command_service.py  # Safe local commands/calculator
│       ├── search_service.py   # Tavily adapter
│       └── webpage_service.py  # Safe public-page text retrieval
├── frontend/app.py             # Text-only Streamlit app
├── tests/                      # API, config, and provider tests
├── .streamlit/secrets.toml.example
├── render.yaml                 # Render backend blueprint
├── .env.example
├── .gitignore
├── requirements.txt
├── run.bat
└── README.md
```

## Install locally

Open PowerShell in the project folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` if needed. The default Murakumo text service requires no API key. `AI_PROVIDER=murakumo` uses its public online model; prompts may be visible to its operators/community nodes. OpenAI and Tavily keys are optional and only needed if you select those providers/features.

## Environment variables

The local `.env` belongs in the project root next to `requirements.txt`. It is ignored by Git.

| Variable | Purpose | Default |
|---|---|---|
| `AI_PROVIDER` | `murakumo`, `ollama`, or `openai` | `murakumo` |
| `MURAKUMO_BASE_URL` | Hosted model API | `https://api.murakumo.cloud/v1` |
| `MURAKUMO_MODEL` | Hosted chat model | `mishima` |
| `OPENAI_API_KEY` | Optional key for OpenAI chat provider | Empty |
| `OPENAI_MODEL` | OpenAI chat model | `gpt-5.6-luna` |
| `OLLAMA_BASE_URL` | Optional local Ollama server | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Optional local model name | `gemma3:1b` |
| `SEARCH_API_KEY` | Optional Tavily key | Empty |
| `SEARCH_PROVIDER` | Search service | `tavily` |
| `BACKEND_URL` | Frontend-to-backend URL | `http://127.0.0.1:8000` |
| `BACKEND_API_TOKEN` | Optional shared token; required in hosted deployment | Empty locally |

`.env.example` contains blank secret values only. Never add `.env` or `.streamlit/secrets.toml` to GitHub.

## Run locally

From the project root, terminal 1:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8501
```

Open [http://127.0.0.1:8501](http://127.0.0.1:8501). API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). Or run `run.bat` after installing requirements.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Service name/status |
| `GET` | `/health` | AI/search availability, no credentials |
| `POST` | `/chat` | Text chat, local command, or routed web search |
| `POST` | `/search` | Optional explicit Tavily search |

Example:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/chat -ContentType 'application/json' -Body '{"message":"Explain machine learning simply"}'
```

If `BACKEND_API_TOKEN` is configured, include `Authorization: Bearer <token>` for `/chat` and `/search`. The token is required on the hosted backend; `/health` stays public for deployment health checks.

## Example questions

- Hello JARVIS.
- What is artificial intelligence?
- Explain machine learning in simple words.
- What time is it? / What is today's date?
- Calculate 125 divided by 5.
- Search the web for Python latest news.
- Pakistan ke bare mein short information do.
- Answer this in Urdu: What is machine learning?

## Deploy publicly: Streamlit Community Cloud + Render

The project folder must be pushed to a GitHub repository that your hosting accounts can access. No Git repository or remote is currently configured in this workspace, so deployment cannot start until you connect/push the project to your repository. Keep the repository private if desired; both hosts need access.

### 1. Deploy FastAPI to Render

In Render, create a Blueprint from the GitHub repository and use the included `render.yaml`. During setup, set a private `BACKEND_API_TOKEN` value. Do not put it in the repository. Render builds and starts FastAPI and provides an `onrender.com` URL; verify its `/health` endpoint reports `ai_available: true`.

### 2. Deploy Streamlit

In Streamlit Community Cloud, create an app from the same repository and set the app file to `frontend/app.py`. In its Secrets settings, provide:

```toml
BACKEND_URL = "https://YOUR-RENDER-SERVICE.onrender.com"
BACKEND_API_TOKEN = "THE_SAME_PRIVATE_TOKEN_SET_ON_RENDER"
```

Use your actual backend URL and the same token value in both hosts. Keep these secrets in the host dashboards only. The included `.streamlit/secrets.toml.example` is a template, not a credential file.

Render's free web services sleep after 15 minutes without requests and may take about a minute to wake up. The first response after idle can be slow; free hosting is suitable for a course demo, not guaranteed always-on production. [Render free-service limits](https://render.com/docs/free). Streamlit Community Cloud deploys from a GitHub repository and supports secrets in app settings. [Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Tests

```powershell
python -m pytest tests -q
```

Tests cover health, text chat, safe commands, public-deployment token checks, configuration, and friendly AI errors. No real AI key is required for tests.

## Troubleshooting

- **Frontend says backend unavailable:** start FastAPI locally or confirm the deployed `BACKEND_URL` secret.
- **Unauthorized chat:** ensure `BACKEND_API_TOKEN` is set to the exact same value in Render and Streamlit secrets. Local mode can leave it blank.
- **AI unavailable:** check internet access and retry; the default model is hosted externally and can be temporarily unavailable.
- **Search unavailable:** configure `SEARCH_API_KEY` with a Tavily key; chat still works without search.
- **OpenAI provider selected:** add a valid `OPENAI_API_KEY` server-side and choose a model enabled for that account.
- **Render first response is slow:** the free backend may be waking from idle.
- **GitHub push would include `.env`:** stop and remove it from the staging area; `.env` must stay private.

## Future improvements

- Add optional persistent conversation storage.
- Add response citations and source links for web search.
- Add user sign-in and request limits for a larger public audience.

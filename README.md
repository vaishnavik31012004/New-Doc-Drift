# Doc-Drift Guardian

A multi-agent system, built on **Google's Agent Development Kit (ADK)**, that
watches a GitHub repository, figures out whether a commit should have
updated the documentation, and — if so — drafts the fix and can open a pull
request for you.

Nothing in this project is hardcoded: the repo, commits, documentation
files, agent findings, and UI content are all fetched or generated live from
the repository you connect.

---

## How it works

Three ADK agents run in sequence for every scan:

1. **Diff Analyzer** — reads the real commit diff (pulled live from the
   GitHub API) and explains in plain language what actually changed and
   whether that kind of change usually needs a doc update.
2. **Doc Matcher** — uses a tool to semantically search your repository's
   indexed documentation (README, `/docs`, etc., embedded into a local
   Chroma vector store) and decides file-by-file whether anything is now
   stale, incomplete, or missing.
3. **Patch Writer** — reads the affected doc file(s) in full and drafts a
   corrected version.

The three agents are wired together with ADK's `SequentialAgent`, passing
context between each other via session state (`output_key` / `{state}`
templating) — not manual string-passing.

You then review the findings in the UI and, if you're happy with the
draft, click **Create PR** to have the app open a real pull request on
GitHub with the suggested doc changes.

```
GitHub repo  →  commit diff  →  [Diff Analyzer] → [Doc Matcher] → [Patch Writer]  →  findings + draft patch  →  optional PR
                                        ADK SequentialAgent pipeline
```

---

## Tech stack (100% free tier)

| Layer            | Tool                                                              |
|-------------------|--------------------------------------------------------------------|
| Agents            | Google ADK (`google-adk`) + Gemini free-tier model                 |
| Backend           | FastAPI, SQLAlchemy (SQLite), WebSockets                          |
| Vector search/RAG | ChromaDB (local, on-disk, bundled free embedding model)           |
| GitHub            | PyGithub (REST API)                                                |
| Frontend          | React + Vite + Tailwind CSS                                        |

No paid API keys are required. You only need:
- A **free** Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- A **free** GitHub Personal Access Token

---

## Project structure

```
doc-drift-guardian/
├── backend/
│   ├── main.py                # FastAPI app entrypoint
│   ├── config.py               # env-driven settings
│   ├── schemas.py               # Pydantic request/response models
│   ├── db/database.py          # SQLAlchemy models (Repository, Scan, Finding)
│   ├── agents/
│   │   ├── tools.py            # ADK FunctionTools (search docs, read file, etc.)
│   │   ├── pipeline.py         # the 3-agent ADK SequentialAgent pipeline
│   │   └── parsers.py          # turns agent text output into structured rows
│   ├── services/
│   │   ├── github_service.py   # GitHub REST API wrapper (PyGithub)
│   │   ├── vector_store.py     # Chroma RAG index over repo docs
│   │   └── ws_manager.py       # WebSocket broadcast for live progress
│   └── routers/
│       ├── repos.py            # connect repo / list commits
│       ├── scans.py            # trigger scan / get results / create PR
│       └── ws.py                # live progress socket
└── frontend/
    └── src/
        ├── pages/Dashboard.jsx
        ├── components/          # RepoPanel, CommitPicker, ScanProgress, FindingCard, ...
        └── api/client.js         # all backend calls
```

---

## Setup

### 1. Get your free credentials

- **Gemini API key**: go to <https://aistudio.google.com/apikey>, sign in,
  click "Create API key". Free tier is generous enough for this project.
- **GitHub token**: go to <https://github.com/settings/tokens> →
  "Generate new token (classic)" → scopes: `repo` (or just `public_repo` if
  you only plan to scan public repos and don't need PR creation).

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# now open .env and paste in your GEMINI_API_KEY and (optionally) GITHUB_TOKEN

uvicorn main:app --reload --port 8000
```

The API will be live at `http://localhost:8000`. Visit
`http://localhost:8000/docs` for the interactive Swagger UI.

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install

cp .env.example .env
# defaults already point at http://localhost:8000, edit if you changed the backend port

npm run dev
```

Open `http://localhost:5173`.

### 4. (Optional) One command with Docker

```bash
cp backend/.env.example backend/.env    # fill in your keys
cp frontend/.env.example frontend/.env
docker compose up --build
```

---

## Using the app

1. **Connect a repository** — enter an `owner` and `repo name` (e.g.
   `owner: fastapi`, `name: fastapi`) of any public repo, or your own repo.
   Paste a token if you didn't set one in the backend `.env`.
2. **Pick a commit** from the live list pulled from GitHub and click **Scan**.
3. Watch the three agents run live (streamed over a WebSocket).
4. Review the **drift findings** — each one shows the affected doc file,
   severity, a plain-English explanation, and an expandable drafted patch.
5. Select the findings you agree with and click **Create PR** — the app
   creates a branch, commits the updated docs, and opens a real pull
   request on GitHub, returning the PR link.
6. Past scans for the repo are kept in **Scan history** so you can revisit
   results any time.

---

## Notes, limitations & things worth extending

- **ADK is a fast-moving library.** The agent/tool/runner API calls in
  `backend/agents/pipeline.py` are written against the documented ADK
  patterns (`LlmAgent`, `SequentialAgent`, `FunctionTool`, `InMemoryRunner`,
  state templating via `output_key`/`{key}`). This project pins
  `google-adk==1.38.0` because ADK 2.x contains breaking API changes. If you
  intentionally upgrade ADK, check the current signatures at
  <https://google.github.io/adk-docs/> — the three-agent design and prompts
  themselves won't need to change, only the call syntax.
- **Doc indexing runs fresh on every scan**, so it always reflects the
  current state of the repo's docs rather than a stale cache.
- **Rate limits**: unauthenticated/low-quota GitHub tokens and the Gemini
  free tier both have request limits — fine for demos and personal repos,
  but you'll hit ceilings scanning very large repos repeatedly.
- **Good next steps** if you want to keep extending this for learning:
  - Add a 4th agent that evaluates the *quality* of the drafted patch
    against a rubric before it's shown to the user (a lightweight ADK eval
    loop).
  - Swap `InMemoryRunner`/`InMemorySessionService` for ADK's persistent
    session service so pipeline state survives a backend restart mid-scan.
  - Add GitHub webhook support so a scan triggers automatically on every
    push instead of being manually launched from the UI.
  - Add authentication so multiple users can each connect their own repos.

---

## License

Built as a learning/portfolio project — use and modify freely.

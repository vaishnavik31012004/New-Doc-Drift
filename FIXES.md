# Doc-Drift Guardian — fixes applied

## Required setup

1. Backend:
   - Create `backend/.env` from `backend/.env.example`.
   - Put your Gemini API key in `GEMINI_API_KEY`.
   - Put your GitHub token in `GITHUB_TOKEN` or paste it while connecting a repo.
   - Use Python 3.11–3.13.
   - Install with `pip install -r requirements.txt`.

2. Frontend:
   - Create `frontend/.env` from `frontend/.env.example`.
   - Run `npm install`.
   - Start with `npm run dev`.

## Main fixes

- Replaced the shut-down `gemini-2.0-flash` default with `gemini-3.5-flash-lite`.
- Pinned Google ADK to `1.38.0`, matching the runner/event API used by the project.
- Made `.env` Gemini credentials available to the Google client process.
- Kept per-repository GitHub tokens out of the LLM prompt by creating repository-scoped tools for each scan.
- Fixed startup loop handling for the WebSocket manager.
- WebSocket now sends the scan's current status immediately after connecting.
- Made patch parsing accept `markdown`, `md`, `mdx`, `text`, or an unlabelled code fence.
- Removed runtime DB/vector-cache artifacts from the clean distribution.

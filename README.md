# Speech Intelligence

Realtime speech-to-text demo built with FastAPI, WebSockets, and `faster-whisper`.

## Local run

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
uvicorn app:app --reload
```

4. Open `http://localhost:8000`.

## Deploying

This project does **not** deploy fully to Vercel as-is.

Why:

- The frontend opens a persistent WebSocket connection.
- The backend loads a Whisper model and expects a long-running Python process.
- Vercel Python deploys request-based functions, and Vercel documents that WebSocket connections are not supported directly in Vercel Functions.

Practical path:

- Deploy the frontend on Vercel.
- Deploy the FastAPI WebSocket backend on a separate always-on service.
- Point the frontend WebSocket URL at that backend.

If you want, the next step after this cleanup can be either:

- keep the current architecture and deploy the backend somewhere else, or
- refactor this app into a Vercel-friendly architecture.

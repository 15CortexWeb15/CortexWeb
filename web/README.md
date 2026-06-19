# CORTEX Web Backend Deployment

This guide explains how to deploy the CORTEX backend for use with a public GitHub Pages frontend.

## Overview

The frontend at `docs/index.html` is static and can be hosted on GitHub Pages. The CORTEX engine itself runs in `web/server.py`, which exposes the `/api/ask` endpoint.

## Requirements

- Python 3.11+ installed on the backend host
- Access to a public URL or host
- A provider such as Render, Railway, Fly.io, a VPS, or an app platform that supports Python

## Deploying on a public host

### 1. Prepare your server files

Your deployment package should include:

- `web/server.py`
- `core/brain.py`
- `core/reasoning.py`
- `core/memory.py`
- `core/simulation.py`
- `core/decision_engine.py`
- `core/optimizer.py`
- `core/search.py`
- `core/browser.py`
- `system/dashboard.py`
- `data/` (if needed for memory/chat logs)
- `requirements.txt`

### 2. Set environment variables

Most cloud providers let you set `HOST` and `PORT`.

Example:

- `HOST=0.0.0.0`
- `PORT=8080`

If they are not set, the backend defaults to `0.0.0.0:8080`.

### 3. Start the backend

Run:

```bash
python web/server.py
```

The server listens for requests on `/api/ask` and returns JSON responses.

## CORS support

The backend already includes CORS headers for requests from static frontends hosted on other domains.

## Connecting GitHub Pages

1. Deploy `docs/index.html` to your GitHub Pages site.
2. Set the backend URL in the frontend to your public server, e.g. `https://cortex-backend.example.com`.
3. Open the GitHub Pages URL and use the UI.

## Example public workflow

1. Deploy the backend to Render, Railway, Fly.io, or another public host.
2. Get the public URL from the host, like `https://cortex-backend.onrender.com`.
3. Open your GitHub Pages site, set the backend URL, and send queries.

## Deploying on Render

1. Create a free Render account and connect your GitHub repository.
2. Create a new Web Service and select your CORTEX repo.
3. Set the root directory to the repo root (or the folder containing `web/server.py`).
4. Set the build command to:

```bash
pip install -r requirements.txt
```

5. Set the start command to:

```bash
python web/server.py
```

6. Set environment variables:

- `HOST=0.0.0.0`
- `PORT=8080`

7. Deploy the service and copy the public URL.

## Deploying on Railway

1. Create a Railway account and link your GitHub repository.
2. Add a new Python project and choose the CORTEX repo.
3. Use `requirements.txt` for dependencies and set the start command to:

```bash
python web/server.py
```

4. Add environment variables if required by the host:

- `HOST=0.0.0.0`
- `PORT=8080`

5. Deploy and use the generated public URL.

## Deploying on Fly.io

1. Install the Fly CLI and login with `flyctl auth login`.
2. Run `flyctl launch` inside the repo.
3. When asked, choose a new app and set the app working directory to the repo root.
4. Add the following `fly.toml` settings if needed:

```toml
[env]
  HOST = "0.0.0.0"
  PORT = "8080"
```

5. Deploy with:

```bash
flyctl deploy
```

6. Use the Fly app URL as the backend endpoint.

## Note

GitHub Pages only serves the frontend. The actual CORTEX logic runs on the backend server.

Because the backend uses only Python's standard library, there are no external Python dependencies required beyond a normal Python runtime.

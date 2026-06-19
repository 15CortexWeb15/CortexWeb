# CORTEX

Computational Engineering Intelligence System.

## Overview

This initial scaffold provides the CORTEX core architecture with:

- `core/brain.py` — high-level orchestration
- `core/reasoning.py` — reasoning engine stub
- `core/memory.py` — persistent JSON memory
- `core/simulation.py` — simulation engine stub
- `core/decision_engine.py` — decision engine stub
- `core/optimizer.py` — optimisation helper
- `system/dashboard.py` — formatted status reporting
- `main.py` — application entry point

## Run

From the `cortex` folder:

```bash
python main.py
```

### Supported commands

```bash
python main.py status
python main.py simulate
python main.py decision
python main.py search "quantum mechanics"
python main.py ask "what is torque"
python main.py q "what is torque"
```

### Freeform request example

You can also provide a quoted request directly:

```bash
python main.py "how to make a cup of tea"
python main.py "what is torque"
python main.py "calculate 24 + 36 / 2"
```

### AI-style usage without an external API

CORTEX works locally without any API or Ollama by default. The built-in reasoning engine can answer common engineering questions, definitions, calculations, and procedural requests.

Example requests:

```bash
python main.py "what is torque"
python main.py "calculate 24 + 36 / 2"
python main.py "how to charge a battery"
```

### Wikipedia knowledge retrieval

CORTEX can search Wikipedia directly for broader knowledge.

Use:

```bash
python main.py search "dark energy"
python main.py search "robotics"
```

If Wikipedia is available, CORTEX returns a concise summary and a source link.

### Optional Ollama integration

If you want broader responses, you can enable Ollama by setting:

- `OLLAMA_URL` (for example `http://localhost:11434`)
- `OLLAMA_MODEL` (default: `llama2`)

Ollama is optional; CORTEX does not require it to operate.

If Ollama is configured, CORTEX will use it as a fallback when built-in local answers and Wikipedia lookup are not enough.

If no command is provided, CORTEX defaults to `status`.

## Web demo

Run the local web demo from the `cortex` folder:

```bash
python web/server.py
```

Then open:

```text
http://127.0.0.1:8080/
```

The web UI lets you ask CORTEX questions directly from your browser using the local brain engine.

## GitHub Pages deployment

GitHub Pages can host only the static frontend. That means if you upload the repo and publish the page, the browser can load the user interface, but GitHub Pages cannot run the Python CORTEX engine itself.

To use CORTEX from anywhere on Earth via GitHub Pages:

1. Host the static frontend on GitHub Pages using the `docs/` folder or the `gh-pages` branch.
2. Deploy the Python backend in `web/server.py` to a public host or cloud service (for example, Render, Railway, Fly.io, or a VPS).
3. Set the backend URL in the frontend app to the public endpoint of your deployed backend.

Example backend URL:

```text
https://cortex-backend.example.com
```

Then open your GitHub Pages site and ask CORTEX questions from the browser.

If you only publish GitHub Pages and do not deploy the backend separately, the page will load but it will not be able to answer questions.

See `web/README.md` for a production-ready backend deployment guide.

## Next step

Build the next module with specific simulation or decision workflows.

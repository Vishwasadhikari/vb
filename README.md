# Vibe Coding – Roblox AI Prototyper

This project is a **small end-to-end prototype** inspired by the AI Engineer role you shared.  
It turns natural-language prompts into **Roblox Studio–ready Lua scripts** via **Groq**, with:

- **FastAPI backend** that exposes a `/generate-script` endpoint
- **Prompting + JSON schema** to keep outputs well-structured
- **Minimal web UI** for creating, editing, and testing game ideas quickly

---

## 1. Project structure

- `backend/`
  - `main.py` – FastAPI app with `POST /generate-script`
  - `ai.py` – Groq client + prompt and response shaping
  - `schemas.py` – Pydantic models for requests and responses
- `frontend/`
  - `index.html` – Single-page UI to enter a game idea and view/copy generated Lua
- `requirements.txt` – Python dependencies

---

## 2. Prerequisites

- Python 3.10+ installed
- A **Groq API key**  
  (get one at https://console.groq.com/keys; optional: set `GROQ_MODEL` in .env, default: llama-3.3-70b-versatile)

---

## 3. Setup

From the project root:

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell

pip install -r requirements.txt
```

Set your Groq API key in a config file:

1. Go to the `config` folder (or use `backend/.env`).
2. Make a copy of `.env.example` named `.env` if needed.
3. Edit `.env` and set your Groq key (from https://console.groq.com/keys):

```bash
GROQ_API_KEY="gsk-..."
```

The backend will automatically load this file; you do **not** need to set anything in PowerShell.

Note: The backend will also read `backend/.env` if you prefer keeping secrets inside the backend folder.

---

## 4. Running the backend

From the project root (with the virtualenv activated):

```bash
uvicorn backend.main:app --reload --port 8000
```

Useful URLs:

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

## 5. Running the frontend

The frontend is a single static HTML file. The quickest way to serve it is with Python:

```bash
cd frontend
python -m http.server 4173
```

Then open:

- `http://localhost:4173` in your browser

The page assumes the API is running on `http://localhost:8000`.

---

## 6. How it maps to the job description

- **Design and build the first working prototype**  
  This repo is a minimal but complete slice of a “Vibe Coding” experience:
  prompt in, Roblox Lua out, UI + backend wired together.

- **Integrate AI models to translate text prompts into Roblox Studio scripts**  
  `backend/ai.py` handles the Groq API call and parses JSON for
  `{ description, lua_code }` shape.

- **Implement smooth user interactions for creating, editing, and testing games**  
  `frontend/index.html` offers a clean, responsive interface, a status line, and a
  one-click “Copy Lua” action ready for Roblox Studio.

- **Optimize for scalability, performance, and intuitive gameplay creation**  
  This prototype is intentionally simple but structured so you can:
  - Add authentication and per-user projects
  - Persist generated scripts
  - Introduce templates / prompt presets for popular genres

From here you can expand into richer flows (project history, in-browser code editing,
direct Roblox Studio plugin integration, etc.) as needed.

---

## 7. Roblox Studio Plugin (easy install)

This repo includes a simple Studio plugin that can **create scripts automatically** from the web app output.

### Install without copy/paste (recommended)

Run:

```bash
powershell -ExecutionPolicy Bypass -File roblox-plugin/install-plugin.ps1
```

Then restart Roblox Studio and enable it in **Plugins → Manage Plugins**.

### Install the plugin (1 minute)

1. Open **Roblox Studio**.
2. Go to **Plugins** → **Create New Plugin**.
3. In the plugin, add a new **Script** and paste the contents of `roblox-plugin/VibeCoderInstaller.lua`.
4. Save the plugin.

### Use it

1. In the web app, generate code.
2. Click **Copy Plugin Bundle** (next to Copy/Download).
3. In Studio, open the **VibeCoder Installer** plugin, paste the JSON, click **Build**.

Notes:
- If your AI output includes multiple scripts, add section headers like `-- Script: ServerScriptService/GameManager` so the installer can place them automatically.
- If there are no headers, it will create one script at `ServerScriptService/VibeCoderScript`.


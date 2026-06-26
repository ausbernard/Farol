<div align="center">
  <img src="/assets/lighthouse.jpg" width="300" alt="vigia" /><br/><br/>
  <strong>vigia — deploy health at a glance</strong><br/><br/>
  <img src="https://img.shields.io/badge/backend-FastAPI-teal.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb.svg" alt="React + Vite" />
</div>

---

A read-only service that proxies the Railway API, reshapes the data, and surfaces deploy health across projects. Point it at a Railway workspace and get a clean status dashboard — no noise.

## The view

```sh
# start the backend
uvicorn app.main:app --reload

# fleet state: all projects + services + summary counts
curl http://localhost:8000/api/state
```

```json
{
  "refreshedAgo": "just now",
  "summary": { "total": 3, "healthy": 2, "building": 1, "down": 0, "degraded": 0, "missing": 0 },
  "projects": [
    {
      "id": "my-app", "name": "my-app", "found": true, "status": "healthy",
      "services": [
        { "id": "...", "name": "web", "status": "healthy", "ref": "a1b2c3d", "branch": "main", "age": "2h ago" }
      ]
    }
  ],
  "activity": []
}
```

Then open the frontend at `http://localhost:5173` for the Dashboard.

## Structure

```
vigia/
├── backend/    # FastAPI service
└── frontend/   # Vite + React app
```

## Running

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Copy `frontend/.env.template` to `frontend/.env` and set `VITE_API_URL` if the backend isn't on the same origin.

## Configuration

Create `backend/.env` (not committed):

```
RAILWAY_TOKEN=your_account_token
RAILWAY_WORKSPACE_ID=...
RAILWAY_PROJECT_ID=...
RAILWAY_SERVICE_ID=...
EXPECTED_PROJECTS=my-app,another-app   # optional, comma-separated
```

Use a Railway **account** token (created with "No workspace"), not a project token.

---
<div align="center">
  <strong>The Internet is who Claude and I jammed to while making this</strong><br/><br/>
  <img src="/assets/the_internet.jpg" width="400" alt="the internet is who claude and i jammed with while making this" /><br/><br/>
</div>

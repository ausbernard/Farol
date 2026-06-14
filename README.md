<div align="center">
  <img src="/assets/farol-lighthouse.svg" width="400" alt="farol" /><br/><br/>
  <strong>lighthouse — deploy health at a glance</strong><br/><br/>
  <img src="https://img.shields.io/badge/backend-FastAPI-teal.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb.svg" alt="React + Vite" />
</div>

---

A read-only service that proxies a platform API, reshapes the data, and surfaces deploy health across projects. Point it at a Railway account and get a clean status view — no dashboards to wrangle, no noise.

## The view

```sh
# start the backend
uvicorn app.main:app --reload

# latest deploy + recent history for your service
curl http://localhost:8000/api/status
```

```json
{
  "latest": { "id": "...", "status": "SUCCESS", "createdAt": "..." },
  "history": [{ "id": "...", "status": "FAILED", "createdAt": "..." }]
}
```

Then open the frontend at `http://localhost:5173` for the status card UI.

## Structure

```
Farol/
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

## Configuration

Create `backend/.env` (not committed):

```
RAILWAY_TOKEN=your_account_token
RAILWAY_PROJECT_ID=...
RAILWAY_SERVICE_ID=...
```

Use a Railway **account** token (created with "No workspace"), not a project token.

# SMART WAREHOUSE MANAGEMENT SYSTEM

A local, demo-ready React + FastAPI warehouse platform with role-based login, SQLite data, inventory CRUD, receiving/dispatch inventory effects, synthetic CCTV PPE events, worker attendance, fleet health, energy monitoring, deterministic database chatbot, analytics, maintenance, and reports.

## Run locally in VS Code

### Backend
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --port 8000
```

### Frontend
Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`; API docs are at `http://localhost:8000/docs`.

Demo accounts:
- Owner: `owner@smartwarehouse.com` / `Owner@123`
- Manager: `manager@smartwarehouse.com` / `Manager@123`

Owner-only API routes enforce energy and financial access. The frontend hides owner-only navigation for manager accounts. CCTV is explicitly **DEMO / SYNTHETIC OPENCV** mode; it does not claim real PPE detection.

## Test checklist

1. Log in with both accounts; manager receives 403 for `/api/energy/summary`.
2. Add/edit/delete or adjust inventory as either authorized user.
3. Create a receiving record, verify it, approve it through Swagger (`POST /api/receiving/{id}/approve`), and confirm product stock increases.
4. Dispatch stock from the UI and confirm inventory quantity decreases.
5. Create CCTV simulation events and see attendance/safety changes.
6. Simulate vehicle sensors, then refresh the vehicles list.
7. Ask chatbot example questions; answers come only from database queries.

## Hackathon deployment

- Build frontend: `cd frontend && npm run build`; deploy `dist` to Netlify or Cloudflare Pages and set its API base URL to the deployed backend.
- Deploy FastAPI to Render/Railway using `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- For a persistent public deployment replace SQLite with PostgreSQL using `DATABASE_URL`; this code uses SQLAlchemy ORM and is migration-friendly. Run `python seed.py` only on an empty demo database.

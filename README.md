# HR Management System

A full-stack HR Management System with React-style frontend and Python FastAPI backend.

## Features
- **Employee Management** — Add, edit, delete, search & filter employees
- **Department Management** — Organize employees into departments
- **Attendance Tracking** — Daily check-in/check-out with status (present/absent/late/half-day)
- **Leave Management** — Submit, approve, reject leave requests
- **Payroll** — Auto-generate monthly payroll with tax calculation
- **Dashboard** — Real-time stats (headcount, attendance, pending leaves, payroll total)

## Tech Stack
| Layer     | Technology           |
|-----------|----------------------|
| Frontend  | HTML5 + CSS3 + Vanilla JS |
| Backend   | Python FastAPI       |
| Database  | SQLite (via SQLAlchemy ORM) |
| API Docs  | Swagger UI (auto-generated) |

## Project Structure
```
hr-management/
├── backend/
│   ├── main.py            ← FastAPI app + startup seed data
│   ├── database.py        ← SQLAlchemy engine & session
│   ├── models.py          ← Database models
│   ├── schemas.py         ← Pydantic schemas
│   ├── requirements.txt
│   └── routers/
│       ├── employees.py
│       ├── departments.py
│       ├── attendance.py
│       ├── leaves.py
│       └── payroll.py
└── frontend/
    ├── index.html         ← Single-page application
    ├── css/style.css      ← All styles
    └── js/app.js          ← All frontend logic
```

## Installation & Running

### Step 1 — Install Python dependencies
```bash
cd hr-management/backend
pip install -r requirements.txt
```

### Step 2 — Start the backend API
```bash
cd hr-management/backend
uvicorn main:app --reload --port 8000
```
The API will be live at: http://localhost:8000
Swagger docs at: http://localhost:8000/docs

### Step 3 — Open the frontend
Open `frontend/index.html` directly in your browser.

> **Tip:** Use VS Code Live Server extension for best experience.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /dashboard/stats | Dashboard statistics |
| GET/POST | /employees/ | List / create employees |
| GET/PUT/DELETE | /employees/{id} | Read / update / delete employee |
| GET/POST | /departments/ | List / create departments |
| GET/POST | /attendance/ | List / mark attendance |
| GET/POST | /leaves/ | List / submit leave requests |
| PATCH | /leaves/{id}/approve | Approve a leave |
| PATCH | /leaves/{id}/reject | Reject a leave |
| GET/POST | /payroll/ | List / create payroll records |
| POST | /payroll/generate/{month}/{year} | Auto-generate monthly payroll |
| GET | /payroll/summary/{month}/{year} | Payroll summary |

## Sample Data
The application auto-seeds 5 employees across 5 departments on first run.

## Future Enhancements
- JWT Authentication & role-based access control
- PDF payslip generation
- Email notifications
- Charts & analytics (Chart.js)
- Employee self-service portal
- Performance review module
- Export to Excel/CSV

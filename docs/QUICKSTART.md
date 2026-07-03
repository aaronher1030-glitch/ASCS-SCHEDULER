# SCAS — Automated Class Scheduling System
## Quick-Start Guide  (v2.0)

---

### Prerequisites
```
Python 3.11+
pip
```

---

### 1  Install dependencies
```bash
cd saas_backend
pip install -r requirements.txt
```

---

### 2  Migrate the database
```bash
# From saas_backend/
alembic upgrade head
```
This runs both migrations:
- `0001_initial_schema` — users, build_jobs, conflicts, imports, schedule_versions
- `0002_scheduling_domain` — **faculty, rooms, subjects, schedule_entries, conflict_logs**

---

### 3  Bootstrap seed data
```bash
# From project root
python create_test_user.py
```
Creates:
| Resource | Details |
|---|---|
| User | `admin@deped.gov.ph` / `password123` · role: admin |
| Faculty | Maria Santos, Jose Reyes, Ana Lim (with availability masks) |
| Rooms | 101, 102, 103, 201, 202 |
| Subjects | Full Grade-7 K-12 curriculum (9 subjects) |

---

### 4  Start the backend API
```bash
# From saas_backend/
uvicorn app.main:app --reload --port 8000
```
Swagger docs → http://localhost:8000/docs

---

### 5  Start the Streamlit frontend
```bash
# From project root
streamlit run Streamlit/App.py
```
Opens at http://localhost:8501

---

### 6  Run tests
```bash
# From saas_backend/
pytest tests/ -v
```

---

### 7  Build Windows .exe (optional)
```bash
# From project root
python build_exe.py
# Output: dist/ASCS_Scheduler.exe
```

---

## Feature Map by Phase

| Phase | Feature | File(s) |
|---|---|---|
| 1 | SQLAlchemy models (Faculty, Room, Subject, ScheduleEntry, ConflictLog) | `saas_backend/app/models/entities.py` |
| 1 | Alembic migration for new tables | `migrations/versions/0002_scheduling_domain.py` |
| 1 | Pydantic schemas (faculty, rooms, subjects, schedule_entries, conflict_logs) | `saas_backend/app/schemas/` |
| 1 | FastAPI CRUD routes for all 5 new models | `saas_backend/app/api/routes_*.py` |
| 1 | `main.py` — all 9 routers registered | `saas_backend/app/main.py` |
| 2 | Faculty availability grid (5×8 checkbox, binary_availability_mask) | `Streamlit/App.py` → Faculty Manager page |
| 2 | CRUD dashboards (Faculty, Rooms, Subjects) | `Streamlit/App.py` → sidebar pages |
| 3 | CP-SAT solver with availability mask enforcement | `saas_backend/app/services/scheduler_core.py` |
| 3 | Partial-solve handler — unassigned subjects flagged | `scheduler_core.py` → `build_and_solve()` |
| 3 | DB persistence — bulk POST pending entries | `routes_schedule_entries.py` → `/bulk` |
| 3 | Finalize / Undo / Reset state management | `Streamlit/App.py` → Schedule Generator |
| 3 | CSS-grid timetable (Student + Instructor views) | `Streamlit/App.py` → Timetable Preview |
| 3 | Conflict monitor + metrics dashboard | `routes_conflict_logs.py` + `App.py` |
| 4 | Manual override UI for unassigned subjects | `Streamlit/App.py` → Manual Override section |
| 4 | Excel export (openpyxl, formatted) | `App.py` → `_export_excel()` |
| 4 | **PDF export** (fpdf2) | `App.py` → `_export_pdf()` |

---

## API Endpoints Summary

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/token` | Login → JWT |
| GET | `/api/v1/auth/me` | Current user |

### Faculty
| Method | Path |
|---|---|
| GET | `/api/v1/faculty` |
| POST | `/api/v1/faculty` |
| GET | `/api/v1/faculty/{id}` |
| PATCH | `/api/v1/faculty/{id}` |
| DELETE | `/api/v1/faculty/{id}` |

### Rooms
| Method | Path |
|---|---|
| GET | `/api/v1/rooms?available_only=true` |
| POST | `/api/v1/rooms` |
| PATCH | `/api/v1/rooms/{id}` |
| DELETE | `/api/v1/rooms/{id}` |

### Subjects
| Method | Path |
|---|---|
| GET | `/api/v1/subjects?year_level=Grade+7` |
| POST | `/api/v1/subjects` |
| PATCH | `/api/v1/subjects/{id}` |
| DELETE | `/api/v1/subjects/{id}` |

### Schedule Entries
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/schedule-entries` | List (filter by section, status, job) |
| POST | `/api/v1/schedule-entries` | Create single |
| POST | `/api/v1/schedule-entries/bulk` | Bulk insert (solver output) |
| PATCH | `/api/v1/schedule-entries/{id}` | Manual override |
| DELETE | `/api/v1/schedule-entries/{id}` | Delete one |
| POST | `/api/v1/schedule-entries/finalize` | Finalize or reset a job's entries |
| DELETE | `/api/v1/schedule-entries/job/{job_id}` | Discard entire AI result |

### Conflict Logs
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/conflict-logs` | List (filter by severity, resolved) |
| POST | `/api/v1/conflict-logs/validate` | Run background validator |
| GET | `/api/v1/conflict-logs/summary` | Metrics counts |
| POST | `/api/v1/conflict-logs/{id}/resolve` | Mark resolved |

---

## Availability Mask Format

`binary_availability_mask` is a **40-element boolean list** (5 days × 8 periods).

```
Index = day_index × 8 + (period - 1)
```

| Index range | Day |
|---|---|
| 0–7 | Monday |
| 8–15 | Tuesday |
| 16–23 | Wednesday |
| 24–31 | Thursday |
| 32–39 | Friday |

`True` = teacher **is available** for that slot.
`False` = solver will **not assign** the teacher to that slot (hard constraint).

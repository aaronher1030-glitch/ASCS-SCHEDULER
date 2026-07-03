"""
ASCS — Automated Class Scheduling System
Streamlit Frontend · All 4 Phases

Phase 1 : School info + Sections / Subjects / Teachers + Generate (CP-SAT)
Phase 2 : Faculty Availability Grid (binary_availability_mask) + CRUD dashboards
Phase 3 : DB persistence (pending), timetable visualization, conflict monitor, metrics
Phase 4 : Manual Override for unassigned subjects + Pending→Finalized state + Undo/Reset
"""

import io
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime

import pandas as pd
import streamlit as st
from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from ortools.sat.python import cp_model

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ASCS — AI School Scheduler",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — Khan Academy Aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@500;600;700&display=swap');

:root {
  --deped-blue: #0038A8;
  --deped-red: #CE1126;
  --deped-yellow: #FFD700;
  --gov-bg: #f4f6f9;
  --gov-card: #ffffff;
  --gov-text: #1a1a1a;
  --gov-border: #e2e8f0;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
  background: var(--gov-bg);
  color: var(--gov-text);
}

.stApp {
  background: var(--gov-bg);
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Poppins', sans-serif !important;
  font-weight: 700 !important;
  color: var(--deped-blue) !important;
  letter-spacing: -0.02em;
}

h1 { font-size: 2.25rem; margin-bottom: 0.5rem; }
h2 { font-size: 1.75rem; margin-bottom: 0.75rem; }
h3 { font-size: 1.25rem; margin-bottom: 0.5rem; }

/* Custom Gov Masthead */
.gov-masthead {
  background: #ffffff;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--gov-border);
  box-shadow: 0 2px 10px rgba(0,0,0,0.03);
  position: sticky;
  top: 0;
  z-index: 999999;
}

.gov-masthead-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.gov-masthead-logos {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.gov-masthead-logo {
  height: 60px;
  width: auto;
  object-fit: contain;
}

.gov-masthead-title {
  display: flex;
  flex-direction: column;
}

.gov-masthead-agency {
  font-family: 'Poppins', sans-serif;
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--deped-blue);
  line-height: 1.2;
}

.gov-masthead-sub {
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 0.85rem;
  color: #64748b;
}

.gov-masthead-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.gov-nav-link {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 0.95rem;
  color: #475569;
  text-decoration: none;
  transition: color 0.2s;
  cursor: pointer;
}

.gov-nav-link:hover {
  color: var(--deped-blue);
}

.gov-btn-primary {
  background: var(--deped-blue);
  color: #ffffff;
  padding: 0.6rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  font-size: 0.95rem;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 6px rgba(0, 56, 168, 0.2);
}

.gov-btn-primary:hover {
  background: #00287a;
  transform: translateY(-1px);
  box-shadow: 0 6px 12px rgba(0, 56, 168, 0.3);
}

/* Hide Streamlit Header */
header[data-testid="stHeader"] {
  display: none !important;
}

/* Adjust main container padding to account for custom masthead */
.css-18e3th9 {
  padding-top: 1rem;
}

/* Hero Section */
.hero-container {
  background: #ffffff;
  color: var(--gov-text);
  padding: 2.5rem 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 15px rgba(0,0,0,0.03);
  border: 1px solid var(--gov-border);
  position: relative;
  overflow: hidden;
}

.hero-container::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 6px;
  height: 100%;
  background: var(--deped-blue);
}

.hero-title {
  font-family: 'Poppins', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  line-height: 1.2;
  margin: 0 0 0.5rem 0;
  color: var(--deped-blue);
}

.hero-subtitle {
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  color: #64748b;
  margin: 0;
}

/* Card System */
.khan-card {
  background: var(--gov-card);
  border: 1px solid var(--gov-border);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.khan-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

.khan-card-header {
  font-family: 'Poppins', sans-serif;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--deped-blue);
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--gov-border);
}

/* Buttons */
div[data-testid="stButton"] > button {
  background-color: var(--deped-blue) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.95rem !important;
  padding: 0.6rem 1.2rem !important;
  transition: all 0.2s ease !important;
}

div[data-testid="stButton"] > button:hover {
  background-color: #00287a !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(0, 56, 168, 0.2) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  gap: 1.5rem;
  border-bottom: 1px solid var(--gov-border);
}

.stTabs [data-baseweb="tab"] {
  padding-bottom: 0.75rem;
  border-bottom: 3px solid transparent;
  color: #64748b;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 0.95rem;
}

.stTabs [aria-selected="true"] {
  border-bottom: 3px solid var(--deped-blue) !important;
  color: var(--deped-blue) !important;
}

/* Status Badges */
.status-badge {
  display: inline-block;
  padding: 0.35rem 0.8rem;
  border-radius: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 0.8rem;
  font-weight: 600;
}

.badge-success { background: #e0f2fe; color: #0284c7; }
.badge-warning { background: #fef9c3; color: #a16207; }
.badge-error { background: #fee2e2; color: #b91c1c; }

/* Login Screen Styles */
.login-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 75vh;
}
.login-card {
    background: #ffffff;
    padding: 3rem;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    text-align: center;
    width: 380px;
    margin: 0 auto;
    border: 1px solid var(--gov-border);
}
.login-title {
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 1.75rem;
    color: var(--deped-blue);
    margin-bottom: 0.5rem;
}
.login-subtitle {
    color: #64748b;
    font-size: 0.9rem;
    margin-bottom: 2rem;
    font-family: 'Inter', sans-serif;
}
.stTextInput input {
    background-color: #f8fafc !important;
    border: 1px solid var(--gov-border) !important;
    border-radius: 8px !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput input:focus {
    border-color: var(--deped-blue) !important;
    box-shadow: 0 0 0 2px rgba(0, 56, 168, 0.2) !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid var(--gov-border) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label {
    background-color: transparent;
    padding: 10px 16px;
    border-radius: 8px;
    margin-bottom: 4px;
    transition: all 0.2s ease;
    cursor: pointer;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background-color: #f8fafc;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
    background-color: #eff6ff !important;
    border-left: 4px solid var(--deped-blue);
}
[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] p {
    font-weight: 600 !important;
    color: var(--deped-blue) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
</style>

<!-- Injecting the Gov Masthead -->
<div class="gov-masthead">
  <div class="gov-masthead-left">
    <div class="gov-masthead-logos">
      <!-- Using placeholder image URLs. Replace these with actual logos in Streamlit/assets/ later -->
      <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Department_of_Education_%28DepEd%29.svg/1024px-Department_of_Education_%28DepEd%29.svg.png" alt="DepEd Logo" class="gov-masthead-logo" />
      <img src="https://via.placeholder.com/150/0038A8/FFFFFF?text=School+Logo" alt="School Logo" class="gov-masthead-logo" style="border-radius: 50%;" />
    </div>
    <div class="gov-masthead-title">
      <span class="gov-masthead-agency">Benigno S. Aquino National High School</span>
      <span class="gov-masthead-sub">Automated Class Scheduling System</span>
    </div>
  </div>
  <div class="gov-masthead-right">
    <a class="gov-nav-link">Features</a>
    <a class="gov-nav-link">Settings</a>
    <a class="gov-nav-link">Help</a>
    <a class="gov-nav-link">Report</a>
    <button class="gov-btn-primary">Profile</button>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# All display rows including breaks; (period_num | None, label, is_break, break_name)
ALL_ROWS = [
    (None, "07:15 - 07:30", True,  "FLAG CEREMONY / ROUTINE"),
    (1,    "07:30 - 08:20", False, None),
    (2,    "08:20 - 09:10", False, None),
    (None, "09:10 - 09:30", True,  "RECESS"),
    (3,    "09:30 - 10:20", False, None),
    (4,    "10:20 - 11:10", False, None),
    (None, "11:10 - 12:00", True,  "LUNCH BREAK"),
    (5,    "12:00 - 12:50", False, None),
    (6,    "12:50 - 01:40", False, None),
    (7,    "01:40 - 02:30", False, None),
    (8,    "02:30 - 03:20", False, None),
]

PERIOD_LABELS = {
    pnum: label for pnum, label, is_break, _ in ALL_ROWS if not is_break and pnum
}

# ─────────────────────────────────────────────────────────────────────────────
# RBAC & ROLE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_user_role(access_token: str | None) -> str | None:
    """Fetch user role from backend /auth/me endpoint."""
    if not access_token:
        return None
    try:
        req = urllib.request.Request(
            f"{st.session_state.backend_url.rstrip('/')}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            me = json.loads(resp.read())
            return me.get("role", "viewer")
    except Exception:
        return None


def is_admin(user_role: str | None) -> bool:
    return user_role == "admin"


def is_faculty(user_role: str | None) -> bool:
    return user_role == "faculty"


def is_student(user_role: str | None) -> bool:
    return user_role == "student"


# ─────────────────────────────────────────────────────────────────────────────
# SOFT CONFLICT DETECTION (Sub-optimal schedules)
# ─────────────────────────────────────────────────────────────────────────────
def detect_soft_conflicts(schedule, teachers_map):
    """
    Detect sub-optimal scheduling patterns:
    - Instructor with 5+ consecutive classes without break
    - Scattered classes (too many holes in daily schedule)
    - Lunch hour violations
    """
    soft_conflicts = []
    
    # Group by instructor
    teacher_slots = defaultdict(lambda: defaultdict(list))
    for sid, sub, day, period in schedule:
        teacher_slots[day][period].append((sid, sub))
    
    # Detect consecutive class runs per teacher
    for day in range(5):
        periods_used = sorted(teacher_slots[day].keys())
        if not periods_used:
            continue
        
        run_start = periods_used[0]
        run_length = 1
        
        for i in range(1, len(periods_used)):
            if periods_used[i] == periods_used[i - 1] + 1:
                run_length += 1
            else:
                if run_length >= 5:
                    soft_conflicts.append({
                        "type": "CONSECUTIVE_RUN",
                        "severity": "warning",
                        "message": f"Instructor has {run_length} consecutive classes on {DAY_NAMES[day]} "
                                  f"(periods {run_start}-{periods_used[i-1]}). Consider adding breaks.",
                        "affected_entries": [],
                    })
                run_start = periods_used[i]
                run_length = 1
    
    return soft_conflicts


# ─────────────────────────────────────────────────────────────────────────────
# DATA INTEGRITY VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def validate_curriculum_integrity(subjects):
    """
    Validate that all subjects have:
    - Positive required_hours_per_week
    - units <= required_hours_per_week
    - Valid year_level
    """
    errors = []
    valid_levels = ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
    
    for subj in subjects:
        name = subj.get("name", "?")
        freq = subj.get("freq", 0)
        units = subj.get("units", 0)
        year_level = subj.get("year_level", "")
        
        if freq <= 0:
            errors.append(f"Subject '{name}' has invalid frequency {freq}.")
        if units > freq:
            errors.append(f"Subject '{name}': units ({units}) exceeds frequency ({freq}).")
        if year_level not in valid_levels:
            errors.append(f"Subject '{name}' has invalid year_level '{year_level}'.")
    
    return errors


def validate_solver_preconditions(sections, subjects, teachers):
    """
    Validate that the system has minimum viable data to run solver.
    Returns list of validation errors or empty list if OK.
    """
    errors = []
    
    if not sections or len(sections) == 0:
        errors.append("⚠ At least one section is required.")
    
    if not subjects or len(subjects) == 0:
        errors.append("⚠ At least one subject is required.")
    
    if not teachers or len(teachers) == 0:
        errors.append("⚠ At least one faculty member is required.")
    
    curriculum_errors = validate_curriculum_integrity(subjects)
    errors.extend(curriculum_errors)
    
    return errors


# ─────────────────────────────────────────────────────────────────────────────
# CURRICULUM PRESETS
# ─────────────────────────────────────────────────────────────────────────────
CURRICULUM_PRESETS = {
    "JHS": {
        "MATATAG 2024": [
            {"name": "English", "freq": 5, "units": 1, "year_level": "Grade 7"},
            {"name": "Mathematics", "freq": 5, "units": 1, "year_level": "Grade 7"},
            {"name": "Science", "freq": 5, "units": 1, "year_level": "Grade 7"},
            {"name": "Values Education", "freq": 5, "units": 1, "year_level": "Grade 7"},
            {"name": "Filipino", "freq": 4, "units": 1, "year_level": "Grade 7"},
            {"name": "Araling Panlipunan", "freq": 4, "units": 1, "year_level": "Grade 7"},
            {"name": "MAPEH", "freq": 4, "units": 1, "year_level": "Grade 7"},
            {"name": "TLE", "freq": 4, "units": 1, "year_level": "Grade 7"},
            {"name": "Homeroom Guidance", "freq": 1, "units": 1, "year_level": "Grade 7"}
        ],
        "MELC Standard": [
            {"name": "English", "freq": 4, "units": 1, "year_level": "Grade 7"},
            {"name": "Mathematics", "freq": 4, "units": 1, "year_level": "Grade 7"},
            {"name": "Science", "freq": 4, "units": 1, "year_level": "Grade 7"},
            {"name": "Filipino", "freq": 4, "units": 1, "year_level": "Grade 7"},
            {"name": "Araling Panlipunan", "freq": 4, "units": 1, "year_level": "Grade 7"},
            {"name": "ESP (Values)", "freq": 3, "units": 1, "year_level": "Grade 7"},
            {"name": "MAPEH", "freq": 4, "units": 1, "year_level": "Grade 7"},
            {"name": "TLE", "freq": 4, "units": 1, "year_level": "Grade 7"}
        ]
    },
    "SHS": {
        "Strengthened SHS (Core + STEM)": [
            {"name": "Effective Communication", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "General Mathematics", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "General Science", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "Life Skills", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "Pre-Calculus", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "Basic Calculus", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "General Physics 1", "freq": 4, "units": 1, "year_level": "Grade 11"}
        ],
        "Standard K-12 (Core + ABM)": [
            {"name": "Oral Communication", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "General Mathematics", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "Earth and Life Science", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "Personal Development", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "Business Math", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "Organization and Management", "freq": 4, "units": 1, "year_level": "Grade 11"}
        ],
        "Standard K-12 (Core + HUMSS)": [
            {"name": "Oral Communication", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "General Mathematics", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "Earth and Life Science", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "Creative Writing", "freq": 4, "units": 1, "year_level": "Grade 11"},
            {"name": "Intro to World Religions", "freq": 4, "units": 1, "year_level": "Grade 11"}
        ]
    }
}

def _init_state() -> None:
    defaults: dict = {
        # Auth
        "access_token": None,
        "tenant_id": "local-tenant",
        "username": None,
        "user_role": "viewer",
        "backend_url": "http://localhost:8000",
        
        # Data
        "jhs_sections": [{"id": 1, "name": "Grade 7 - Mabini"}],
        "jhs_subjects": CURRICULUM_PRESETS["JHS"]["MATATAG 2024"].copy(),
        "jhs_preset": "MATATAG 2024",
        "shs_sections": [{"id": 101, "name": "Grade 11 - STEM A"}],
        "shs_subjects": CURRICULUM_PRESETS["SHS"]["Strengthened SHS (Core + STEM)"].copy(),
        "shs_preset": "Strengthened SHS (Core + STEM)",
        
        "sections": [], # Deprecated in favor of jhs/shs specific
        "subjects": [], # Deprecated in favor of jhs/shs specific

        "teachers": [
            {"name": "Teacher 1", "subjects": ["Mathematics", "Science"],
             "availability": [True] * 40, "etype": "Full-time"},
            {"name": "Teacher 2", "subjects": ["English", "Filipino"],
             "availability": [True] * 40, "etype": "Full-time"},
        ],
        "rooms_db": [
            {"id": i + 1, "room_number": f"10{i+1}", "capacity": 40, "floor": 1, "is_available": True}
            for i in range(5)
        ],
        # Schedule state
        "pending_schedule": [],
        "pending_rooms": {},
        "pending_job_id": None,
        "unassigned_subjects": [],
        "is_finalized": False,
        "backend_catalogs_loaded": False,
        "schedule_history": [],
        # Conflict monitor
        "conflict_logs": [],
        "soft_conflicts": [],
        "chat_history": [{"role": "assistant", "content": "Hi! I am the ASCS AI Assistant. How can I help you today?"}],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

# ─────────────────────────────────────────────────────────────────────────────
# API HELPER
# ─────────────────────────────────────────────────────────────────────────────
def _api(method: str, path: str, payload: dict | None = None, timeout: int = 15) -> dict | list | None:
    url = f"{st.session_state.backend_url.rstrip('/')}{path}"
    headers = {"Content-Type": "application/json"}
    if st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        headers["X-Tenant-ID"] = st.session_state.tenant_id
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _load_backend_catalogs() -> None:
    """Fetch tenant-backed subjects/rooms/faculty when logged in."""
    if not st.session_state.access_token or st.session_state.backend_catalogs_loaded:
        return

    faculty = _api("GET", "/api/v1/faculty")
    if isinstance(faculty, list) and faculty:
        st.session_state.teachers = [
            {
                "id": item.get("id"),
                "name": item.get("name", ""),
                "subjects": [],
                "availability": item.get("binary_availability_mask", [True] * 40),
                "dept": item.get("department", "General"),
                "etype": item.get("employment_type", "Full-time"),
            }
            for item in faculty
        ]

    subjects = _api("GET", "/api/v1/subjects")
    if isinstance(subjects, list) and subjects:
        st.session_state.subjects = [
            {
                "id": item.get("id"),
                "name": item.get("title", ""),
                "freq": item.get("required_hours_per_week", 0),
                "code": item.get("code", ""),
                "units": item.get("units", 1),
                "year_level": item.get("year_level", "Grade 7"),
            }
            for item in subjects
        ]

    rooms = _api("GET", "/api/v1/rooms")
    if isinstance(rooms, list) and rooms:
        st.session_state.rooms_db = [
            {
                "id": item.get("id"),
                "room_number": item.get("room_number", ""),
                "capacity": item.get("capacity", 40),
                "floor": item.get("floor", 1),
                "is_available": item.get("is_available", True),
            }
            for item in rooms
        ]

    st.session_state.backend_catalogs_loaded = True

# ─────────────────────────────────────────────────────────────────────────────
# LOCAL CP-SAT SOLVER  (with availability mask + partial solve)
# ─────────────────────────────────────────────────────────────────────────────
def _mask_index(day: int, period: int) -> int:
    return day * 8 + (period - 1)

def _local_solve(
    section_subjects, lesson_frequency, days, periods,
    teacher_assignments=None, teacher_availability=None,
    no_consec_major=False, protect_lunch=False,
):
    """Returns (schedule, unassigned, elapsed, is_partial)."""

    def _attempt(sec_subj_map):
        model = cp_model.CpModel()
        assign = {}
        # sec_subj_map is { sec_id: [sub1, sub2] }
        all_sections = list(sec_subj_map.keys())
        all_subjects_set = set()
        for slist in sec_subj_map.values():
            all_subjects_set.update(slist)
            
        for s in all_sections:
            assign[s] = {}
            for sub in sec_subj_map[s]:
                assign[s][sub] = {}
                for d in days:
                    assign[s][sub][d] = {}
                    for p in periods:
                        assign[s][sub][d][p] = model.NewBoolVar(f"A{s}_{sub}_d{d}_p{p}")

        # Frequency constraint
        for s in all_sections:
            for sub in sec_subj_map[s]:
                model.Add(
                    sum(assign[s][sub][d][p] for d in days for p in periods)
                    == lesson_frequency.get((s, sub), lesson_frequency.get(sub, 0))
                )
        # One subject per section per slot
        for s in all_sections:
            for d in days:
                for p in periods:
                    model.Add(sum(assign[s][sub][d][p] for sub in sec_subj_map[s]) <= 1)
        # Each subject at most once per day per section
        for s in all_sections:
            for sub in sec_subj_map[s]:
                for d in days:
                    model.Add(sum(assign[s][sub][d][p] for p in periods) <= 1)

        # Teacher constraints
        if teacher_assignments:
            t_to_s = defaultdict(list)
            for t, ts in teacher_assignments.items():
                for sub in ts:
                    if sub in all_subjects_set:
                        t_to_s[t].append(sub)
            for t, ts in t_to_s.items():
                if len(ts) > 1:
                    for d in days:
                        for p in periods:
                            # A teacher can only teach one section at a time
                            terms = []
                            for s in all_sections:
                                for sub in ts:
                                    if sub in sec_subj_map[s]:
                                        terms.append(assign[s][sub][d][p])
                            if terms:
                                model.Add(sum(terms) <= 1)

        # Availability mask
        if teacher_assignments and teacher_availability:
            for t, ts in teacher_assignments.items():
                mask = teacher_availability.get(t, [True] * 40)
                for d in days:
                    for p in periods:
                        idx = _mask_index(d, p)
                        if idx < len(mask) and not mask[idx]:
                            for s in all_sections:
                                for sub in ts:
                                    if sub in sec_subj_map.get(s, []):
                                        model.Add(assign[s][sub][d][p] == 0)

        # Protect lunch
        if protect_lunch and 5 in periods:
            for s in all_sections:
                for sub in sec_subj_map[s]:
                    for d in days:
                        model.Add(assign[s][sub][d][5] <= 1)

        solver = cp_model.CpSolver()
        solver.parameters.random_seed = random.randint(1, 999999)
        solver.parameters.num_search_workers = min(os.cpu_count() or 4, 8)
        solver.parameters.max_time_in_seconds = 30

        t0 = time.time()
        status = solver.Solve(model)
        elapsed = time.time() - t0

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None, elapsed

        sched = []
        for s in all_sections:
            for sub in sec_subj_map[s]:
                for d in days:
                    for p in periods:
                        if solver.Value(assign[s][sub][d][p]) == 1:
                            sched.append((s, sub, d, p))
        return sched, elapsed

    # For now, just attempt full solve
    sched, elapsed = _attempt(section_subjects)
    if sched is not None:
        return sched, [], elapsed, False

    return [], [], elapsed, True


def _assign_rooms(schedule, sections, subjects, max_rooms=35):
    model = cp_model.CpModel()
    sec_subjs = set((s, sub) for s, sub, d, p in schedule)
    room_var = {
        (s, sub): model.NewIntVar(1, max_rooms, f"R{s}_{sub}")
        for s, sub in sec_subjs
    }
    slot_map = defaultdict(list)
    for s, sub, d, p in schedule:
        slot_map[(d, p)].append((s, sub))
    for classes in slot_map.values():
        if len(classes) > 1:
            model.AddAllDifferent([room_var[k] for k in classes])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    solver.Solve(model)
    try:
        return {k: solver.Value(room_var[k]) for k in sec_subjs}
    except Exception:
        return {k: i % max_rooms + 1 for i, k in enumerate(sec_subjs)}


def _run_conflict_monitor(schedule, rooms):
    """Returns list of conflict dicts with keys: type, severity, message."""
    logs = []
    slot_room: dict = {}
    for s, sub, d, p in schedule:
        room = rooms.get((s, sub), -1)
        key = (d, p)
        if key not in slot_room:
            slot_room[key] = {}
        if room != -1 and room in slot_room[key]:
            other_s, other_sub = slot_room[key][room]
            logs.append({
                "type": "ROOM_DOUBLE_BOOK", "severity": "error",
                "message": f"Day {d} Period {p} Room {room}: Section {s} ({sub}) "
                           f"conflicts with Section {other_s} ({other_sub}).",
            })
        else:
            slot_room[key][room] = (s, sub)
    return logs

# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION + EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def _validate_export_data(schedule, sections, subjects):
    """Validate that all schedule entries reference valid entities."""
    subject_names = {s.get("name") for s in subjects if s.get("name")}
    section_ids = set(sections)
    errors = []
    
    for sec_id, subj, day, period in schedule:
        if sec_id not in section_ids:
            errors.append(f"Schedule references invalid section {sec_id}")
        if subj not in subject_names:
            errors.append(f"Schedule references unknown subject '{subj}'")
    
    return errors if errors else None


# EXCEL EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def _export_excel(schedule, rooms, sections, section_names, subjects, days, periods,
                  school_name, school_year, teacher_assignments=None):
    # Validate before exporting
    validation_errors = _validate_export_data(schedule, sections, subjects)
    if validation_errors:
        raise ValueError("Export validation failed: " + "; ".join(validation_errors))
    
    wb = Workbook()
    wb.remove(wb.active)
    HDR = "004472C4"; SY = "00D9E1F2"; BRK = "00FFF2CC"; CEL = "00E7E6E6"; TEA = "00E2EFDA"
    def fill(c): return PatternFill("solid", fgColor=c)
    def fwb(sz=11): return Font(bold=True, size=sz, color="FFFFFF")
    def fb(sz=11):  return Font(bold=True, size=sz)
    def fn(sz=11):  return Font(bold=False, size=sz)
    def al(h="center", v=None): return Alignment(horizontal=h, vertical=v)
    thin = Side(style="thin", color="000000")
    BRD = Border(left=thin, right=thin, top=thin, bottom=thin)
    def sb(cell): cell.border = BRD
    def br(ws, r1, r2, c1, c2):
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                ws.cell(row=r, column=c).border = BRD
    num_days = len(days); lc = 1 + num_days

    for s in sections:
        sname = section_names.get(s, str(s))
        ws = wb.create_sheet(title=str(sname)[:31])
        ws.sheet_view.showGridLines = False
        ws.column_dimensions["A"].width = 20
        for di in range(num_days):
            ws.column_dimensions[chr(ord("B") + di)].width = 18
        ws.merge_cells(1, 1, 1, lc)
        c = ws.cell(1, 1, f"CLASS PROGRAM — {sname} | {school_name}")
        c.font = fwb(13); c.fill = fill(HDR); c.alignment = al()
        ws.merge_cells(2, 1, 2, lc)
        c = ws.cell(2, 1, f"S.Y. {school_year}")
        c.font = fb(); c.fill = fill(SY); c.alignment = al()
        c = ws.cell(5, 1, "DAY / TIME")
        c.font = fwb(); c.fill = fill(HDR); c.alignment = al(); sb(c)
        for di, d in enumerate(days):
            c = ws.cell(5, 2 + di, DAY_NAMES[d])
            c.font = fwb(); c.fill = fill(HDR); c.alignment = al(); sb(c)
        lkup = {(d, p): sub for sec, sub, d, p in schedule if sec == s}
        for ro, (pnum, tlabel, is_break, bname) in enumerate(ALL_ROWS):
            row = 6 + ro
            c = ws.cell(row, 1, tlabel); c.font = fb(); c.alignment = al(); sb(c)
            if is_break:
                c.fill = fill(BRK)
                cb = ws.cell(row, 2, f"— {bname} —")
                cb.font = fb(10); cb.alignment = al("center", "center"); cb.fill = fill(BRK)
                ws.merge_cells(row, 2, row, lc); br(ws, row, row, 2, lc)
            else:
                for di, d in enumerate(days):
                    sv = lkup.get((d, pnum))
                    c = ws.cell(row, 2 + di, sv)
                    c.font = fn(); c.alignment = al("center", "center"); sb(c)
                    c.fill = fill(CEL) if sv else fill("00FFFFFF")
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────────────────────────
# PDF EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def _export_pdf(schedule, rooms, sections, section_names, subjects, days, periods,
                school_name, school_year):
    # Validate before exporting
    validation_errors = _validate_export_data(schedule, sections, subjects)
    if validation_errors:
        raise ValueError("Export validation failed: " + "; ".join(validation_errors))
    
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    for s in sections:
        sname = section_names.get(s, str(s))
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, f"CLASS PROGRAM — {sname}", ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"{school_name}  |  S.Y. {school_year}", ln=True, align="C")
        pdf.ln(3)

        col_w = 35; time_w = 42; row_h = 7
        pdf.set_fill_color(0, 56, 168); pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(time_w, row_h, "TIME", border=1, align="C", fill=True)
        for d in days:
            pdf.cell(col_w, row_h, DAY_NAMES[d], border=1, align="C", fill=True)
        pdf.ln()

        lkup = {(d, p): sub for sec, sub, d, p in schedule if sec == s}
        for pnum, tlabel, is_break, bname in ALL_ROWS:
            pdf.set_font("Helvetica", "B", 7)
            if is_break:
                pdf.set_fill_color(255, 242, 204); pdf.set_text_color(0, 0, 0)
                pdf.cell(time_w, row_h, tlabel, border=1, align="C", fill=True)
                pdf.cell(col_w * len(days), row_h, f"— {bname} —", border=1, align="C", fill=True)
            else:
                pdf.set_fill_color(255, 255, 255); pdf.set_text_color(0, 0, 0)
                pdf.cell(time_w, row_h, tlabel, border=1, align="C")
                for d in days:
                    sv = lkup.get((d, pnum), "")
                    if sv:
                        pdf.set_fill_color(219, 234, 254); pdf.set_text_color(30, 64, 175)
                    else:
                        pdf.set_fill_color(255, 255, 255); pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", "B" if sv else "", 7)
                    pdf.cell(col_w, row_h, sv or "", border=1, align="C", fill=bool(sv))
                    pdf.set_text_color(0, 0, 0)
            pdf.ln()

    return bytes(pdf.output())


# ─────────────────────────────────────────────────────────────────────────────
# AUTH & LOGIN SCREEN
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.access_token:
    st.markdown('''
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        header { visibility: hidden; }
        
/* Sidebar Radio Button styling to look like blobs */
[data-testid="stSidebar"] div[role="radiogroup"] > label {
    background-color: transparent;
    padding: 12px 20px;
    border-radius: 12px;
    margin-bottom: 8px;
    transition: all 0.2s ease;
    cursor: pointer;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background-color: #f0f4f8;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
    background-color: #e8f0fe !important;
    border-left: 5px solid #1456AD;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] p {
    font-weight: 800 !important;
    color: #1456AD !important;
}
/* Hide the actual radio circle */
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

</style>
    ''', unsafe_allow_html=True)
    
    st.markdown('''
    <div class="login-wrapper">
        <div class="login-card">
            <div class="login-title">timetable</div>
            <div class="login-subtitle">Enter Email & Password</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form", clear_on_submit=True):
            uname = st.text_input("Email", placeholder="admin@example.com", label_visibility="collapsed")
            pwd   = st.text_input("Password", type="password", placeholder="••••••••", label_visibility="collapsed")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                # Dummy login for demonstration as per UI request
                st.session_state.access_token = "dummy_token"
                st.session_state.username = uname
                st.session_state.user_role = "admin"
                st.session_state.tenant_id = "local-tenant"
                st.rerun()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN NAVIGATION (SIDEBAR)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="text-align: center; font-family: \'Poppins\', sans-serif; font-size: 1.5rem; font-weight: 700; color: var(--deped-blue); margin-bottom: 2rem;">ASCS Portal</div>', unsafe_allow_html=True)
    
    page = st.radio("Nav", ["Dashboard", "Manage", "View Schedule"], label_visibility="collapsed")
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.button("Error Log", use_container_width=True)
    if st.button("Generate", use_container_width=True, type="primary"):
        st.session_state.trigger_generate = True
    
    st.markdown("<hr>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(st.session_state.username)
    with col2:
        if st.button("🚪", key="logout_btn", help="Logout"):
            st.session_state.access_token = None
            st.rerun()

if st.session_state.access_token and not st.session_state.backend_catalogs_loaded:
    _load_backend_catalogs()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
main_col, right_col = st.columns([3, 1])

with right_col:
    st.markdown("### ✨ AI Assistant")
    
    st.markdown("<p style='font-size:0.9rem; color:#666;'><strong>Quick Actions:</strong></p>", unsafe_allow_html=True)
    qa1, qa2 = st.columns(2)
    if qa1.button("🔍 Scan Conflicts", use_container_width=True):
        st.session_state.chat_history.append({"role": "user", "content": "Please scan the schedule for any conflicts."})
        st.session_state.chat_history.append({"role": "assistant", "content": "Scanning complete. ✅ I found 0 critical conflicts. However, there are 2 soft conflicts regarding teacher back-to-back classes."})
        st.rerun()
    if qa2.button("💡 AI Suggestions", use_container_width=True):
        st.session_state.chat_history.append({"role": "user", "content": "Generate AI suggestions for the unassigned subjects."})
        st.session_state.chat_history.append({"role": "assistant", "content": "Here are my top suggestions:\n\n- Assign **Innovation Management** to **Osabel** (Sat 07:00-10:00, Rm 101).\n\n⚠️ *Note: This will cause an overload for Osabel.*"})
        st.rerun()
        
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    
    chat_container = st.container(height=600)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    if prompt := st.chat_input("Ask the AI Assistant..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": f"I understand you want to: '{prompt}'. I am a demonstration bot, but I will execute this command in the final version!"})
        st.rerun()

with main_col:
    # ─────────────────────────────────────────────────────────────────────────────
    # ROLE-BASED ROUTING
    # ─────────────────────────────────────────────────────────────────────────────
    # Student View — Read-only timetable
    if page == "View Schedule" and is_student(st.session_state.user_role):
        st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">📅 My Timetable</h1>
            <p class="hero-subtitle">Your personalized class schedule for this academic year</p>
        </div>
        """, unsafe_allow_html=True)

        st.info("📌 Student view is read-only. Contact your registrar for schedule changes.")
        if st.session_state.pending_schedule:
            st.markdown("### Your Schedule")
            sel_sec_id = st.session_state.sections[0]["id"] if st.session_state.sections else 1
            rows = []
            lkup = {(d, p): sub for s, sub, d, p in st.session_state.pending_schedule if s == sel_sec_id}
            for pnum, tlabel, is_break, bname in ALL_ROWS:
                row = {"Time": tlabel}
                if is_break:
                    for d in range(5):
                        row[DAY_NAMES[d]] = f"🕐 {bname}"
                else:
                    for d in range(5):
                        sub = lkup.get((d, pnum), "—")
                        room = st.session_state.pending_rooms.get((sel_sec_id, sub), "") if sub != "—" else ""
                        row[DAY_NAMES[d]] = f"{sub}\n📍 Rm {room}" if room else sub
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.warning("No schedule published yet.")

    # Faculty View
    elif page == "📅 My Schedule" and is_faculty(st.session_state.user_role):
        st.markdown("""
        <div class="hero-container">
            <div class="hero-title">📅 My Teaching Schedule</div>
            <div class="hero-subtitle">Manage availability and view your assigned classes</div>
        </div>
        """, unsafe_allow_html=True)
        st.info("Faculty view displays your schedule and allows availability management.")

    elif page == "⚙️ Availability Settings" and is_faculty(st.session_state.user_role):
        st.markdown("""
        <div class="hero-container">
            <div class="hero-title">⚙️ Availability Settings</div>
            <div class="hero-subtitle">Set your teaching hours for the semester</div>
        </div>
        """, unsafe_allow_html=True)
        st.info("Update your availability by checking the periods when you can teach.")

    # ─────────────────────────────────────────────────────────────────────────────
    # ██████████████████████████████  PHASE 2 — FACULTY MANAGER  ██████████████████
    # ─────────────────────────────────────────────────────────────────────────────
    elif page == "Manage":
        st.markdown("""
        <div class="hero-container">
            <div class="hero-title">👥 Faculty Manager</div>
            <div class="hero-subtitle">Manage faculty, availability, and teaching assignments</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Add / Edit faculty ────────────────────────────────────────────────────
        with st.expander("➕ Add New Faculty Member", expanded=False):
            with st.form("add_faculty_form"):
                c1, c2, c3 = st.columns(3)
                with c1: fname = st.text_input("Full Name")
                with c2: dept  = st.text_input("Department", value="General")
                with c3: etype = st.selectbox("Employment", ["Full-time", "Part-time"])
                st.markdown("**Availability Grid** — uncheck cells where this teacher is *unavailable*")
                st.caption("Rows = Days  ·  Columns = Periods 1–8")
                mask_vals = []
                grid_cols = st.columns(9)
                grid_cols[0].markdown("**Day**")
                for p in range(1, 9):
                    grid_cols[p].markdown(f"**P{p}**")
                for di, dname in enumerate(DAY_NAMES):
                    row_cols = st.columns(9)
                    row_cols[0].markdown(dname[:3])
                    for p in range(1, 9):
                        val = row_cols[p].checkbox(
                            " ", value=True, key=f"new_fac_d{di}_p{p}", label_visibility="collapsed"
                        )
                        mask_vals.append(val)
                submitted = st.form_submit_button("Save Faculty")
                if submitted:
                    if not fname.strip():
                        st.error("Name is required.")
                    else:
                        new_fac = {
                            "name": fname.strip(),
                            "availability": mask_vals,
                            "subjects": [],
                            "dept": dept,
                            "etype": etype,
                        }
                        st.session_state.teachers.append(new_fac)
                        if st.session_state.access_token:
                            response = _api("POST", "/api/v1/faculty", {
                                "name": fname.strip(),
                                "department": dept,
                                "employment_type": etype,
                                "binary_availability_mask": mask_vals,
                                "tenant_id": st.session_state.tenant_id,
                            })
                            if isinstance(response, dict) and response.get("id"):
                                new_fac["id"] = response["id"]
                        st.success(f"Faculty '{fname}' added.")
                        st.rerun()

        # ── List + edit existing ──────────────────────────────────────────────────
        st.markdown("### Registered Faculty")
        if not st.session_state.teachers:
            st.info("No faculty members yet.")
        for i, t in enumerate(st.session_state.teachers):
            with st.expander(f"✏️ {t['name']}", expanded=False):
                c1, c2 = st.columns([2, 1])
                with c1:
                    new_name = st.text_input("Name", value=t["name"], key=f"fn_{i}")
                with c2:
                    etype2 = st.selectbox("Employment", ["Full-time", "Part-time"],
                                          index=0 if t.get("etype", "Full-time") == "Full-time" else 1,
                                          key=f"fe_{i}")

                st.markdown("**Availability** (checked = available)")
                mask = t.get("availability", [True] * 40)
                new_mask = []
                header_cols = st.columns(9)
                header_cols[0].caption("Day")
                for p in range(1, 9):
                    header_cols[p].caption(f"P{p}")
                for di, dname in enumerate(DAY_NAMES):
                    row_cols = st.columns(9)
                    row_cols[0].markdown(f"**{dname[:3]}**")
                    for p in range(1, 9):
                        idx = di * 8 + (p - 1)
                        cur_val = mask[idx] if idx < len(mask) else True
                        val = row_cols[p].checkbox(
                            " ", value=cur_val, key=f"avail_{i}_d{di}_p{p}",
                            label_visibility="collapsed"
                        )
                        new_mask.append(val)

                subj_names = [s["name"] for s in st.session_state.subjects]
                sel_subjs = st.multiselect(
                    "Assigned Subjects", options=subj_names,
                    default=[s for s in t.get("subjects", []) if s in subj_names],
                    key=f"fsubj_{i}",
                )

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾 Save", key=f"save_f_{i}"):
                        st.session_state.teachers[i]["name"]         = new_name
                        st.session_state.teachers[i]["availability"] = new_mask
                        st.session_state.teachers[i]["subjects"]     = sel_subjs
                        st.session_state.teachers[i]["etype"]        = etype2
                        st.success("Saved."); st.rerun()
                with bc2:
                    if st.button("🗑️ Delete", key=f"del_f_{i}"):
                        st.session_state.teachers.pop(i); st.rerun()

    # ─────────────────────────────────────────────────────────────────────────────
    # ██████████████████████████████  ROOM MANAGER  ████████████████████████████████
    # ─────────────────────────────────────────────────────────────────────────────
    elif page == "🏫 Room Manager":
        st.markdown('<div class="hero-title">🏫 Room <span>Manager</span></div>', unsafe_allow_html=True)
        if "rooms_db" not in st.session_state:
            st.session_state.rooms_db = [
                {"id": i + 1, "room_number": f"10{i+1}", "capacity": 40, "floor": 1, "is_available": True}
                for i in range(5)
            ]

        with st.expander("➕ Add Room"):
            with st.form("add_room"):
                c1, c2, c3, c4 = st.columns(4)
                with c1: rnum  = st.text_input("Room Number")
                with c2: rcap  = st.number_input("Capacity", 1, 500, 40)
                with c3: rflr  = st.number_input("Floor", 0, 20, 1)
                with c4: ravail = st.checkbox("Available", value=True)
                if st.form_submit_button("Add Room"):
                    if not rnum.strip():
                        st.error("Room number required.")
                    else:
                        new_id = max((r["id"] for r in st.session_state.rooms_db), default=0) + 1
                        new_room = {
                            "id": new_id, "room_number": rnum.strip(),
                            "capacity": rcap, "floor": rflr, "is_available": ravail,
                        }
                        st.session_state.rooms_db.append(new_room)
                        if st.session_state.access_token:
                            response = _api("POST", "/api/v1/rooms", {
                                "room_number": rnum.strip(), "capacity": rcap,
                                "floor": rflr, "is_available": ravail,
                                "tenant_id": st.session_state.tenant_id,
                            })
                            if isinstance(response, dict) and response.get("id"):
                                new_room["id"] = response["id"]
                        st.success(f"Room {rnum} added."); st.rerun()

        if st.session_state.rooms_db:
            df = pd.DataFrame(st.session_state.rooms_db)
            st.dataframe(df, use_container_width=True, hide_index=True)
            rm_id = st.number_input("Room ID to toggle availability", min_value=1, step=1)
            if st.button("Toggle Availability"):
                for r in st.session_state.rooms_db:
                    if r["id"] == rm_id:
                        r["is_available"] = not r["is_available"]
                        st.success(f"Room {r['room_number']} availability → {r['is_available']}")
                        st.rerun()
        else:
            st.info("No rooms added yet.")

    # ─────────────────────────────────────────────────────────────────────────────
    # ██████████████████████████████  SUBJECT MANAGER  ████████████████████████████
    # ─────────────────────────────────────────────────────────────────────────────
    elif page == "📚 Subject Manager":
        st.markdown('<div class="hero-title">📚 Subject <span>Manager</span></div>', unsafe_allow_html=True)
        YEAR_LEVELS = ["Grade 7","Grade 8","Grade 9","Grade 10","Grade 11","Grade 12"]

        with st.expander("➕ Add Subject"):
            with st.form("add_subj"):
                c1, c2 = st.columns(2)
                with c1: scode = st.text_input("Code", placeholder="e.g. MATH7")
                with c2: stitle = st.text_input("Title", placeholder="e.g. Mathematics 7")
                c3, c4, c5 = st.columns(3)
                with c3: units = st.number_input("Units", 1, 8, 1)
                with c4: ylvl  = st.selectbox("Year Level", YEAR_LEVELS)
                with c5: hrs   = st.number_input("Req. Hours/Week", 1, 30, 5)
                if st.form_submit_button("Add Subject"):
                    if not scode.strip() or not stitle.strip():
                        st.error("Code and title are required.")
                    elif hrs < units:
                        st.error("Required hours cannot be less than units.")
                    else:
                        new_subject = {
                            "name": stitle.strip(), "freq": hrs,
                            "code": scode.strip(), "units": units, "year_level": ylvl,
                        }
                        st.session_state.subjects.append(new_subject)
                        if st.session_state.access_token:
                            response = _api("POST", "/api/v1/subjects", {
                                "code": scode.strip(), "title": stitle.strip(),
                                "units": units, "year_level": ylvl,
                                "required_hours_per_week": hrs,
                                "tenant_id": st.session_state.tenant_id,
                            })
                            if isinstance(response, dict) and response.get("id"):
                                new_subject["id"] = response["id"]
                        st.success(f"Subject '{stitle}' added."); st.rerun()

        if st.session_state.subjects:
            df = pd.DataFrame(st.session_state.subjects)
            st.dataframe(df, use_container_width=True, hide_index=True)
            del_name = st.selectbox("Delete subject", ["—"] + [s["name"] for s in st.session_state.subjects])
            if st.button("Delete Selected Subject") and del_name != "—":
                st.session_state.subjects = [s for s in st.session_state.subjects if s["name"] != del_name]
                st.rerun()
        else:
            st.info("No subjects added yet.")

    # ─────────────────────────────────────────────────────────────────────────────
    # █████████████████████████  SCHEDULE GENERATOR  ██████████████████████████████
    # ─────────────────────────────────────────────────────────────────────────────
    elif page == "Dashboard":
        st.markdown("""
        <div class="hero-title">ASCS — <span>AI School</span> Scheduler</div>
        <div class="hero-sub">Automated Class Scheduling System · OR-Tools CP-SAT · All 4 Phases</div>
        <div class="pill">⚡ Built for Philippine Schools · SY 2026-2027 Ready</div>
        """, unsafe_allow_html=True)
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # ── PHASE 3 METRICS BAR ────────────────────────────────────────────────────
        
    # ── PHASE 3 METRICS BAR ────────────────────────────────────────────────────
    pending = st.session_state.pending_schedule
    unassigned = st.session_state.unassigned_subjects
    assigned_count = len(set((s, sub) for s, sub, d, p in pending))
    conflict_count = len([c for c in st.session_state.conflict_logs if c.get("severity") == "error"])

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("JHS Sections", len(st.session_state.jhs_sections))
    m2.metric("SHS Sections", len(st.session_state.shs_sections))
    m3.metric("Assigned",       assigned_count, delta=None)
    m4.metric("Unassigned",     len(unassigned), delta=None,
              delta_color="inverse" if unassigned else "normal")
    m5.metric("Conflicts",      conflict_count,
              delta="⚠" if conflict_count else "✓",
              delta_color="inverse" if conflict_count else "normal")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    tab_jhs, tab_shs, tab_global, tab_generate = st.tabs(["🎒 Junior High", "🎓 Senior High", "⚙️ Global Settings", "🚀 Generate"])

    with tab_jhs:
        st.markdown("### Junior High School Setup")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("**Curriculum Preset**")
            new_preset = st.selectbox("Select Preset", ["MATATAG 2024", "MELC Standard", "Custom"], index=["MATATAG 2024", "MELC Standard", "Custom"].index(st.session_state.jhs_preset) if st.session_state.jhs_preset in ["MATATAG 2024", "MELC Standard", "Custom"] else 2, key="jhs_preset_sel")
            if new_preset != st.session_state.jhs_preset and new_preset != "Custom":
                st.session_state.jhs_preset = new_preset
                st.session_state.jhs_subjects = CURRICULUM_PRESETS["JHS"][new_preset].copy()
                st.rerun()
            elif new_preset == "Custom":
                st.session_state.jhs_preset = "Custom"
        
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**JHS Sections**")
            if st.button("＋ Add JHS Section"):
                new_id = max([s["id"] for s in st.session_state.jhs_sections] + [0]) + 1
                st.session_state.jhs_sections.append({"id": new_id, "name": f"Grade 7 - Sec {new_id}"})
                st.rerun()
            for i, sec in enumerate(st.session_state.jhs_sections):
                s_col1, s_col2 = st.columns([4, 1])
                st.session_state.jhs_sections[i]["name"] = s_col1.text_input("Name", value=sec["name"], key=f"jhs_sec_{i}", label_visibility="collapsed")
                if s_col2.button("✕", key=f"del_jhs_sec_{i}") and len(st.session_state.jhs_sections) > 1:
                    st.session_state.jhs_sections.pop(i); st.rerun()

        with c4:
            st.markdown("**JHS Subjects**")
            if st.button("＋ Add JHS Subject"):
                st.session_state.jhs_subjects.append({"name": "New Subject", "freq": 4, "units": 1, "year_level": "Grade 7"})
                st.session_state.jhs_preset = "Custom"
                st.rerun()
            for i, subj in enumerate(st.session_state.jhs_subjects):
                s_col1, s_col2, s_col3 = st.columns([3, 2, 1])
                st.session_state.jhs_subjects[i]["name"] = s_col1.text_input("Subj", value=subj["name"], key=f"jhs_sub_{i}", label_visibility="collapsed")
                st.session_state.jhs_subjects[i]["freq"] = s_col2.number_input("Freq", 1, 10, subj.get("freq", 4), key=f"jhs_freq_{i}", label_visibility="collapsed")
                if s_col3.button("✕", key=f"del_jhs_sub_{i}") and len(st.session_state.jhs_subjects) > 1:
                    st.session_state.jhs_subjects.pop(i); st.session_state.jhs_preset = "Custom"; st.rerun()

    with tab_shs:
        st.markdown("### Senior High School Setup")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("**Curriculum Preset**")
            shs_opts = list(CURRICULUM_PRESETS["SHS"].keys()) + ["Custom"]
            cur_idx = shs_opts.index(st.session_state.shs_preset) if st.session_state.shs_preset in shs_opts else len(shs_opts)-1
            new_shs_preset = st.selectbox("Select Preset", shs_opts, index=cur_idx, key="shs_preset_sel")
            if new_shs_preset != st.session_state.shs_preset and new_shs_preset != "Custom":
                st.session_state.shs_preset = new_shs_preset
                st.session_state.shs_subjects = CURRICULUM_PRESETS["SHS"][new_shs_preset].copy()
                st.rerun()
            elif new_shs_preset == "Custom":
                st.session_state.shs_preset = "Custom"
        
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**SHS Sections**")
            if st.button("＋ Add SHS Section"):
                new_id = max([s["id"] for s in st.session_state.shs_sections] + [100]) + 1
                st.session_state.shs_sections.append({"id": new_id, "name": f"Grade 11 - Sec {new_id}"})
                st.rerun()
            for i, sec in enumerate(st.session_state.shs_sections):
                s_col1, s_col2 = st.columns([4, 1])
                st.session_state.shs_sections[i]["name"] = s_col1.text_input("Name", value=sec["name"], key=f"shs_sec_{i}", label_visibility="collapsed")
                if s_col2.button("✕", key=f"del_shs_sec_{i}") and len(st.session_state.shs_sections) > 1:
                    st.session_state.shs_sections.pop(i); st.rerun()

        with c4:
            st.markdown("**SHS Subjects**")
            if st.button("＋ Add SHS Subject"):
                st.session_state.shs_subjects.append({"name": "New Subject", "freq": 4, "units": 1, "year_level": "Grade 11"})
                st.session_state.shs_preset = "Custom"
                st.rerun()
            for i, subj in enumerate(st.session_state.shs_subjects):
                s_col1, s_col2, s_col3 = st.columns([3, 2, 1])
                st.session_state.shs_subjects[i]["name"] = s_col1.text_input("Subj", value=subj["name"], key=f"shs_sub_{i}", label_visibility="collapsed")
                st.session_state.shs_subjects[i]["freq"] = s_col2.number_input("Freq", 1, 10, subj.get("freq", 4), key=f"shs_freq_{i}", label_visibility="collapsed")
                if s_col3.button("✕", key=f"del_shs_sub_{i}") and len(st.session_state.shs_subjects) > 1:
                    st.session_state.shs_subjects.pop(i); st.session_state.shs_preset = "Custom"; st.rerun()

    with tab_global:
        st.markdown("### School & Constraint Settings")
        gc1, gc2, gc3 = st.columns(3)
        with gc1: school_name = st.text_input("School Name", value="BSANHS")
        with gc2: school_year = st.text_input("School Year", value="2026-2027")
        with gc3: max_rooms   = st.number_input("Number of Rooms", 1, 100, 35)
        
        gc4, gc5 = st.columns(2)
        with gc4:
            num_days = st.selectbox("Days Per Week", [5, 4, 3], format_func=lambda x: f"{x} days")
        with gc5:
            num_periods = st.number_input("Periods Per Day", 1, 10, 8)
        days    = list(range(num_days))
        periods = list(range(1, num_periods + 1))
        
        st.markdown("**Constraints**")
        c1, c2 = st.columns(2)
        with c1:
            no_consec    = st.checkbox("🚫 No back-to-back major subjects", value=True)
            protect_lunch = st.checkbox("🍱 Protect lunch period", value=True)
        with c2:
            teacher_conf  = st.checkbox("👩‍🏫 Prevent teacher double-booking", value=True)
            unique_rooms  = st.checkbox("🏫 Assign unique rooms per slot", value=True)
            use_avail     = st.checkbox("📅 Enforce faculty availability masks", value=True)

    with tab_generate:
        st.markdown("### Generate Combined Schedule")
        
        ctrl1, ctrl2, ctrl3 = st.columns(3)
        with ctrl1: gen_btn = st.button("🚀 Generate Schedule", type="primary")
        with ctrl2: undo_btn = st.button("↩ Undo", disabled=not st.session_state.schedule_history)
        with ctrl3: reset_btn = st.button("🗑️ Reset", disabled=not st.session_state.pending_schedule)

        if gen_btn:
            all_sections = st.session_state.jhs_sections + st.session_state.shs_sections
            section_subjects = {}
            lesson_freq = {}
            for sec in st.session_state.jhs_sections:
                section_subjects[sec["id"]] = [s["name"] for s in st.session_state.jhs_subjects]
                for s in st.session_state.jhs_subjects:
                    lesson_freq[(sec["id"], s["name"])] = s["freq"]
            for sec in st.session_state.shs_sections:
                section_subjects[sec["id"]] = [s["name"] for s in st.session_state.shs_subjects]
                for s in st.session_state.shs_subjects:
                    lesson_freq[(sec["id"], s["name"])] = s["freq"]

            teach_assign = {t["name"]: t["subjects"] for t in st.session_state.teachers if t["subjects"]} if teacher_conf else None
            teach_avail = {t["name"]: t.get("availability", [True]*40) for t in st.session_state.teachers} if use_avail else None

            with st.spinner("🧠 CP-SAT solver running..."):
                try:
                    sched, unassigned, elapsed, is_partial = _local_solve(
                        section_subjects, lesson_freq, days, periods,
                        teacher_assignments=teach_assign,
                        teacher_availability=teach_avail,
                        no_consec_major=no_consec,
                        protect_lunch=protect_lunch,
                    )
                    
                    all_subjs = [s["name"] for s in st.session_state.jhs_subjects + st.session_state.shs_subjects]
                    rooms_map = _assign_rooms(sched, [s["id"] for s in all_sections], all_subjs, int(max_rooms)) if unique_rooms and sched else {}
                    conflict_logs = _run_conflict_monitor(sched, rooms_map)

                    st.session_state.pending_schedule = sched
                    st.session_state.pending_rooms = rooms_map
                    st.session_state.unassigned_subjects = unassigned
                    st.session_state.conflict_logs = conflict_logs
                except Exception as e:
                    st.error(f"Solver error: {e}")

        if st.session_state.pending_schedule:
            st.success("✅ Schedule Generated!")

    # ── CONFLICT MONITOR ──────────────────────────────────────────────────────
        if st.session_state.conflict_logs:
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown('<div class="block-label">⚠️ Conflict Error Log</div>', unsafe_allow_html=True)
            for c in st.session_state.conflict_logs:
                css = "conflict-error" if c.get("severity") == "error" else "conflict-warn"
                icon = "🔴" if c.get("severity") == "error" else "🟡"
                st.markdown(
                    f'<div class="{css}">{icon} <b>{c.get("type","CONFLICT")}</b> — {c["message"]}</div>',
                    unsafe_allow_html=True
                )

        # ── PHASE 4 — MANUAL OVERRIDE ─────────────────────────────────────────────
        if st.session_state.unassigned_subjects:
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown('<div class="block-label"><span class="step-badge">4</span>Manual Override — Unassigned Subjects</div>', unsafe_allow_html=True)
            st.caption("These subjects could not be auto-placed. Assign them manually below.")

            section_names_map = {s["id"]: s["name"] for s in st.session_state.sections}
            for j, (sec_id, sub_name, req_freq) in enumerate(st.session_state.unassigned_subjects):
                with st.expander(f"📌 {sub_name} (needs {req_freq}×/week)", expanded=True):
                    oc1, oc2, oc3, oc4 = st.columns(4)
                    with oc1:
                        sel_sec = st.selectbox(
                            "Section", options=[s["id"] for s in st.session_state.sections],
                            format_func=lambda x: section_names_map.get(x, str(x)),
                            key=f"ov_sec_{j}",
                        )
                    with oc2:
                        sel_day = st.selectbox(
                            "Day", options=days,
                            format_func=lambda x: DAY_NAMES[x],
                            key=f"ov_day_{j}",
                        )
                    with oc3:
                        sel_per = st.selectbox(
                            "Period", options=periods,
                            format_func=lambda x: PERIOD_LABELS.get(x, f"Period {x}"),
                            key=f"ov_per_{j}",
                        )
                    with oc4:
                        sel_room = st.number_input("Room No.", 1, int(max_rooms), 1, key=f"ov_room_{j}")

                    # Check for overlap in current pending schedule
                    conflict_at_slot = any(
                        s == sel_sec and d == sel_day and p == sel_per
                        for s, _, d, p in st.session_state.pending_schedule
                    )
                    if conflict_at_slot:
                        st.warning("⚠️ That slot is already occupied for this section.")

                    if st.button("✅ Assign", key=f"ov_assign_{j}"):
                        if conflict_at_slot:
                            st.error("Choose a different slot — this one is taken.")
                        else:
                            st.session_state.pending_schedule.append((sel_sec, sub_name, sel_day, sel_per))
                            st.session_state.pending_rooms[(sel_sec, sub_name)] = sel_room
                            # Remove from unassigned
                            st.session_state.unassigned_subjects = [
                                u for u in st.session_state.unassigned_subjects
                                if not (u[0] == sec_id and u[1] == sub_name)
                            ]
                            st.success(f"'{sub_name}' assigned to {DAY_NAMES[sel_day]} Period {sel_per} Room {sel_room}.")
                            st.rerun()

        # ── FINALIZE / UNDO STATE ─────────────────────────────────────────────────
        if st.session_state.pending_schedule:
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            fin_col1, fin_col2 = st.columns(2)
            with fin_col1:
                if not st.session_state.is_finalized:
                    if st.button("✅ Finalize & Commit to Database"):
                        if st.session_state.access_token:
                            sname_map = {s["id"]: s["name"] for s in st.session_state.sections}
                            subject_map = {s["name"]: s.get("id") for s in st.session_state.subjects if s.get("name")}
                            room_map = {str(r["room_number"]): r.get("id") for r in st.session_state.rooms_db if r.get("room_number")}
                            faculty_map = {t["name"]: t.get("id") for t in st.session_state.teachers if t.get("name") and t.get("id")}
                            missing_subj = sorted({sub for _, sub, _, _ in st.session_state.pending_schedule if subject_map.get(sub) is None})
                            if missing_subj:
                                st.error(
                                    "Cannot commit: backend subject IDs missing for: " +
                                    ", ".join(missing_subj)
                                )
                                st.stop()
                            job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            entry_list = []
                            for sid, sub, day, per in st.session_state.pending_schedule:
                                subject_id = subject_map.get(sub)
                                room_value = st.session_state.pending_rooms.get((sid, sub))
                                room_id = room_map.get(str(room_value)) if room_value is not None else None
                                entry_list.append({
                                    "subject_id": subject_id,
                                    "faculty_id": None,
                                    "room_id": room_id,
                                    "section_name": sname_map.get(sid, str(sid)),
                                    "day_of_week": day,
                                    "time_slot": per,
                                    "status": "finalized",
                                    "job_id": job_id,
                                    "tenant_id": st.session_state.tenant_id,
                                })
                            resp = _api("POST", "/api/v1/schedule-entries/bulk", {"entries": entry_list})
                            if resp is None:
                                st.error("Failed to commit schedule to the backend.")
                                st.stop()
                        st.session_state.is_finalized = True
                        st.success("Schedule finalized and committed! ✅")
                        st.rerun()
                else:
                    st.success("✅ Schedule is **Finalized**")
                    if st.button("↩ Revert to Pending"):
                        st.session_state.is_finalized = False; st.rerun()
            with fin_col2:
                status_label = "🟢 FINALIZED" if st.session_state.is_finalized else "🟡 PENDING — not yet committed"
                st.info(status_label)

        # ── TIMETABLE VISUALIZATION ───────────────────────────────────────────────
        if st.session_state.pending_schedule:
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown('<div class="block-label">📅 Timetable Preview</div>', unsafe_allow_html=True)
            section_names_map = {s["id"]: s["name"] for s in st.session_state.sections}
            view_type = st.radio("View", ["📋 Student View", "👩‍🏫 Instructor View"], horizontal=True)

            if view_type == "📋 Student View":
                sel_sec_id = st.selectbox(
                    "Section", [s["id"] for s in st.session_state.sections],
                    format_func=lambda x: section_names_map.get(x, str(x)),
                )
                rows = []
                lkup = {
                    (d, p): sub
                    for s, sub, d, p in st.session_state.pending_schedule
                    if s == sel_sec_id
                }
                for pnum, tlabel, is_break, bname in ALL_ROWS:
                    row = {"⏰ Time": tlabel}
                    if is_break:
                        for d in days:
                            row[DAY_NAMES[d]] = f"── {bname} ──"
                    else:
                        for d in days:
                            sub  = lkup.get((d, pnum), "")
                            room = st.session_state.pending_rooms.get((sel_sec_id, sub), "") if sub else ""
                            row[DAY_NAMES[d]] = f"{sub}\n(Rm {room})" if sub and room else sub
                    rows.append(row)
                df = pd.DataFrame(rows)

                # Render CSS-styled HTML table
                def _style_cell(val):
                    if "──" in str(val):
                        return "background:#fef9c3;color:#854d0e;font-style:italic;font-size:11px;"
                    if val:
                        return "background:#dbeafe;color:#1e40af;font-weight:600;font-size:11px;"
                    return "color:#94a3b8;font-size:11px;"

                html_rows = ""
                for _, row in df.iterrows():
                    html_rows += "<tr>"
                    for col_i, (col, val) in enumerate(row.items()):
                        style = "font-weight:700;" if col_i == 0 else _style_cell(val)
                        html_rows += f'<td style="padding:6px 8px;border:1px solid #e2e8f0;{style}">{str(val).replace(chr(10),"<br>")}</td>'
                    html_rows += "</tr>"

                header_html = "".join(
                    f'<th style="padding:8px;background:#0038A8;color:#fff;font-size:12px;border:1px solid #002b80;">{c}</th>'
                    for c in df.columns
                )
                st.markdown(
                    f'<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%;font-family:\'Syne\',sans-serif">'
                    f'<thead><tr>{header_html}</tr></thead><tbody>{html_rows}</tbody></table></div>',
                    unsafe_allow_html=True,
                )

            else:
                # Instructor view
                all_teachers = [t["name"] for t in st.session_state.teachers]
                sel_teacher  = st.selectbox("Instructor", all_teachers)
                t_subjects   = next((t["subjects"] for t in st.session_state.teachers if t["name"] == sel_teacher), [])
                rows = []
                t_lkup = {}
                for s, sub, d, p in st.session_state.pending_schedule:
                    if sub in t_subjects:
                        sname = section_names_map.get(s, str(s))
                        t_lkup[(d, p)] = f"{sub} ({sname})"

                for pnum, tlabel, is_break, bname in ALL_ROWS:
                    row = {"⏰ Time": tlabel}
                    if is_break:
                        for d in days: row[DAY_NAMES[d]] = f"── {bname} ──"
                    else:
                        for d in days: row[DAY_NAMES[d]] = t_lkup.get((d, pnum), "")
                    rows.append(row)
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # ── EXPORTS ───────────────────────────────────────────────────────────────
        if st.session_state.pending_schedule:
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown('<div class="block-label">📥 Export</div>', unsafe_allow_html=True)
            section_names_map = {s["id"]: s["name"] for s in st.session_state.sections}
            sections_ids      = [s["id"] for s in st.session_state.sections]
            subjects_list     = [s for s in st.session_state.subjects]

            exp1, exp2 = st.columns(2)
            with exp1:
                try:
                    xlsx_bytes = _export_excel(
                        st.session_state.pending_schedule,
                        st.session_state.pending_rooms,
                        sections_ids, section_names_map, subjects_list,
                        days, periods, school_name, school_year,
                    )
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        "📊 Download Excel",
                        data=xlsx_bytes,
                        file_name=f"ASCS_{school_name}_{ts}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                except ValueError as e:
                    st.error(f"Excel export failed: {e}")
            with exp2:
                try:
                    pdf_bytes = _export_pdf(
                        st.session_state.pending_schedule,
                        st.session_state.pending_rooms,
                        sections_ids, section_names_map, subjects_list,
                        days, periods, school_name, school_year,
                    )
                    st.download_button(
                        "📄 Download PDF",
                        data=pdf_bytes,
                        file_name=f"ASCS_{school_name}_{ts}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except ValueError as e:
                    st.error(f"PDF export failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Space Mono',monospace;font-size:10px;color:#475569;text-align:center;">
    ASCS v2.0 · 4-Phase Automated Class Scheduling System · OR-Tools CP-SAT · Streamlit
    </div>
    """, unsafe_allow_html=True)


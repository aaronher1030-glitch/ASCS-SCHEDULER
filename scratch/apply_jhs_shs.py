import re

APP_PATH = "Streamlit/App.py"

with open(APP_PATH, "r", encoding="utf-8") as f:
    content = f.read()

presets_code = """
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
"""

if "CURRICULUM_PRESETS" not in content:
    idx = content.find("def _init_state() -> None:")
    content = content[:idx] + presets_code + "\n" + content[idx:]


# Replace state initialization inside `_init_state`
state_defaults_replacement = """
        # Data
        "jhs_sections": [{"id": 1, "name": "Grade 7 - Mabini"}],
        "jhs_subjects": CURRICULUM_PRESETS["JHS"]["MATATAG 2024"].copy(),
        "jhs_preset": "MATATAG 2024",
        "shs_sections": [{"id": 101, "name": "Grade 11 - STEM A"}],
        "shs_subjects": CURRICULUM_PRESETS["SHS"]["Strengthened SHS (Core + STEM)"].copy(),
        "shs_preset": "Strengthened SHS (Core + STEM)",
        
        "sections": [], # Deprecated in favor of jhs/shs specific
        "subjects": [], # Deprecated in favor of jhs/shs specific
"""
content = re.sub(r'# Data\n\s*"sections": \[{"id": 1, "name": "Grade 7 - Mabini"}\],\n\s*"subjects": \[\n.*?\n\s*\],', state_defaults_replacement, content, flags=re.DOTALL)


# Update `_local_solve` to take `section_subjects` dict
local_solve_sig = """def _local_solve(
    section_subjects, lesson_frequency, days, periods,
    teacher_assignments=None, teacher_availability=None,
    no_consec_major=False, protect_lunch=False,
):
    \"\"\"Returns (schedule, unassigned, elapsed, is_partial).\"\"\"

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
"""

content = re.sub(r'def _local_solve\(\n.*?return sched or \[\], unassigned, total_elapsed, len\(unassigned\) > 0\n', local_solve_sig, content, flags=re.DOTALL)


# Now we must update the Dashboard UI section (under `elif page == "Dashboard":`)
# We will find where `m1, m2, m3, m4, m5 = st.columns(5)` is, and replace everything down to `st.markdown('<hr class="section-divider">', unsafe_allow_html=True)`
# Then replace Step 1, Step 2, Step 3, Step 4, Step 5, Step 6

dashboard_ui = """
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
"""

# Regex replacement from `pending = st.session_state.pending_schedule` up to `if st.session_state.conflict_logs:`
pattern = r'pending = st\.session_state\.pending_schedule.*?# ── CONFLICT MONITOR'
content = re.sub(pattern, dashboard_ui + '\n    # ── CONFLICT MONITOR', content, flags=re.DOTALL)

with open(APP_PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("Applied JHS/SHS logic and curriculum presets")

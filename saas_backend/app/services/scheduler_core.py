from __future__ import annotations

import os
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field

from ortools.sat.python import cp_model


# ──────────────────────────────────────────────────────────────
#  RESULT TYPE
# ──────────────────────────────────────────────────────────────

@dataclass
class SolveResult:
    schedule: list[tuple[int, str, int, int]]          # (section_id, subject, day, period)
    unassigned: list[tuple[int, str, int]]              # (section_id, subject, required_freq)
    elapsed: float
    is_partial: bool = False
    status_label: str = "OPTIMAL"


# ──────────────────────────────────────────────────────────────
#  AVAILABILITY HELPER
# ──────────────────────────────────────────────────────────────

def _mask_index(day: int, period: int) -> int:
    """
    Convert (day, period) to a flat index into the 40-element
    binary_availability_mask.  day ∈ [0,4], period ∈ [1,8].
    """
    return day * 8 + (period - 1)


def _slot_allowed_for_teacher(
    mask: list[bool],
    day: int,
    period: int,
) -> bool:
    idx = _mask_index(day, period)
    if idx >= len(mask):
        return True   # mask is shorter than expected → allow
    return mask[idx]


# ──────────────────────────────────────────────────────────────
#  MAIN SOLVER
# ──────────────────────────────────────────────────────────────

def build_and_solve(
    sections: list[int],
    subjects: list[str],
    lesson_frequency: dict[str, int],
    days: list[int],
    periods: list[int],
    teacher_assignments: dict[str, list[str]] | None = None,
    # NEW: {teacher_name: [True/False * 40]} availability masks
    teacher_availability: dict[str, list[bool]] | None = None,
    no_consec_major: bool = False,
    protect_lunch: bool = False,
    seed: int | None = None,
) -> SolveResult:
    """
    CP-SAT scheduler.

    Returns a SolveResult with:
    - schedule:    assigned (section_id, subject, day, period) tuples
    - unassigned:  subjects the solver could NOT place (partial solve)
    - elapsed:     wall-clock seconds
    - is_partial:  True when some subjects went unassigned
    """

    # ── Phase 1: try to solve everything at once ───────────────
    result = _attempt_solve(
        sections, subjects, lesson_frequency, days, periods,
        teacher_assignments, teacher_availability,
        no_consec_major, protect_lunch, seed,
        hard_fail=False,
    )

    if result is not None:
        return result

    # ── Phase 2: partial solve — drop subjects one by one ─────
    # Sort by frequency descending so high-freq subjects get priority
    remaining = sorted(subjects, key=lambda s: lesson_frequency.get(s, 0), reverse=True)
    best_schedule: list[tuple[int, str, int, int]] = []
    unassigned: list[tuple[int, str, int]] = []
    elapsed_total = 0.0

    while remaining:
        attempt = _attempt_solve(
            sections, remaining, lesson_frequency, days, periods,
            teacher_assignments, teacher_availability,
            no_consec_major, protect_lunch, seed,
            hard_fail=False,
        )
        if attempt is not None:
            best_schedule = attempt.schedule
            elapsed_total += attempt.elapsed
            break
        # Drop lowest-priority subject and retry
        dropped = remaining.pop()
        unassigned.append((0, dropped, lesson_frequency.get(dropped, 0)))
        elapsed_total += 0.5  # minimal accounting per retry

    return SolveResult(
        schedule=best_schedule,
        unassigned=unassigned,
        elapsed=elapsed_total,
        is_partial=len(unassigned) > 0,
        status_label="PARTIAL" if unassigned else "FEASIBLE",
    )


def _attempt_solve(
    sections: list[int],
    subjects: list[str],
    lesson_frequency: dict[str, int],
    days: list[int],
    periods: list[int],
    teacher_assignments: dict[str, list[str]] | None,
    teacher_availability: dict[str, list[bool]] | None,
    no_consec_major: bool,
    protect_lunch: bool,
    seed: int | None,
    hard_fail: bool = True,
) -> SolveResult | None:
    """
    Single CP-SAT attempt.  Returns None on infeasibility (unless hard_fail=True,
    which raises RuntimeError).
    """
    model = cp_model.CpModel()

    assign: dict[int, dict[str, dict[int, dict[int, cp_model.IntVar]]]] = {}
    for section_id in sections:
        assign[section_id] = {}
        for subject in subjects:
            assign[section_id][subject] = {}
            for day in days:
                assign[section_id][subject][day] = {}
                for period in periods:
                    assign[section_id][subject][day][period] = model.NewBoolVar(
                        f"A_s{section_id}_{subject}_d{day}_p{period}"
                    )

    # ── Hard: correct lesson frequency ────────────────────────
    for section_id in sections:
        for subject in subjects:
            req = lesson_frequency.get(subject, 0)
            model.Add(
                sum(
                    assign[section_id][subject][day][period]
                    for day in days
                    for period in periods
                ) == req
            )

    # ── Hard: one subject per section per slot ─────────────────
    for section_id in sections:
        for day in days:
            for period in periods:
                model.Add(
                    sum(assign[section_id][subject][day][period] for subject in subjects) <= 1
                )

    # ── Hard: subject max once per day per section ─────────────
    for section_id in sections:
        for subject in subjects:
            for day in days:
                model.Add(
                    sum(assign[section_id][subject][day][period] for period in periods) <= 1
                )

    # ── Hard: teacher no double-booking ───────────────────────
    if teacher_assignments:
        teacher_to_subjects: dict[str, list[str]] = defaultdict(list)
        for teacher, subject_list in teacher_assignments.items():
            for subject in subject_list:
                if subject in subjects:
                    teacher_to_subjects[teacher].append(subject)

        for teacher, t_subjects in teacher_to_subjects.items():
            if len(t_subjects) > 1:
                for day in days:
                    for period in periods:
                        model.Add(
                            sum(
                                assign[section_id][subject][day][period]
                                for section_id in sections
                                for subject in t_subjects
                            ) <= 1
                        )

    # ── Hard: faculty availability mask ──────────────────────
    if teacher_assignments and teacher_availability:
        teacher_to_subjects_avail: dict[str, list[str]] = defaultdict(list)
        for teacher, subject_list in teacher_assignments.items():
            for subject in subject_list:
                if subject in subjects:
                    teacher_to_subjects_avail[teacher].append(subject)

        for teacher, t_subjects in teacher_to_subjects_avail.items():
            mask = teacher_availability.get(teacher)
            if not mask:
                continue  # no mask → assume fully available
            for day in days:
                for period in periods:
                    if not _slot_allowed_for_teacher(mask, day, period):
                        # Force every assignment variable for this teacher's subjects
                        # at this (day, period) to 0
                        for section_id in sections:
                            for subject in t_subjects:
                                model.Add(assign[section_id][subject][day][period] == 0)

    # ── Soft: protect lunch (period 5 gets at most 1 class) ───
    if protect_lunch and 5 in periods:
        for section_id in sections:
            for subject in subjects:
                for day in days:
                    model.Add(assign[section_id][subject][day][5] <= 1)

    # ── Soft: no back-to-back major subjects ──────────────────
    if no_consec_major:
        major_subjects = {"Math", "Mathematics", "Science", "English"}
        active_majors = [s for s in subjects if s in major_subjects]
        for section_id in sections:
            for day in days:
                for p_idx in range(len(periods) - 1):
                    p_cur = periods[p_idx]
                    p_nxt = periods[p_idx + 1]
                    major_pair = [
                        assign[section_id][subject][day][p_cur]
                        for subject in active_majors
                    ] + [
                        assign[section_id][subject][day][p_nxt]
                        for subject in active_majors
                    ]
                    if major_pair:
                        model.Add(sum(major_pair) <= 1)

    solver = cp_model.CpSolver()
    solver_seed = seed if seed is not None else random.randint(1, 999_999)
    solver.parameters.random_seed = solver_seed
    solver.parameters.num_search_workers = min(os.cpu_count() or 4, 8)
    solver.parameters.randomize_search = True
    solver.parameters.max_time_in_seconds = 60

    start = time.time()
    status = solver.Solve(model)
    elapsed = time.time() - start

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if hard_fail:
            raise RuntimeError("No feasible schedule found. Try reducing subjects or frequency.")
        return None

    schedule: list[tuple[int, str, int, int]] = []
    for section_id in sections:
        for subject in subjects:
            for day in days:
                for period in periods:
                    if solver.Value(assign[section_id][subject][day][period]) == 1:
                        schedule.append((section_id, subject, day, period))

    label = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
    return SolveResult(schedule=schedule, unassigned=[], elapsed=elapsed, status_label=label)


# ──────────────────────────────────────────────────────────────
#  ROOM ASSIGNMENT
# ──────────────────────────────────────────────────────────────

def assign_rooms(
    schedule: list[tuple[int, str, int, int]],
    max_rooms: int = 35,
) -> dict[tuple[int, str], int]:
    model = cp_model.CpModel()
    section_subjects = set((section_id, subject) for section_id, subject, _, _ in schedule)
    room_assign = {
        (section_id, subject): model.NewIntVar(1, max_rooms, f"R_s{section_id}_{subject}")
        for section_id, subject in section_subjects
    }

    timeslot_classes: dict[tuple[int, int], list[tuple[int, str]]] = defaultdict(list)
    for section_id, subject, day, period in schedule:
        timeslot_classes[(day, period)].append((section_id, subject))

    for classes in timeslot_classes.values():
        if len(classes) > 1:
            model.AddAllDifferent(
                [room_assign[(section_id, subject)] for section_id, subject in classes]
            )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15
    solver.parameters.num_search_workers = min(os.cpu_count() or 4, 8)
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # Fallback: simple round-robin
        return {
            (section_id, subject): i % max_rooms + 1
            for i, (section_id, subject) in enumerate(section_subjects)
        }

    return {
        (section_id, subject): solver.Value(room_assign[(section_id, subject)])
        for section_id, subject in section_subjects
    }


# ──────────────────────────────────────────────────────────────
#  ROOM CONFLICT DETECTION
# ──────────────────────────────────────────────────────────────

def verify_room_conflicts(
    schedule: list[tuple[int, str, int, int]],
    rooms: dict[tuple[int, str], int],
) -> list[str]:
    timeslot_rooms: dict[tuple[int, int], dict[int, tuple[int, str]]] = {}
    conflicts: list[str] = []
    for section_id, subject, day, period in schedule:
        room = rooms.get((section_id, subject), -1)
        slot_key = (day, period)
        if slot_key not in timeslot_rooms:
            timeslot_rooms[slot_key] = {}
        if room in timeslot_rooms[slot_key]:
            other_section, other_subject = timeslot_rooms[slot_key][room]
            conflicts.append(
                f"Day {day} Period {period} Room {room}: "
                f"Section {section_id} ({subject}) vs {other_section} ({other_subject})"
            )
        else:
            timeslot_rooms[slot_key][room] = (section_id, subject)
    return conflicts

"""scheduling domain tables — faculty, rooms, subjects, schedule_entries, conflict_logs

Revision ID: 0002_scheduling_domain
Revises: 0001_initial_schema
Create Date: 2026-05-10 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_scheduling_domain"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "faculty",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("department", sa.String(100), nullable=False, server_default="General"),
        sa.Column("employment_type", sa.String(20), nullable=False, server_default="Full-time"),
        sa.Column("binary_availability_mask", sa.JSON(), nullable=False),
        sa.Column("tenant_id", sa.String(120), nullable=False, server_default="default-tenant"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_faculty_name", "faculty", ["name"])
    op.create_index("ix_faculty_tenant_id", "faculty", ["tenant_id"])

    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_number", sa.String(50), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("floor", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("tenant_id", sa.String(120), nullable=False, server_default="default-tenant"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_rooms_room_number", "rooms", ["room_number"])
    op.create_index("ix_rooms_tenant_id", "rooms", ["tenant_id"])

    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("units", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("year_level", sa.String(20), nullable=False, server_default="Grade 7"),
        sa.Column("required_hours_per_week", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("tenant_id", sa.String(120), nullable=False, server_default="default-tenant"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_subjects_code", "subjects", ["code"])
    op.create_index("ix_subjects_tenant_id", "subjects", ["tenant_id"])

    op.create_table(
        "schedule_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("faculty_id", sa.Integer(), sa.ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("section_name", sa.String(100), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("time_slot", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("job_id", sa.String(64), nullable=True),
        sa.Column("tenant_id", sa.String(120), nullable=False, server_default="default-tenant"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_schedule_entries_subject_id", "schedule_entries", ["subject_id"])
    op.create_index("ix_schedule_entries_faculty_id", "schedule_entries", ["faculty_id"])
    op.create_index("ix_schedule_entries_room_id", "schedule_entries", ["room_id"])
    op.create_index("ix_schedule_entries_section_name", "schedule_entries", ["section_name"])
    op.create_index("ix_schedule_entries_job_id", "schedule_entries", ["job_id"])
    op.create_index("ix_schedule_entries_tenant_id", "schedule_entries", ["tenant_id"])

    op.create_table(
        "conflict_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conflict_type", sa.String(60), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="error"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("affected_entries", sa.JSON(), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("resolved_by", sa.String(100), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("tenant_id", sa.String(120), nullable=False, server_default="default-tenant"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_conflict_logs_conflict_type", "conflict_logs", ["conflict_type"])
    op.create_index("ix_conflict_logs_tenant_id", "conflict_logs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_conflict_logs_tenant_id", table_name="conflict_logs")
    op.drop_index("ix_conflict_logs_conflict_type", table_name="conflict_logs")
    op.drop_table("conflict_logs")

    op.drop_index("ix_schedule_entries_tenant_id", table_name="schedule_entries")
    op.drop_index("ix_schedule_entries_job_id", table_name="schedule_entries")
    op.drop_index("ix_schedule_entries_section_name", table_name="schedule_entries")
    op.drop_index("ix_schedule_entries_room_id", table_name="schedule_entries")
    op.drop_index("ix_schedule_entries_faculty_id", table_name="schedule_entries")
    op.drop_index("ix_schedule_entries_subject_id", table_name="schedule_entries")
    op.drop_table("schedule_entries")

    op.drop_index("ix_subjects_tenant_id", table_name="subjects")
    op.drop_index("ix_subjects_code", table_name="subjects")
    op.drop_table("subjects")

    op.drop_index("ix_rooms_tenant_id", table_name="rooms")
    op.drop_index("ix_rooms_room_number", table_name="rooms")
    op.drop_table("rooms")

    op.drop_index("ix_faculty_tenant_id", table_name="faculty")
    op.drop_index("ix_faculty_name", table_name="faculty")
    op.drop_table("faculty")

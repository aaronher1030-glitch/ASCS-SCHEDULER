CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE schools (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'Asia/Manila',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE academic_years (
    id UUID PRIMARY KEY,
    school_id UUID NOT NULL REFERENCES schools(id),
    label TEXT NOT NULL,
    terms_per_year INT NOT NULL CHECK (terms_per_year BETWEEN 1 AND 4)
);

CREATE TABLE terms (
    id UUID PRIMARY KEY,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    term_index INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL
);

CREATE TABLE programs (
    id UUID PRIMARY KEY,
    school_id UUID NOT NULL REFERENCES schools(id),
    code TEXT NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE grade_levels (
    id UUID PRIMARY KEY,
    program_id UUID NOT NULL REFERENCES programs(id),
    name TEXT NOT NULL
);

CREATE TABLE sections (
    id UUID PRIMARY KEY,
    grade_level_id UUID NOT NULL REFERENCES grade_levels(id),
    name TEXT NOT NULL
);

CREATE TABLE subjects (
    id UUID PRIMARY KEY,
    program_id UUID NOT NULL REFERENCES programs(id),
    code TEXT NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE elective_groups (
    id UUID PRIMARY KEY,
    program_id UUID NOT NULL REFERENCES programs(id),
    strand_code TEXT NOT NULL,
    name TEXT NOT NULL,
    min_pick INT NOT NULL DEFAULT 1,
    max_pick INT NOT NULL DEFAULT 2
);

CREATE TABLE elective_group_subjects (
    elective_group_id UUID NOT NULL REFERENCES elective_groups(id),
    subject_id UUID NOT NULL REFERENCES subjects(id),
    PRIMARY KEY (elective_group_id, subject_id)
);

CREATE TABLE teachers (
    id UUID PRIMARY KEY,
    school_id UUID NOT NULL REFERENCES schools(id),
    name TEXT NOT NULL
);

CREATE TABLE rooms (
    id UUID PRIMARY KEY,
    school_id UUID NOT NULL REFERENCES schools(id),
    name TEXT NOT NULL,
    capacity INT NOT NULL DEFAULT 40
);

CREATE TABLE students (
    id UUID PRIMARY KEY,
    section_id UUID NOT NULL REFERENCES sections(id),
    learner_reference TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL
);

CREATE TABLE student_requests (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(id),
    term_id UUID NOT NULL REFERENCES terms(id),
    subject_id UUID NOT NULL REFERENCES subjects(id),
    rank_order INT NOT NULL,
    approval_status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE constraint_profiles (
    id UUID PRIMARY KEY,
    school_id UUID NOT NULL REFERENCES schools(id),
    name TEXT NOT NULL
);

CREATE TABLE constraint_rules (
    id UUID PRIMARY KEY,
    profile_id UUID NOT NULL REFERENCES constraint_profiles(id),
    rule_code TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE build_jobs (
    id UUID PRIMARY KEY,
    school_id UUID NOT NULL REFERENCES schools(id),
    term_id UUID NOT NULL REFERENCES terms(id),
    status TEXT NOT NULL,
    request_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE build_results (
    id UUID PRIMARY KEY,
    build_job_id UUID NOT NULL REFERENCES build_jobs(id),
    solve_seconds NUMERIC(8, 2) NOT NULL,
    result_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE conflict_items (
    id UUID PRIMARY KEY,
    build_result_id UUID NOT NULL REFERENCES build_results(id),
    code TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    suggested_action TEXT
);

CREATE TABLE resolution_actions (
    id UUID PRIMARY KEY,
    conflict_item_id UUID NOT NULL REFERENCES conflict_items(id),
    action_code TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE schedule_versions (
    id UUID PRIMARY KEY,
    build_result_id UUID NOT NULL REFERENCES build_results(id),
    status TEXT NOT NULL,
    version_no INT NOT NULL,
    snapshot_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE integration_connector_runs (
    id UUID PRIMARY KEY,
    school_id UUID NOT NULL REFERENCES schools(id),
    connector_type TEXT NOT NULL,
    direction TEXT NOT NULL,
    status TEXT NOT NULL,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    school_id UUID NOT NULL REFERENCES schools(id),
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

import React, { useState, useEffect } from 'react';
import AppShell from '../components/AppShell';
import { apiGet, apiPost } from '../lib/api';

interface BuildJob {
  job_id: string;
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
  error: string | null;
  artifact: {
    total_classes: number;
    solve_seconds: number;
    conflicts: { code: string; message: string; severity: string; suggested_action: string | null }[];
  } | null;
}

interface Faculty { id: number; name: string; department: string; }
interface Room { id: number; room_number: string; }
interface Subject { id: number; code: string; title: string; required_hours_per_week: number; }

export default function BuildPage() {
  const [faculty, setFaculty] = useState<Faculty[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [job, setJob] = useState<BuildJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    Promise.all([
      apiGet<Faculty[]>('/faculty').catch(() => []),
      apiGet<Room[]>('/rooms').catch(() => []),
      apiGet<Subject[]>('/subjects').catch(() => []),
    ]).then(([f, r, s]) => { setFaculty(f); setRooms(r); setSubjects(s); });
  }, []);

  const handleGenerate = async () => {
    if (subjects.length === 0) { setError('Add at least one subject before generating.'); return; }
    setLoading(true); setError(''); setJob(null);
    try {
      const payload = {
        tenant_id: 'local-tenant',
        school_id: 'bsanhs-001',
        school_name: 'Benigno S. Aquino National High School',
        school_year: '2025-2026',
        terms_per_year: 2,
        program: 'JHS',
        days_per_week: 5,
        periods_per_day: 8,
        max_rooms: Math.max(rooms.length, 10),
        sections: [{ id: 1, name: 'Section A' }],
        subjects: subjects.map(s => ({ name: s.title, freq: s.required_hours_per_week })),
        teachers: faculty.map(f => ({ name: f.name, subjects: [] })),
        constraints: {
          no_consec_major: true,
          protect_lunch: true,
          prevent_teacher_double_booking: true,
          unique_rooms: true,
        },
      };
      const result = await apiPost<BuildJob>('/build-jobs', payload);
      setJob(result);
      setPolling(true);
      pollJob(result.job_id);
    } catch (err: any) { setError(err.message); }
    setLoading(false);
  };

  const pollJob = async (jobId: string) => {
    let tries = 0;
    const interval = setInterval(async () => {
      tries++;
      try {
        const updated = await apiGet<BuildJob>(`/build-jobs/${jobId}`);
        setJob(updated);
        if (updated.status === 'succeeded' || updated.status === 'failed' || updated.status === 'published' || tries > 60) {
          clearInterval(interval);
          setPolling(false);
        }
      } catch { clearInterval(interval); setPolling(false); }
    }, 2000);
  };

  const statusColor = (s: string) => {
    if (s === 'succeeded' || s === 'published') return '#059669';
    if (s === 'failed') return '#dc2626';
    if (s === 'running') return '#2563eb';
    return '#64748b';
  };

  return (
    <AppShell activePage="Build Schedule">
      <h1 style={h1}>Build Schedule</h1>
      <p style={{ color: '#64748b', fontSize: 14, marginBottom: 32 }}>Generate an optimized timetable using the AI scheduling engine (Google OR-Tools CP-SAT).</p>

      {error && <div style={errBox}>{error}</div>}

      {/* Pre-flight stats */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 32, flexWrap: 'wrap' }}>
        {[
          { label: 'Faculty', count: faculty.length, color: '#0038A8' },
          { label: 'Rooms', count: rooms.length, color: '#059669' },
          { label: 'Subjects', count: subjects.length, color: '#d97706' },
        ].map(s => (
          <div key={s.label} style={{ ...card, padding: 20, minWidth: 160, flex: 1 }}>
            <div style={{ fontSize: 13, color: '#64748b', fontWeight: 600, marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontSize: 32, fontWeight: 700, color: s.color, fontFamily: 'Poppins, sans-serif' }}>{s.count}</div>
          </div>
        ))}
      </div>

      <button
        style={{ ...btnPrimary, opacity: loading || polling ? 0.7 : 1, padding: '14px 40px', fontSize: 16 }}
        onClick={handleGenerate}
        disabled={loading || polling}
      >
        {loading ? '⏳ Submitting…' : polling ? '⏳ Solving…' : '⚡ Generate Schedule'}
      </button>

      {/* Job status */}
      {job && (
        <div style={{ ...card, marginTop: 32, padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 style={{ fontFamily: 'Poppins, sans-serif', fontSize: 18, fontWeight: 700, color: '#1a1a1a', margin: 0 }}>Build Job</h2>
            <span style={{ padding: '4px 16px', borderRadius: 20, fontSize: 13, fontWeight: 700, color: '#fff', backgroundColor: statusColor(job.status) }}>
              {job.status.toUpperCase()}
            </span>
          </div>

          {/* Progress bar */}
          <div style={{ backgroundColor: '#e2e8f0', borderRadius: 8, height: 10, marginBottom: 16, overflow: 'hidden' }}>
            <div style={{ backgroundColor: statusColor(job.status), height: '100%', width: `${job.progress}%`, transition: 'width 0.5s ease', borderRadius: 8 }} />
          </div>
          <div style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>Progress: {job.progress}%  •  Job ID: {job.job_id.slice(0, 8)}…</div>

          {job.error && <div style={errBox}>{job.error}</div>}

          {job.artifact && (
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <div style={statBox}><div style={statLabel}>Classes Scheduled</div><div style={statValue}>{job.artifact.total_classes}</div></div>
              <div style={statBox}><div style={statLabel}>Solve Time</div><div style={statValue}>{job.artifact.solve_seconds.toFixed(2)}s</div></div>
              <div style={statBox}><div style={statLabel}>Conflicts</div><div style={{ ...statValue, color: job.artifact.conflicts.length > 0 ? '#dc2626' : '#059669' }}>{job.artifact.conflicts.length}</div></div>
            </div>
          )}

          {job.artifact && job.artifact.conflicts.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: '#1a1a1a', marginBottom: 12 }}>Detected Conflicts</h3>
              {job.artifact.conflicts.map((c, i) => (
                <div key={i} style={{ backgroundColor: '#fff7ed', border: '1px solid #fed7aa', borderRadius: 8, padding: 12, marginBottom: 8 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: '#9a3412', marginBottom: 4 }}>{c.code}</div>
                  <div style={{ fontSize: 13, color: '#78350f' }}>{c.message}</div>
                  {c.suggested_action && <div style={{ fontSize: 12, color: '#92400e', marginTop: 4, fontStyle: 'italic' }}>💡 {c.suggested_action}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}

const h1: React.CSSProperties = { fontFamily: 'Poppins, sans-serif', fontWeight: 700, fontSize: 24, color: '#0038A8', margin: 0, marginBottom: 8 };
const card: React.CSSProperties = { backgroundColor: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' };
const btnPrimary: React.CSSProperties = { backgroundColor: '#0038A8', color: '#fff', borderRadius: 10, fontWeight: 700, border: 'none', cursor: 'pointer', boxShadow: '0 4px 12px rgba(0,56,168,0.25)' };
const errBox: React.CSSProperties = { backgroundColor: '#fee2e2', color: '#b91c1c', padding: 12, borderRadius: 8, fontSize: 13, fontWeight: 500, marginBottom: 16 };
const statBox: React.CSSProperties = { flex: 1, minWidth: 140, backgroundColor: '#f8fafc', borderRadius: 8, padding: 16, border: '1px solid #e2e8f0' };
const statLabel: React.CSSProperties = { fontSize: 12, color: '#64748b', fontWeight: 600, marginBottom: 4 };
const statValue: React.CSSProperties = { fontSize: 24, fontWeight: 700, color: '#1a1a1a', fontFamily: 'Poppins, sans-serif' };

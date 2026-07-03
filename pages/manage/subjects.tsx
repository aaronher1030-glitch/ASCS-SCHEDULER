import React, { useState, useEffect } from 'react';
import AppShell from '../../components/AppShell';
import { apiGet, apiPost, apiDelete } from '../../lib/api';

interface Subject { id: number; code: string; title: string; units: number; year_level: string; required_hours_per_week: number; tenant_id: string; }

export default function SubjectsPage() {
  const [rows, setRows] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ code: '', title: '', units: 3, year_level: 'Grade 7', required_hours_per_week: 5 });
  const [error, setError] = useState('');

  const yearLevels = ['Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12'];

  const load = async () => {
    setLoading(true);
    try { setRows(await apiGet('/subjects')); } catch { setRows([]); }
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault(); setError('');
    try {
      await apiPost('/subjects', { ...form, tenant_id: 'local-tenant' });
      setForm({ code: '', title: '', units: 3, year_level: 'Grade 7', required_hours_per_week: 5 });
      setShowForm(false); load();
    } catch (err: any) { setError(err.message); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this subject?')) return;
    try { await apiDelete(`/subjects/${id}`); load(); } catch (err: any) { setError(err.message); }
  };

  return (
    <AppShell activePage="Subjects">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={h1}>Subject Management</h1>
        <button style={btnPrimary} onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : '+ Add Subject'}</button>
      </div>

      {error && <div style={errBox}>{error}</div>}

      {showForm && (
        <form onSubmit={handleCreate} style={card}>
          <div style={formRow}>
            <input style={{ ...input, width: 100 }} placeholder="Code (e.g. MATH7)" required value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} />
            <input style={input} placeholder="Subject Title" required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
            <select style={{ ...input, width: 120 }} value={form.year_level} onChange={e => setForm({ ...form, year_level: e.target.value })}>
              {yearLevels.map(y => <option key={y}>{y}</option>)}
            </select>
            <input style={{ ...input, width: 70 }} type="number" min={1} max={10} value={form.units} onChange={e => setForm({ ...form, units: Number(e.target.value) })} />
            <input style={{ ...input, width: 70 }} type="number" min={1} max={10} value={form.required_hours_per_week} onChange={e => setForm({ ...form, required_hours_per_week: Number(e.target.value) })} />
            <button type="submit" style={btnPrimary}>Save</button>
          </div>
        </form>
      )}

      <div style={card}>
        {loading ? <p style={{ padding: 24, color: '#64748b' }}>Loading…</p> : rows.length === 0 ? <p style={{ padding: 24, color: '#64748b' }}>No subjects yet. Click "+ Add Subject" to create one.</p> : (
          <table style={table}>
            <thead><tr>
              <th style={th}>Code</th><th style={th}>Title</th><th style={th}>Year Level</th><th style={th}>Units</th><th style={th}>Hrs/Week</th><th style={th}>Actions</th>
            </tr></thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.id}>
                  <td style={td}><strong>{r.code}</strong></td>
                  <td style={td}>{r.title}</td>
                  <td style={td}><span style={badgeBlue}>{r.year_level}</span></td>
                  <td style={td}>{r.units}</td>
                  <td style={td}>{r.required_hours_per_week}</td>
                  <td style={td}><button style={btnDanger} onClick={() => handleDelete(r.id)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <div style={{ marginTop: 16, fontSize: 13, color: '#64748b' }}>Total: {rows.length} subjects</div>
    </AppShell>
  );
}

const h1: React.CSSProperties = { fontFamily: 'Poppins, sans-serif', fontWeight: 700, fontSize: 24, color: '#0038A8', margin: 0 };
const card: React.CSSProperties = { backgroundColor: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' };
const table: React.CSSProperties = { width: '100%', borderCollapse: 'collapse', fontSize: 14 };
const th: React.CSSProperties = { textAlign: 'left', padding: '14px 16px', color: '#64748b', borderBottom: '1px solid #e2e8f0', fontWeight: 600, fontSize: 13 };
const td: React.CSSProperties = { padding: '14px 16px', borderBottom: '1px solid #e2e8f0', color: '#1a1a1a' };
const input: React.CSSProperties = { flex: 1, padding: '10px 14px', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 14, outline: 'none' };
const formRow: React.CSSProperties = { display: 'flex', gap: 12, padding: 20, alignItems: 'center', flexWrap: 'wrap' };
const btnPrimary: React.CSSProperties = { backgroundColor: '#0038A8', color: '#fff', padding: '10px 24px', borderRadius: 8, fontWeight: 600, fontSize: 14, border: 'none', cursor: 'pointer' };
const btnDanger: React.CSSProperties = { backgroundColor: '#fee2e2', color: '#b91c1c', padding: '6px 14px', borderRadius: 6, fontWeight: 600, fontSize: 12, border: 'none', cursor: 'pointer' };
const badgeBlue: React.CSSProperties = { backgroundColor: '#dbeafe', color: '#1e40af', padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600 };
const errBox: React.CSSProperties = { backgroundColor: '#fee2e2', color: '#b91c1c', padding: 12, borderRadius: 8, fontSize: 13, fontWeight: 500, marginBottom: 16 };

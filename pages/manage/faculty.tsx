import React, { useState, useEffect } from 'react';
import AppShell from '../../components/AppShell';
import { apiGet, apiPost, apiDelete } from '../../lib/api';

interface Faculty { id: number; name: string; department: string; employment_type: string; tenant_id: string; }

export default function FacultyPage() {
  const [rows, setRows] = useState<Faculty[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', department: 'General', employment_type: 'Full-time' });
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try { setRows(await apiGet('/faculty')); } catch { setRows([]); }
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault(); setError('');
    try {
      await apiPost('/faculty', { ...form, tenant_id: 'local-tenant' });
      setForm({ name: '', department: 'General', employment_type: 'Full-time' });
      setShowForm(false); load();
    } catch (err: any) { setError(err.message); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this faculty member?')) return;
    try { await apiDelete(`/faculty/${id}`); load(); } catch (err: any) { setError(err.message); }
  };

  return (
    <AppShell activePage="Faculty">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={h1}>Faculty Management</h1>
        <button style={btnPrimary} onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : '+ Add Faculty'}</button>
      </div>

      {error && <div style={errBox}>{error}</div>}

      {showForm && (
        <form onSubmit={handleCreate} style={card}>
          <div style={formRow}>
            <input style={input} placeholder="Full Name" required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            <input style={input} placeholder="Department" value={form.department} onChange={e => setForm({ ...form, department: e.target.value })} />
            <select style={input} value={form.employment_type} onChange={e => setForm({ ...form, employment_type: e.target.value })}>
              <option>Full-time</option><option>Part-time</option>
            </select>
            <button type="submit" style={btnPrimary}>Save</button>
          </div>
        </form>
      )}

      <div style={card}>
        {loading ? <p style={{ padding: 24, color: '#64748b' }}>Loading…</p> : rows.length === 0 ? <p style={{ padding: 24, color: '#64748b' }}>No faculty members yet. Click "+ Add Faculty" to create one.</p> : (
          <table style={table}>
            <thead><tr>
              <th style={th}>Name</th><th style={th}>Department</th><th style={th}>Type</th><th style={th}>Actions</th>
            </tr></thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.id}>
                  <td style={td}><strong>{r.name}</strong></td>
                  <td style={td}>{r.department}</td>
                  <td style={td}><span style={r.employment_type === 'Full-time' ? badgeGreen : badgeYellow}>{r.employment_type}</span></td>
                  <td style={td}><button style={btnDanger} onClick={() => handleDelete(r.id)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <div style={{ marginTop: 16, fontSize: 13, color: '#64748b' }}>Total: {rows.length} faculty members</div>
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
const badgeGreen: React.CSSProperties = { backgroundColor: '#d1fae5', color: '#065f46', padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600 };
const badgeYellow: React.CSSProperties = { backgroundColor: '#fef3c7', color: '#92400e', padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600 };
const errBox: React.CSSProperties = { backgroundColor: '#fee2e2', color: '#b91c1c', padding: 12, borderRadius: 8, fontSize: 13, fontWeight: 500, marginBottom: 16 };

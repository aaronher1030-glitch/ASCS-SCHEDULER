import React, { useState, useEffect } from 'react';
import AppShell from '../../components/AppShell';
import { apiGet, apiPost, apiDelete } from '../../lib/api';

interface Room { id: number; room_number: string; capacity: number; floor: number; is_available: boolean; tenant_id: string; }

export default function RoomsPage() {
  const [rows, setRows] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ room_number: '', capacity: 40, floor: 1 });
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try { setRows(await apiGet('/rooms')); } catch { setRows([]); }
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault(); setError('');
    try {
      await apiPost('/rooms', { ...form, is_available: true, tenant_id: 'local-tenant' });
      setForm({ room_number: '', capacity: 40, floor: 1 });
      setShowForm(false); load();
    } catch (err: any) { setError(err.message); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this room?')) return;
    try { await apiDelete(`/rooms/${id}`); load(); } catch (err: any) { setError(err.message); }
  };

  return (
    <AppShell activePage="Rooms">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={h1}>Room Management</h1>
        <button style={btnPrimary} onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : '+ Add Room'}</button>
      </div>

      {error && <div style={errBox}>{error}</div>}

      {showForm && (
        <form onSubmit={handleCreate} style={card}>
          <div style={formRow}>
            <input style={input} placeholder="Room Number (e.g. 201)" required value={form.room_number} onChange={e => setForm({ ...form, room_number: e.target.value })} />
            <input style={{ ...input, width: 100 }} type="number" min={1} placeholder="Capacity" value={form.capacity} onChange={e => setForm({ ...form, capacity: Number(e.target.value) })} />
            <input style={{ ...input, width: 80 }} type="number" min={1} placeholder="Floor" value={form.floor} onChange={e => setForm({ ...form, floor: Number(e.target.value) })} />
            <button type="submit" style={btnPrimary}>Save</button>
          </div>
        </form>
      )}

      <div style={card}>
        {loading ? <p style={{ padding: 24, color: '#64748b' }}>Loading…</p> : rows.length === 0 ? <p style={{ padding: 24, color: '#64748b' }}>No rooms yet. Click "+ Add Room" to create one.</p> : (
          <table style={table}>
            <thead><tr>
              <th style={th}>Room #</th><th style={th}>Floor</th><th style={th}>Capacity</th><th style={th}>Status</th><th style={th}>Actions</th>
            </tr></thead>
            <tbody>
              {rows.map(r => (
                <tr key={r.id}>
                  <td style={td}><strong>{r.room_number}</strong></td>
                  <td style={td}>{r.floor}</td>
                  <td style={td}>{r.capacity} seats</td>
                  <td style={td}><span style={r.is_available ? badgeGreen : badgeRed}>{r.is_available ? 'Available' : 'Unavailable'}</span></td>
                  <td style={td}><button style={btnDanger} onClick={() => handleDelete(r.id)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <div style={{ marginTop: 16, fontSize: 13, color: '#64748b' }}>Total: {rows.length} rooms</div>
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
const badgeRed: React.CSSProperties = { backgroundColor: '#fee2e2', color: '#b91c1c', padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600 };
const errBox: React.CSSProperties = { backgroundColor: '#fee2e2', color: '#b91c1c', padding: 12, borderRadius: 8, fontSize: 13, fontWeight: 500, marginBottom: 16 };

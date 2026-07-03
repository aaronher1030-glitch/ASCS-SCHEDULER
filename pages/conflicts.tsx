import React, { useState, useEffect } from 'react';
import AppShell from '../components/AppShell';
import { apiGet, apiPost } from '../lib/api';

interface ConflictLog {
  id: number;
  conflict_type: string;
  severity: string;
  message: string;
  affected_entries: number[];
  is_resolved: boolean;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

interface Summary {
  total: number;
  errors: number;
  warnings: number;
  resolved: number;
  unresolved: number;
}

export default function ConflictsPage() {
  const [logs, setLogs] = useState<ConflictLog[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [filter, setFilter] = useState<'all' | 'error' | 'warning'>('all');
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const [s, l] = await Promise.all([
        apiGet<Summary>('/conflict-logs/summary'),
        apiGet<ConflictLog[]>('/conflict-logs'),
      ]);
      setSummary(s);
      setLogs(l);
    } catch { setLogs([]); }
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const handleScan = async () => {
    setScanning(true); setError('');
    try {
      const result = await apiPost<{ conflicts_found: number }>('/conflict-logs/validate', {});
      setError(`Scan complete. Found ${result.conflicts_found} conflict(s).`);
      load();
    } catch (err: any) { setError(err.message); }
    setScanning(false);
  };

  const handleResolve = async (logId: number) => {
    try {
      await apiPost(`/conflict-logs/${logId}/resolve`, { resolved_by: 'admin' });
      load();
    } catch (err: any) { setError(err.message); }
  };

  const filtered = logs.filter(l => {
    if (filter === 'all') return true;
    return l.severity === filter;
  });

  const severityStyle = (s: string): React.CSSProperties => ({
    padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700,
    backgroundColor: s === 'error' ? '#fee2e2' : s === 'warning' ? '#fef3c7' : '#d1fae5',
    color: s === 'error' ? '#b91c1c' : s === 'warning' ? '#92400e' : '#065f46',
  });

  const typeIcon = (t: string) => {
    if (t.includes('ROOM')) return '🏫';
    if (t.includes('FACULTY')) return '👨‍🏫';
    if (t.includes('AVAILABILITY')) return '🕒';
    if (t.includes('HOURS')) return '📚';
    if (t.includes('MISSING')) return '⚠️';
    return '🔍';
  };

  return (
    <AppShell activePage="Conflicts">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={h1}>Conflict Center</h1>
        <button style={btnPrimary} onClick={handleScan} disabled={scanning}>
          {scanning ? '⏳ Scanning…' : '🔍 Run Validation Scan'}
        </button>
      </div>

      {error && <div style={{ ...infoBox, backgroundColor: error.startsWith('Scan') ? '#dbeafe' : '#fee2e2', color: error.startsWith('Scan') ? '#1e40af' : '#b91c1c' }}>{error}</div>}

      {/* Summary cards */}
      {summary && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 32, flexWrap: 'wrap' }}>
          {[
            { label: 'Total', value: summary.total, color: '#1a1a1a' },
            { label: 'Errors', value: summary.errors, color: '#dc2626' },
            { label: 'Warnings', value: summary.warnings, color: '#d97706' },
            { label: 'Resolved', value: summary.resolved, color: '#059669' },
            { label: 'Unresolved', value: summary.unresolved, color: '#7c3aed' },
          ].map(s => (
            <div key={s.label} style={{ ...card, padding: 20, flex: 1, minWidth: 120 }}>
              <div style={{ fontSize: 12, color: '#64748b', fontWeight: 600, marginBottom: 4 }}>{s.label}</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: s.color, fontFamily: 'Poppins, sans-serif' }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {(['all', 'error', 'warning'] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '8px 20px', borderRadius: 20, fontSize: 13, fontWeight: 600, cursor: 'pointer', border: 'none',
            backgroundColor: filter === f ? '#0038A8' : '#e2e8f0',
            color: filter === f ? '#fff' : '#475569',
          }}>
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1) + 's'}
          </button>
        ))}
      </div>

      {/* Conflict list */}
      <div style={card}>
        {loading ? <p style={{ padding: 24, color: '#64748b' }}>Loading…</p> :
         filtered.length === 0 ? <p style={{ padding: 24, color: '#64748b' }}>✅ No conflicts found. Your schedule is clean!</p> : (
          <div>
            {filtered.map(log => (
              <div key={log.id} style={{
                padding: '16px 20px', borderBottom: '1px solid #e2e8f0',
                display: 'flex', alignItems: 'flex-start', gap: 16,
                opacity: log.is_resolved ? 0.5 : 1,
              }}>
                <div style={{ fontSize: 24, lineHeight: 1 }}>{typeIcon(log.conflict_type)}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={severityStyle(log.severity)}>{log.severity.toUpperCase()}</span>
                    <span style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>{log.conflict_type}</span>
                    {log.is_resolved && <span style={{ fontSize: 11, color: '#059669', fontWeight: 700 }}>✓ RESOLVED</span>}
                  </div>
                  <div style={{ fontSize: 14, color: '#1a1a1a', lineHeight: 1.5 }}>{log.message}</div>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>
                    {new Date(log.created_at).toLocaleString()}
                    {log.resolved_by && ` • Resolved by ${log.resolved_by}`}
                  </div>
                </div>
                {!log.is_resolved && (
                  <button style={btnResolve} onClick={() => handleResolve(log.id)}>
                    ✓ Resolve
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}

const h1: React.CSSProperties = { fontFamily: 'Poppins, sans-serif', fontWeight: 700, fontSize: 24, color: '#0038A8', margin: 0 };
const card: React.CSSProperties = { backgroundColor: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' };
const btnPrimary: React.CSSProperties = { backgroundColor: '#0038A8', color: '#fff', padding: '10px 24px', borderRadius: 8, fontWeight: 600, fontSize: 14, border: 'none', cursor: 'pointer' };
const btnResolve: React.CSSProperties = { backgroundColor: '#d1fae5', color: '#065f46', padding: '6px 16px', borderRadius: 6, fontWeight: 600, fontSize: 12, border: 'none', cursor: 'pointer', whiteSpace: 'nowrap' };
const infoBox: React.CSSProperties = { padding: 12, borderRadius: 8, fontSize: 13, fontWeight: 500, marginBottom: 16 };

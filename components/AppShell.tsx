import React, { useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';

interface AppShellProps {
  children: React.ReactNode;
  activePage: string;
}

export default function AppShell({ children, activePage }: AppShellProps) {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('ascs_token');
    if (!token) router.push('/login');
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('ascs_token');
    router.push('/login');
  };

  const navItems = [
    { label: 'Dashboard', path: '/' },
    { label: 'Faculty', path: '/manage/faculty' },
    { label: 'Rooms', path: '/manage/rooms' },
    { label: 'Subjects', path: '/manage/subjects' },
    { label: 'Build Schedule', path: '/build' },
    { label: 'Conflicts', path: '/conflicts' },
  ];

  return (
    <div style={s.container}>
      <Head>
        <title>{activePage} — ASCS</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap" rel="stylesheet" />
      </Head>

      {/* Masthead */}
      <div style={s.masthead}>
        <div style={s.mastheadLeft}>
          <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Department_of_Education_%28DepEd%29.svg/1024px-Department_of_Education_%28DepEd%29.svg.png" alt="DepEd" style={{ height: 44 }} />
          <div>
            <div style={s.agencyName}>Benigno S. Aquino National High School</div>
            <div style={s.systemName}>Automated Class Scheduling System</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <span style={s.navLink}>Settings</span>
          <span style={s.navLink}>Help</span>
          <span style={s.navLink}>Report</span>
          <button style={s.logoutBtn} onClick={handleLogout}>Logout</button>
        </div>
      </div>

      <div style={s.body}>
        {/* Sidebar */}
        <nav style={s.sidebar}>
          {navItems.map(item => (
            <div
              key={item.label}
              style={activePage === item.label ? { ...s.navItem, ...s.navItemActive } : s.navItem}
              onClick={() => router.push(item.path)}
            >
              {item.label}
            </div>
          ))}
        </nav>

        {/* Content */}
        <main style={s.content}>{children}</main>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  container: { display: 'flex', flexDirection: 'column', height: '100vh', fontFamily: 'Inter, Poppins, sans-serif', backgroundColor: '#f4f6f9', color: '#1a1a1a' },
  masthead: { backgroundColor: '#fff', padding: '12px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', boxShadow: '0 2px 10px rgba(0,0,0,0.03)', position: 'sticky', top: 0, zIndex: 999 },
  mastheadLeft: { display: 'flex', alignItems: 'center', gap: 20 },
  agencyName: { fontFamily: 'Poppins, sans-serif', fontWeight: 700, fontSize: 18, color: '#0038A8', lineHeight: 1.2 },
  systemName: { fontFamily: 'Inter, sans-serif', fontWeight: 500, fontSize: 13, color: '#64748b' },
  navLink: { fontWeight: 600, fontSize: 14, color: '#475569', cursor: 'pointer' },
  logoutBtn: { backgroundColor: '#0038A8', color: '#fff', padding: '8px 24px', borderRadius: 8, fontWeight: 600, fontSize: 14, border: 'none', cursor: 'pointer', boxShadow: '0 4px 6px rgba(0,56,168,0.2)' },
  body: { display: 'flex', flex: 1, overflow: 'hidden' },
  sidebar: { width: 240, backgroundColor: '#fff', padding: '24px 16px', display: 'flex', flexDirection: 'column', borderRight: '1px solid #e2e8f0' },
  navItem: { padding: '12px 16px', marginBottom: 4, borderRadius: 8, cursor: 'pointer', color: '#475569', fontSize: 14, fontWeight: 500, transition: 'all 0.2s' },
  navItemActive: { backgroundColor: '#eff6ff', color: '#0038A8', borderLeft: '4px solid #0038A8', fontWeight: 600, paddingLeft: 12 },
  content: { flex: 1, padding: 32, overflowY: 'auto', backgroundColor: '#f4f6f9' },
};

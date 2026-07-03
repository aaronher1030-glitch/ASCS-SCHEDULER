import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useTheme } from '../components/ThemeProvider';
import { TimetableGrid } from '../components/TimetableGrid';
import { 
  MoonIcon, 
  SunIcon, 
  DashboardIcon, 
  CalendarIcon, 
  GearIcon, 
  ExitIcon 
} from '@radix-ui/react-icons';

export default function AppReplica() {
  const router = useRouter();
  const { resolvedTheme, toggleTheme } = useTheme();
  const [activeSidebar, setActiveSidebar] = useState('View Schedule');

  useEffect(() => {
    // Basic auth check
    const token = localStorage.getItem('ascs_token');
    // if (!token) {
    //   router.push('/login');
    // }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('ascs_token');
    router.push('/login');
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh', // Or 100dvh for mobile support
      minHeight: '100dvh',
      backgroundColor: 'var(--color-background)',
      color: 'var(--color-textPrimary)',
      fontFamily: 'var(--font-body)',
    }}>
      <Head>
        <title>SCAS - Automated Scheduling System</title>
        {/* We would load Geist or Outfit here */}
      </Head>

      {/* Modern Header / Masthead */}
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 'var(--spacing-md) var(--spacing-xl)',
        backgroundColor: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: 'var(--color-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 'bold',
            fontFamily: 'var(--font-heading)',
            fontSize: '18px',
          }}>
            S
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ 
              fontFamily: 'var(--font-heading)', 
              fontWeight: 700, 
              color: 'var(--color-primary)',
              fontSize: '18px',
              lineHeight: 1.2
            }}>
              Benigno S. Aquino NHS
            </span>
            <span style={{ 
              fontSize: '13px', 
              color: 'var(--color-textMuted)' 
            }}>
              Automated Class Scheduling System
            </span>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-lg)' }}>
          <button 
            onClick={toggleTheme}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--color-textSecondary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 'var(--spacing-sm)',
              borderRadius: 'var(--radius-sm)',
            }}
            title="Toggle Theme"
          >
            {resolvedTheme === 'dark' ? <SunIcon width={20} height={20} /> : <MoonIcon width={20} height={20} />}
          </button>
          
          <button 
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-sm)',
              backgroundColor: 'transparent',
              color: 'var(--color-danger)',
              border: '1px solid var(--color-border)',
              padding: 'var(--spacing-sm) var(--spacing-md)',
              borderRadius: 'var(--radius-sm)',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'var(--transition-default)',
            }}
          >
            <ExitIcon />
            Logout
          </button>
        </div>
      </header>

      <div style={{
        display: 'flex',
        flex: 1,
        overflow: 'hidden'
      }}>
        {/* Modern Sidebar */}
        <nav style={{
          width: '260px',
          backgroundColor: 'var(--color-surface)',
          borderRight: '1px solid var(--color-border)',
          display: 'flex',
          flexDirection: 'column',
          padding: 'var(--spacing-md)',
          gap: 'var(--spacing-sm)'
        }}>
          {[
            { id: 'Dashboard', icon: <DashboardIcon /> },
            { id: 'Manage', icon: <GearIcon /> },
            { id: 'View Schedule', icon: <CalendarIcon /> }
          ].map(item => (
            <div 
              key={item.id}
              onClick={() => setActiveSidebar(item.id)}
              style={{
                padding: 'var(--spacing-md)',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-md)',
                fontSize: '14px',
                fontWeight: activeSidebar === item.id ? 600 : 500,
                color: activeSidebar === item.id ? 'var(--color-primary)' : 'var(--color-textSecondary)',
                backgroundColor: activeSidebar === item.id ? 'var(--color-surfaceElevated)' : 'transparent',
                borderLeft: activeSidebar === item.id ? '4px solid var(--color-primary)' : '4px solid transparent',
                transition: 'var(--transition-default)'
              }}
            >
              {item.icon}
              {item.id}
            </div>
          ))}
          
          <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
             <button style={{
               padding: 'var(--spacing-md)',
               background: 'var(--color-accent)',
               color: '#000', // Gold accent usually needs dark text
               border: 'none',
               borderRadius: 'var(--radius-sm)',
               fontWeight: 600,
               cursor: 'pointer',
             }}>
               Run Generation
             </button>
          </div>
        </nav>

        {/* Main Content Area */}
        <main style={{
          flex: 1,
          padding: 'var(--spacing-xl)',
          overflowY: 'auto',
          backgroundColor: 'var(--color-background)'
        }}>
          {activeSidebar === 'View Schedule' && (
            <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <div style={{ marginBottom: 'var(--spacing-lg)' }}>
                <h1 style={{ 
                  margin: 0, 
                  fontFamily: 'var(--font-heading)',
                  fontSize: '28px',
                  color: 'var(--color-textPrimary)',
                  letterSpacing: '-0.5px'
                }}>
                  Active Timetable
                </h1>
                <p style={{ margin: 'var(--spacing-sm) 0 0 0', color: 'var(--color-textSecondary)' }}>
                  Semester 1, 2026-2027
                </p>
              </div>
              <TimetableGrid />
            </div>
          )}
          {activeSidebar === 'Dashboard' && <div>Dashboard implementation pending.</div>}
          {activeSidebar === 'Manage' && <div>Management implementation pending.</div>}
        </main>
      </div>
    </div>
  );
}

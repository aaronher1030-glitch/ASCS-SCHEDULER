import React, { useState } from 'react';
import { ClockIcon, MagnifyingGlassIcon } from '@radix-ui/react-icons';

interface Session {
  id: string;
  subjectCode: string;
  subjectName: string;
  time: string;
  classroom: string;
  courseSection: string;
  units: number;
  conflict?: boolean;
}

const mockSessions: Session[] = [
  { id: '1', subjectCode: 'GE208', subjectName: 'Science, Technology, and Society', time: 'Mon 08:00-09:30', classroom: '101', courseSection: 'BSEN 1-21', units: 3 },
  { id: '2', subjectCode: 'GE209', subjectName: "Rizal's Life and Works", time: 'Mon 09:30-11:00', classroom: '102', courseSection: 'BSEN 1-21', units: 3 },
  { id: '3', subjectCode: 'PED203', subjectName: 'Physical Education 3', time: 'Wed 19:00-21:00', classroom: '204', courseSection: 'BSEN 1-21', units: 2, conflict: true },
];

export const TimetableGrid: React.FC = () => {
  const [hoveredSession, setHoveredSession] = useState<string | null>(null);

  return (
    <div className="timetable-container" style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--spacing-md)',
      height: '100%',
    }}>
      {/* Controls */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingBottom: 'var(--spacing-sm)',
        borderBottom: '1px solid var(--color-border)',
      }}>
        <div style={{ display: 'flex', gap: 'var(--spacing-sm)', alignItems: 'center' }}>
          <div style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
          }}>
            <MagnifyingGlassIcon style={{ position: 'absolute', left: '10px', color: 'var(--color-textMuted)' }} />
            <input 
              placeholder="Search faculty or room..." 
              style={{
                padding: 'var(--spacing-sm) var(--spacing-sm) var(--spacing-sm) 32px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                background: 'var(--color-surfaceElevated)',
                color: 'var(--color-textPrimary)',
                outline: 'none',
              }} 
            />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
           <button style={{
             background: 'var(--color-surfaceElevated)',
             color: 'var(--color-textPrimary)',
             border: '1px solid var(--color-border)',
             padding: 'var(--spacing-sm) var(--spacing-md)',
             borderRadius: 'var(--radius-sm)',
             cursor: 'pointer',
             transition: 'var(--transition-default)',
           }}>
             Export PDF
           </button>
           <button style={{
             background: 'var(--color-primary)',
             color: '#fff',
             border: 'none',
             padding: 'var(--spacing-sm) var(--spacing-md)',
             borderRadius: 'var(--radius-sm)',
             cursor: 'pointer',
             fontWeight: 600,
             transition: 'var(--transition-default)',
             transform: 'scale(1)',
           }}
           onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.98)'}
           onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
           >
             + Add Session
           </button>
        </div>
      </div>

      {/* Grid Canvas */}
      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: 'var(--spacing-md)',
        overflowY: 'auto',
      }}>
        {mockSessions.map(session => (
          <div 
            key={session.id}
            onMouseEnter={() => setHoveredSession(session.id)}
            onMouseLeave={() => setHoveredSession(null)}
            style={{
              padding: 'var(--spacing-md)',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-surfaceElevated)',
              border: `1px solid ${session.conflict ? 'var(--color-danger)' : 'var(--color-glassBorder)'}`,
              boxShadow: hoveredSession === session.id ? 'var(--color-glassShadow)' : 'none',
              transition: 'var(--transition-default)',
              transform: hoveredSession === session.id ? 'translateY(-2px)' : 'translateY(0)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--spacing-sm)',
              position: 'relative',
            }}
          >
            {session.conflict && (
              <div style={{
                position: 'absolute',
                top: '-8px',
                right: '-8px',
                background: 'var(--color-danger)',
                color: '#fff',
                fontSize: '10px',
                fontWeight: 'bold',
                padding: '2px 6px',
                borderRadius: 'var(--radius-full)',
              }}>
                CONFLICT
              </div>
            )}
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <h3 style={{ margin: 0, fontSize: '16px', color: 'var(--color-textPrimary)' }}>
                {session.subjectCode}
              </h3>
              <span style={{ 
                fontSize: '12px', 
                background: 'var(--color-background)', 
                padding: '2px 8px',
                borderRadius: 'var(--radius-full)',
                color: 'var(--color-textSecondary)'
              }}>
                {session.courseSection}
              </span>
            </div>
            
            <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-textSecondary)' }}>
              {session.subjectName}
            </p>
            
            <div style={{ 
              marginTop: 'auto', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px', 
              fontSize: '13px', 
              color: 'var(--color-textMuted)',
              paddingTop: 'var(--spacing-sm)',
              borderTop: '1px solid var(--color-border)',
            }}>
              <ClockIcon /> {session.time} • Room {session.classroom}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

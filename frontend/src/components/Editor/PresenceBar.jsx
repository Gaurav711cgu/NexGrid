import React from 'react'
import { Users, Wifi } from 'lucide-react'

export function PresenceBar({ isConnected, users, userCursors }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0.4rem 1rem', background: 'rgba(9,13,22,0.9)',
      borderBottom: '1px solid rgba(255,255,255,0.06)', fontSize: '0.8rem', color: '#9ca3af'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <div className={isConnected ? "live-dot" : ""} style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: isConnected ? '#10b981' : '#f43f5e' }} />
          <span>{isConnected ? "CRDT Connected" : "Connecting..."}</span>
        </div>

        <div style={{ width: 1, height: 12, backgroundColor: 'rgba(255,255,255,0.1)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Users size={14} color="#818cf8" />
          <span>{users.length || 1} Active Engineer{users.length > 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Live Online User Avatars with Deterministic Color Pills */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        {users.map((u) => {
          const cursor = userCursors[u.user_id]
          return (
            <div
              key={u.user_id}
              title={`${u.display_name} ${cursor ? `(Ln ${cursor.line}, Col ${cursor.col})` : ''}`}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.3rem',
                background: 'rgba(255,255,255,0.05)', padding: '0.2rem 0.5rem',
                borderRadius: '12px', border: `1px solid ${u.color || '#6366f1'}`
              }}
            >
              <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: u.color || '#6366f1' }} />
              <span style={{ fontSize: '0.75rem', color: '#e5e7eb' }}>{u.display_name}</span>
              {cursor && (
                <span style={{ fontSize: '0.7rem', color: u.color || '#818cf8', fontFamily: 'Fira Code' }}>
                  L{cursor.line}:{cursor.col}
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

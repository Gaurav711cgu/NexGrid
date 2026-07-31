import React from 'react'
import { Users } from 'lucide-react'

export function PresenceBar({ isConnected, users, userCursors }) {
  return (
    <div
      role="region"
      aria-label="Active Presence & CRDT Connection Status"
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0.4rem 1rem', background: '#0d111a',
        borderBottom: '1px solid rgba(255,255,255,0.06)', fontSize: '0.8rem', color: '#9ca3af'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <div className={isConnected ? "live-dot" : ""} style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: isConnected ? '#10b981' : '#f43f5e' }} aria-hidden="true" />
          <span style={{ fontWeight: 500, color: isConnected ? '#34d399' : '#f87171' }}>
            {isConnected ? "CRDT Connected" : "Connecting..."}
          </span>
        </div>

        <div style={{ width: 1, height: 12, backgroundColor: 'rgba(255,255,255,0.1)' }} aria-hidden="true" />

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Users size={14} color="#818cf8" aria-hidden="true" />
          <span style={{ color: '#e5e7eb', fontWeight: 500 }}>{users.length || 1} Active Engineer{users.length > 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Dynamic ARIA Live Region for User Join/Leave & Cursor Pills */}
      <div aria-live="polite" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        {users.map((u) => {
          const cursor = userCursors[u.user_id]
          return (
            <div
              key={u.user_id}
              title={`${u.display_name} ${cursor ? `(Line ${cursor.line}, Column ${cursor.col})` : ''}`}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.3rem',
                background: 'rgba(255,255,255,0.05)', padding: '0.2rem 0.5rem',
                borderRadius: '12px', border: `1px solid ${u.color || '#6366f1'}`
              }}
            >
              <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: u.color || '#6366f1' }} aria-hidden="true" />
              <span style={{ fontSize: '0.75rem', color: '#f3f4f6', fontWeight: 500 }}>{u.display_name}</span>
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

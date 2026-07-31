import React, { useState } from 'react'
import { Code2, Share2, History, Play, Sparkles, Check, User, Activity, Layers, ArrowUpRight } from 'lucide-react'

export function RoomHeader({
  room,
  onRunCode,
  isRunning,
  onToggleAI,
  onToggleHistory,
  user,
  onOpenAuth,
  language,
  setLanguage,
  activeTab,
  setActiveTab
}) {
  const [copied, setCopied] = useState(false)

  const handleCopyCode = () => {
    if (room?.code) {
      navigator.clipboard.writeText(room.code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <header className="display-card" role="banner" style={{
      borderRadius: 0, borderLeft: 'none', borderRight: 'none', borderTop: 'none',
      borderBottom: '1px solid rgba(255,255,255,0.08)', padding: '0.6rem 1.5rem',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      background: '#07070a'
    }}>
      {/* Left: Brand Mark & Capsule Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <button
          onClick={() => setActiveTab('hero')}
          style={{ background: 'none', border: 'none', color: '#ffffff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontFamily: 'Fira Code', fontWeight: 800, fontSize: '1.1rem' }}
        >
          <span style={{ color: '#10b981' }}>&gt;_</span> NEXAGRID
        </button>

        <div className="badge-capsule" style={{ fontSize: '0.7rem' }}>
          <div className="live-dot-green" aria-hidden="true" />
          REAL-TIME CRDT PLATFORM
        </div>
      </div>

      {/* Center: Recruiter-First SPA Navigation Tabs (Zero Routing Issues) */}
      <nav aria-label="Main Application Navigation" style={{ display: 'flex', gap: '0.4rem' }}>
        <button
          onClick={() => setActiveTab('editor')}
          className={activeTab === 'editor' ? 'btn-solid-white' : 'btn-outline-white'}
          style={{ padding: '0.35rem 0.9rem', fontSize: '0.8rem', minHeight: '36px' }}
        >
          STUDIO EDITOR
        </button>

        <button
          onClick={() => setActiveTab('metrics')}
          className={activeTab === 'metrics' ? 'btn-solid-white' : 'btn-outline-white'}
          style={{ padding: '0.35rem 0.9rem', fontSize: '0.8rem', minHeight: '36px' }}
        >
          <Activity size={14} aria-hidden="true" /> SYSTEM METRICS & PIPELINES
        </button>

        <button
          onClick={() => setActiveTab('architecture')}
          className={activeTab === 'architecture' ? 'btn-solid-white' : 'btn-outline-white'}
          style={{ padding: '0.35rem 0.9rem', fontSize: '0.8rem', minHeight: '36px' }}
        >
          <Layers size={14} aria-hidden="true" /> ARCHITECTURE & SECURITY
        </button>
      </nav>

      {/* Right: Room Actions & User Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {activeTab === 'editor' && (
          <>
            {/* Target Language Select */}
            <select
              aria-label="Select Target Programming Language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="display-card-inner"
              style={{
                padding: '0.35rem 0.6rem', fontSize: '0.8rem', color: '#ffffff',
                fontFamily: 'Fira Code', outline: 'none', cursor: 'pointer'
              }}
            >
              <option value="python">Python 3</option>
              <option value="javascript">JavaScript</option>
              <option value="go">Go</option>
            </select>

            {/* History Logs */}
            <button onClick={onToggleHistory} className="btn-outline-white" aria-label="Open Execution History Logs" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', minHeight: '36px' }}>
              <History size={14} aria-hidden="true" /> Logs
            </button>

            {/* AI Assistant */}
            <button onClick={onToggleAI} className="btn-outline-white" aria-label="Open AI Assistant Drawer" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', minHeight: '36px' }}>
              <Sparkles size={14} color="#10b981" aria-hidden="true" /> AI
            </button>

            {/* Run Code */}
            <button onClick={onRunCode} className="btn-solid-white" aria-label="Execute Code in Sandbox Container" disabled={isRunning} style={{ padding: '0.35rem 0.9rem', fontSize: '0.8rem', minHeight: '36px' }}>
              <Play size={14} fill="black" aria-hidden="true" /> {isRunning ? 'Running...' : 'Run Code'}
            </button>
          </>
        )}

        {/* User Auth Profile */}
        {user ? (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            background: 'rgba(255,255,255,0.05)', padding: '0.3rem 0.6rem', borderRadius: '16px',
            border: '1px solid rgba(255,255,255,0.1)', fontSize: '0.8rem'
          }}>
            <div style={{ width: '22px', height: '22px', borderRadius: '50%', backgroundColor: user.avatar_color || '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 700, color: '#000' }}>
              {user.display_name ? user.display_name[0].toUpperCase() : 'U'}
            </div>
            <span>{user.display_name}</span>
          </div>
        ) : (
          <button onClick={onOpenAuth} className="btn-outline-white" aria-label="Open Sign In Dialog" style={{ padding: '0.35rem 0.8rem', fontSize: '0.8rem', minHeight: '36px' }}>
            <User size={14} aria-hidden="true" /> Sign In
          </button>
        )}
      </div>
    </header>
  )
}

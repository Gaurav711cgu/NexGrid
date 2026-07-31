import React, { useState } from 'react'
import { Code2, Share2, History, Play, Sparkles, Check, User } from 'lucide-react'

export function RoomHeader({
  room,
  onRunCode,
  isRunning,
  onToggleAI,
  onToggleHistory,
  user,
  onOpenAuth,
  language,
  setLanguage
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
    <header className="glass-panel" role="banner" style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0.6rem 1.5rem', borderRadius: 0, borderBottom: '1px solid rgba(255,255,255,0.08)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.6rem',
          background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(129,140,248,0.1))',
          padding: '0.4rem 0.8rem', borderRadius: '8px', border: '1px solid rgba(99,102,241,0.3)'
        }}>
          <Code2 size={20} color="#818cf8" aria-hidden="true" />
          <span style={{ fontWeight: 800, fontSize: '1.15rem', letterSpacing: '-0.02em', background: 'linear-gradient(135deg, #fff, #9ca3af)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            NexaGrid
          </span>
        </div>

        {room && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{room.name}</span>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              background: 'rgba(0,0,0,0.3)', padding: '0.25rem 0.6rem', borderRadius: '6px',
              fontSize: '0.8rem', fontFamily: 'Fira Code', color: '#9ca3af'
            }}>
              ROOM: <strong style={{ color: '#6366f1' }}>{room.code}</strong>
              <button
                onClick={handleCopyCode}
                aria-label="Copy Room Code to clipboard"
                title="Copy Room Code"
                style={{ background: 'none', border: 'none', color: copied ? '#10b981' : '#9ca3af', cursor: 'pointer', display: 'flex', alignItems: 'center', minWidth: '24px', minHeight: '24px', justifyContent: 'center' }}
              >
                {copied ? <Check size={14} aria-hidden="true" /> : <Share2 size={14} aria-hidden="true" />}
              </button>
            </div>
          </div>
        )}
      </div>

      <nav aria-label="Room Controls" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {/* Language Selector */}
        <label htmlFor="language-select" className="sr-only" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden' }}>Target Language</label>
        <select
          id="language-select"
          aria-label="Select Target Programming Language"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="input-field"
          style={{ width: '130px', padding: '0.4rem 0.6rem', fontSize: '0.85rem' }}
        >
          <option value="python">Python 3</option>
          <option value="javascript">JavaScript</option>
          <option value="go">Go</option>
        </select>

        {/* Execution Logs */}
        <button onClick={onToggleHistory} className="btn-secondary" aria-label="Open Execution History Logs" style={{ padding: '0.45rem 0.8rem', fontSize: '0.85rem' }}>
          <History size={16} aria-hidden="true" />
          <span>Logs</span>
        </button>

        {/* AI Pair Programmer */}
        <button onClick={onToggleAI} className="btn-secondary" aria-label="Open AI Assistant Drawer" style={{ padding: '0.45rem 0.8rem', fontSize: '0.85rem', borderColor: 'rgba(99,102,241,0.4)', color: '#818cf8' }}>
          <Sparkles size={16} color="#818cf8" aria-hidden="true" />
          <span>AI Assistant</span>
        </button>

        {/* Run Code Button */}
        <button onClick={onRunCode} className="btn-success" aria-label="Execute Code in Sandbox Container" disabled={isRunning} style={{ padding: '0.45rem 1rem', fontSize: '0.85rem' }}>
          <Play size={16} fill="white" aria-hidden="true" />
          <span>{isRunning ? 'Executing...' : 'Run Code'}</span>
        </button>

        {/* User Auth Profile Avatar */}
        {user ? (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            background: 'rgba(255,255,255,0.05)', padding: '0.35rem 0.75rem', borderRadius: '20px',
            border: '1px solid rgba(255,255,255,0.1)', fontSize: '0.85rem'
          }}>
            <div style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: user.avatar_color || '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700 }}>
              {user.display_name ? user.display_name[0].toUpperCase() : 'U'}
            </div>
            <span>{user.display_name}</span>
          </div>
        ) : (
          <button onClick={onOpenAuth} className="btn-secondary" aria-label="Open Sign In Dialog" style={{ padding: '0.45rem 0.8rem', fontSize: '0.85rem' }}>
            <User size={16} aria-hidden="true" />
            <span>Sign In</span>
          </button>
        )}
      </nav>
    </header>
  )
}

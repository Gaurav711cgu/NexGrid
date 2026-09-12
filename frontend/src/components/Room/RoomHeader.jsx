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
    <header className="glass-panel border-b border-border-subtle px-6 py-3 flex items-center justify-between sticky top-0 z-40">
      {/* Left: Brand Mark & Capsule Badge */}
      <div className="flex items-center gap-5">
        <button
          onClick={() => setActiveTab('hero')}
          className="flex items-center gap-2 font-mono font-bold text-lg text-text-primary hover:opacity-80 transition-opacity"
        >
          <span className="text-status-success">&gt;_</span> NEXAGRID
        </button>

        <div className="badge-capsule hidden md:flex">
          <div className="live-dot-green" aria-hidden="true" />
          REAL-TIME CRDT PLATFORM
        </div>
      </div>

      {/* Center: Recruiter-First SPA Navigation Tabs (Zero Routing Issues) */}
      <nav aria-label="Main Application Navigation" className="hidden lg:flex items-center gap-2 p-1 bg-neutral-bg2 rounded-lg border border-border-subtle">
        <button
          onClick={() => setActiveTab('editor')}
          className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === 'editor' ? 'bg-neutral-bg5 text-text-primary shadow-sm' : 'text-text-secondary hover:text-text-primary hover:bg-neutral-bg3'}`}
        >
          STUDIO EDITOR
        </button>

        <button
          onClick={() => setActiveTab('metrics')}
          className={`flex items-center gap-2 px-4 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === 'metrics' ? 'bg-neutral-bg5 text-text-primary shadow-sm' : 'text-text-secondary hover:text-text-primary hover:bg-neutral-bg3'}`}
        >
          <Activity size={14} aria-hidden="true" /> METRICS
        </button>

        <button
          onClick={() => setActiveTab('architecture')}
          className={`flex items-center gap-2 px-4 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === 'architecture' ? 'bg-neutral-bg5 text-text-primary shadow-sm' : 'text-text-secondary hover:text-text-primary hover:bg-neutral-bg3'}`}
        >
          <Layers size={14} aria-hidden="true" /> ARCHITECTURE
        </button>
      </nav>

      {/* Right: Room Actions & User Profile */}
      <div className="flex items-center gap-3">
        {activeTab === 'editor' && (
          <>
            {/* Target Language Select */}
            <select
              aria-label="Select Target Programming Language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="glass-input text-sm font-mono px-3 py-1.5 rounded-md text-text-primary cursor-pointer outline-none"
            >
              <option value="python">Python 3</option>
              <option value="javascript">JavaScript</option>
              <option value="go">Go</option>
            </select>

            {/* History Logs */}
            <button onClick={onToggleHistory} className="btn-outline-white text-sm" aria-label="Open Execution History Logs">
              <History size={14} aria-hidden="true" /> <span className="hidden sm:inline">Logs</span>
            </button>

            {/* AI Assistant */}
            <button onClick={onToggleAI} className="btn-outline-white text-sm" aria-label="Open AI Assistant Drawer">
              <Sparkles size={14} className="text-brand" aria-hidden="true" /> <span className="hidden sm:inline">AI</span>
            </button>

            {/* Run Code */}
            <button onClick={onRunCode} className="btn-solid-white text-sm" aria-label="Execute Code in Sandbox Container" disabled={isRunning}>
              <Play size={14} className="text-neutral-bg1" aria-hidden="true" /> {isRunning ? 'Running...' : 'Run Code'}
            </button>
          </>
        )}

        {/* User Auth Profile */}
        <div className="pl-2 border-l border-border-subtle ml-1">
          {user ? (
            <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-1.5 rounded-full text-sm">
              <div 
                className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-black"
                style={{ backgroundColor: user.avatar_color || '#10b981' }}
              >
                {user.display_name ? user.display_name[0].toUpperCase() : 'U'}
              </div>
              <span className="font-medium hidden sm:inline">{user.display_name}</span>
            </div>
          ) : (
            <button onClick={onOpenAuth} className="btn-outline-white text-sm">
              <User size={14} aria-hidden="true" /> Sign In
            </button>
          )}
        </div>
      </div>
    </header>
  )
}

import React, { useState, useEffect } from 'react'
import { api } from './lib/api'
import { useYjsDoc } from './hooks/useYjsDoc'
import { usePresence } from './hooks/usePresence'
import { useAIStream } from './hooks/useAIStream'

import { RoomHeader } from './components/Room/RoomHeader'
import { PresenceBar } from './components/Editor/PresenceBar'
import { CollaborativeEditor } from './components/Editor/CollaborativeEditor'
import { ExecutionPanel } from './components/Editor/ExecutionPanel'
import { AIPanel } from './components/Editor/AIPanel'
import { RoomHistory } from './components/Room/RoomHistory'
import { AuthModal } from './components/Auth/AuthModal'

import { Code2, Sparkles, ArrowRight, ShieldCheck, Cpu, Terminal, Users } from 'lucide-react'

export default function App() {
  const [user, setUser] = useState(null)
  const [room, setRoom] = useState(null)
  const [joinCodeInput, setJoinCodeInput] = useState('')
  const [language, setLanguage] = useState('python')
  const [currentCode, setCurrentCode] = useState('')
  
  // Modals & Panels State
  const [isAuthOpen, setIsAuthOpen] = useState(false)
  const [isAIOpen, setIsAIOpen] = useState(false)
  const [isHistoryOpen, setIsHistoryOpen] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [executionResult, setExecutionResult] = useState(null)
  const [error, setError] = useState('')

  // Check auth user status on load
  useEffect(() => {
    api.getMe().then((res) => {
      if (res?.user) setUser(res.user)
    }).catch(() => {})
  }, [])

  // Hooks for Y.js CRDT, Presence, AI Stream
  const { isConnected, bindToMonaco } = useYjsDoc(room?.id)
  const { users, userCursors, sendCursorPosition } = usePresence(room?.id)
  const { isGenerating, output, triggerAI, setOutput } = useAIStream(room?.id)

  const handleCreateRoom = async () => {
    setError('')
    try {
      const res = await api.createRoom({ language, name: `Collaborative ${language.toUpperCase()} Workspace` })
      setRoom(res)
      setLanguage(res.language)
      setCurrentCode(res.initial_code)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleJoinRoom = async (e) => {
    e.preventDefault()
    if (!joinCodeInput) return
    setError('')
    try {
      const res = await api.getRoomByCode(joinCodeInput)
      setRoom(res)
      setLanguage(res.language)
      setCurrentCode(res.initial_code)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleRunCode = async () => {
    if (!room) return
    setIsRunning(true)
    setExecutionResult(null)
    try {
      const res = await api.executeCode(room.id, { code: currentCode, language })
      setExecutionResult(res)
    } catch (err) {
      setExecutionResult({
        stdout: '',
        stderr: err.message,
        exit_code: -1,
        execution_time_ms: 0,
        blocked: true
      })
    } finally {
      setIsRunning(false)
    }
  }

  const handleApplyAICode = (aiCode) => {
    setCurrentCode(aiCode)
    setIsAIOpen(false)
  }

  // Home Landing Screen if not in a room
  if (!room) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(circle at 50% 20%, #1e1b4b 0%, #090d16 60%)',
        padding: '2rem'
      }}>
        <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} onAuthSuccess={(u) => setUser(u)} />

        <div className="glass-panel" style={{ width: '100%', maxWidth: '520px', padding: '2.5rem', textAlign: 'center' }}>
          <div style={{
            width: '64px', height: '64px', borderRadius: '16px',
            background: 'linear-gradient(135deg, #6366f1, #818cf8)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 1.5rem auto', boxShadow: '0 0 30px rgba(99,102,241,0.4)'
          }}>
            <Code2 size={36} color="white" />
          </div>

          <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.75rem', letterSpacing: '-0.03em' }}>
            NexaGrid
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '0.95rem', marginBottom: '2rem', lineHeight: 1.6 }}>
            Enterprise-grade real-time distributed code collaboration with CRDTs, sandboxed execution, and streaming AI.
          </p>

          {error && (
            <div style={{ background: 'rgba(244,63,94,0.15)', border: '1px solid rgba(244,63,94,0.3)', color: '#f43f5e', padding: '0.75rem', borderRadius: '8px', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <button onClick={handleCreateRoom} className="btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '0.8rem' }}>
              <span>Create New Workspace</span>
              <ArrowRight size={18} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', margin: '0.5rem 0' }}>
              <div style={{ flex: 1, height: 1, backgroundColor: 'rgba(255,255,255,0.1)' }} />
              <span style={{ fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em' }}>OR JOIN ROOM</span>
              <div style={{ flex: 1, height: 1, backgroundColor: 'rgba(255,255,255,0.1)' }} />
            </div>

            <form onSubmit={handleJoinRoom} style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                className="input-field"
                placeholder="Enter 6-character room code (e.g. K9X2LP)..."
                value={joinCodeInput}
                onChange={(e) => setJoinCodeInput(e.target.value.toUpperCase())}
                style={{ textTransform: 'uppercase', fontFamily: 'Fira Code', textAlign: 'center', letterSpacing: '0.1em' }}
              />
              <button type="submit" className="btn-secondary" style={{ padding: '0 1.25rem' }}>Join</button>
            </form>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginTop: '2.5rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.08)', fontSize: '0.75rem', color: '#9ca3af' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.3rem' }}>
              <Users size={16} color="#818cf8" />
              <span>Y.js CRDT Delta Sync</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.3rem' }}>
              <Terminal size={16} color="#10b981" />
              <span>POSIX Sandbox Engine</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.3rem' }}>
              <Sparkles size={16} color="#f59e0b" />
              <span>Streaming AI Pair Dev</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Full IDE Room Workspace Screen
  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <RoomHeader
        room={room}
        onRunCode={handleRunCode}
        isRunning={isRunning}
        onToggleAI={() => setIsAIOpen(!isAIOpen)}
        onToggleHistory={() => setIsHistoryOpen(!isHistoryOpen)}
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
        language={language}
        setLanguage={setLanguage}
      />

      <PresenceBar isConnected={isConnected} users={users} userCursors={userCursors} />

      <div style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden' }}>
        {/* Main Monaco Collaborative Editor Pane */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
          <CollaborativeEditor
            language={language}
            initialCode={room.initial_code}
            bindToMonaco={bindToMonaco}
            onCursorChange={sendCursorPosition}
            onChangeCode={setCurrentCode}
          />
          <ExecutionPanel
            executionResult={executionResult}
            isRunning={isRunning}
            onClose={() => setExecutionResult(null)}
          />
        </div>

        {/* AI Pair Programmer Drawer */}
        <AIPanel
          isOpen={isAIOpen}
          onClose={() => setIsAIOpen(false)}
          onTriggerAI={triggerAI}
          isGenerating={isGenerating}
          output={output}
          currentCode={currentCode}
          language={language}
          onApplyCode={handleApplyAICode}
        />
      </div>

      <RoomHistory isOpen={isHistoryOpen} onClose={() => setIsHistoryOpen(false)} roomId={room.id} />
      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} onAuthSuccess={(u) => setUser(u)} />
    </div>
  )
}

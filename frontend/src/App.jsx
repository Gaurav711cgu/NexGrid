import React, { useState, useEffect } from 'react'
import { api } from './lib/api'
import { useYjsDoc } from './hooks/useYjsDoc'
import { usePresence } from './hooks/usePresence'
import { useAIStream } from './hooks/useAIStream'

import { RoomHeader } from './components/Room/RoomHeader'
import { RoomHeroBanner } from './components/Room/RoomHeroBanner'
import { PresenceBar } from './components/Editor/PresenceBar'
import { CollaborativeEditor } from './components/Editor/CollaborativeEditor'
import { ExecutionPanel } from './components/Editor/ExecutionPanel'
import { AIPanel } from './components/Editor/AIPanel'
import { RoomHistory } from './components/Room/RoomHistory'
import { AuthModal } from './components/Auth/AuthModal'
import { MetricsPipelinesView } from './components/Room/MetricsPipelinesView'
import { ArchitectureView } from './components/Room/ArchitectureView'

export default function App() {
  const [user, setUser] = useState(null)
  const [room, setRoom] = useState(null)
  const [language, setLanguage] = useState('python')
  const [currentCode, setCurrentCode] = useState('')
  
  // Recruiter SPA Navigation Tab State (Zero Routing Errors)
  const [activeTab, setActiveTab] = useState('hero')

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

  // Auto-create room if entering editor tab without room
  useEffect(() => {
    if (activeTab === 'editor' && !room) {
      handleCreateRoom()
    }
  }, [activeTab])

  // Hooks for Y.js CRDT, Presence, AI Stream
  const { isConnected, bindToMonaco } = useYjsDoc(room?.id)
  const { users, userCursors, sendCursorPosition } = usePresence(room?.id)
  const { isGenerating, output, triggerAI } = useAIStream(room?.id)

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

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', backgroundColor: '#050505' }}>
      
      {/* Top Application Header Bar */}
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
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Content Area — Driven by State (Zero Routing Issues) */}
      <main style={{ flex: 1, overflow: activeTab === 'editor' ? 'hidden' : 'auto', position: 'relative', display: 'flex', flexDirection: 'column' }}>
        
        {/* Tab 0: Hero Overview (Reference Screenshot Theme) */}
        {activeTab === 'hero' && (
          <RoomHeroBanner
            onStartClick={() => setActiveTab('editor')}
            onViewArchitecture={() => setActiveTab('architecture')}
          />
        )}

        {/* Tab 1: Studio Editor View */}
        {activeTab === 'editor' && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
            <PresenceBar isConnected={isConnected} users={users} userCursors={userCursors} />

            <div style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden' }}>
              {/* Monaco Editor Container */}
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
                <CollaborativeEditor
                  language={language}
                  initialCode={room?.initial_code || ''}
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
          </div>
        )}

        {/* Tab 2: System Telemetry & Pipelines View */}
        {activeTab === 'metrics' && <MetricsPipelinesView />}

        {/* Tab 3: Architecture & Security View */}
        {activeTab === 'architecture' && <ArchitectureView />}
      </main>

      {/* Shared Modals */}
      {room && <RoomHistory isOpen={isHistoryOpen} onClose={() => setIsHistoryOpen(false)} roomId={room.id} />}
      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} onAuthSuccess={(u) => setUser(u)} />
    </div>
  )
}

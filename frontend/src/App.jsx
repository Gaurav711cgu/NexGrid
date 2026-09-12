import React, { useState, useEffect } from 'react'
import { RoomHeader } from './components/Room/RoomHeader'
import { RoomHeroBanner } from './components/Room/RoomHeroBanner'
import { MetricsPipelinesView } from './components/Room/MetricsPipelinesView'
import { ArchitectureView } from './components/Room/ArchitectureView'
import { CollaborativeEditor } from './components/Editor/CollaborativeEditor'
import { ExecutionPanel } from './components/Editor/ExecutionPanel'
import { AIPanel } from './components/Editor/AIPanel'
import { RoomHistory } from './components/Room/RoomHistory'
import { AuthModal } from './components/Auth/AuthModal'
import api from './lib/api'
import { AnimatePresence, motion } from 'framer-motion'

export default function App() {
  const [activeTab, setActiveTab] = useState('hero')
  
  // Room & Editor State
  const [room, setRoom] = useState(null)
  const [language, setLanguage] = useState('python')
  
  // UI Panels
  const [showAI, setShowAI] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [showAuth, setShowAuth] = useState(false)
  
  // Execution
  const [isRunning, setIsRunning] = useState(false)
  const [executionResult, setExecutionResult] = useState(null)

  // Auth State
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('nexagrid_user')
    return saved ? JSON.parse(saved) : null
  })

  // Mock Initialization for a "Global Room" if none selected
  useEffect(() => {
    if (!room) {
      setRoom({
        id: 'global-lobby',
        name: 'Global Edge Runtime',
        language: 'python'
      })
    }
  }, [room])

  const handleRunCode = async () => {
    if (!room) return
    setIsRunning(true)
    try {
      const res = await api.post(`/rooms/${room.id}/execute`, { language })
      setExecutionResult(res.data)
      setShowHistory(true)
    } catch (err) {
      setExecutionResult({ 
        status: 'error', 
        error: err.response?.data?.detail || err.message,
        execution_time_ms: 0
      })
    } finally {
      setIsRunning(false)
    }
  }

  const handleAuthSuccess = (userData) => {
    setUser(userData)
    localStorage.setItem('nexagrid_user', JSON.stringify(userData))
    setShowAuth(false)
  }

  return (
    <div className="flex flex-col h-screen bg-neutral-bg1 text-text-primary overflow-hidden font-sans">
      <RoomHeader 
        room={room}
        user={user}
        onOpenAuth={() => setShowAuth(true)}
        language={language}
        setLanguage={setLanguage}
        isRunning={isRunning}
        onRunCode={handleRunCode}
        onToggleAI={() => setShowAI(!showAI)}
        onToggleHistory={() => setShowHistory(!showHistory)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="flex-1 relative flex flex-col md:flex-row overflow-hidden bg-neutral-bg2">
        <AnimatePresence mode="wait">
          {activeTab === 'hero' && (
            <motion.div key="hero" className="flex-1 flex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <RoomHeroBanner />
            </motion.div>
          )}

          {activeTab === 'metrics' && (
            <motion.div key="metrics" className="flex-1 flex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <MetricsPipelinesView />
            </motion.div>
          )}

          {activeTab === 'architecture' && (
            <motion.div key="architecture" className="flex-1 flex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <ArchitectureView />
            </motion.div>
          )}

          {activeTab === 'editor' && (
            <motion.div key="editor" className="flex-1 flex flex-col md:flex-row w-full h-full" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              
              {/* Left Column: Editor & Terminal */}
              <div className="flex-1 flex flex-col min-w-0 h-full border-r border-border-subtle">
                <div className="flex-1 relative">
                  <CollaborativeEditor 
                    roomId={room?.id} 
                    language={language}
                    user={user}
                  />
                </div>
                
                {/* Terminal / Execution Panel */}
                <div className="h-64 border-t border-border-strong bg-neutral-bg3">
                  <ExecutionPanel result={executionResult} isRunning={isRunning} />
                </div>
              </div>

              {/* Right Column: AI Assistant Drawer */}
              <AnimatePresence>
                {showAI && (
                  <motion.div 
                    initial={{ x: '100%', opacity: 0, width: 0 }}
                    animate={{ x: 0, opacity: 1, width: 400 }}
                    exit={{ x: '100%', opacity: 0, width: 0 }}
                    transition={{ type: 'spring', bounce: 0, duration: 0.4 }}
                    className="h-full border-l border-border-subtle bg-neutral-bg2 overflow-hidden flex-shrink-0"
                  >
                    <div className="w-[400px] h-full">
                      <AIPanel 
                        roomId={room?.id} 
                        user={user}
                        onClose={() => setShowAI(false)}
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <AnimatePresence>
        {showHistory && activeTab === 'editor' && (
          <RoomHistory 
            roomId={room?.id}
            onClose={() => setShowHistory(false)}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showAuth && (
          <AuthModal 
            onClose={() => setShowAuth(false)}
            onSuccess={handleAuthSuccess}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

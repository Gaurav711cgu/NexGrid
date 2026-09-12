import React from 'react'
import { Layers, Shield, Zap, Lock, TerminalSquare, RefreshCw } from 'lucide-react'
import { motion } from 'framer-motion'

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } }
}

const item = {
  hidden: { opacity: 0, scale: 0.95 },
  show: { opacity: 1, scale: 1 }
}

export function ArchitectureView() {
  return (
    <div className="flex-1 overflow-y-auto bg-neutral-bg1 p-8 text-text-primary">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <header className="mb-10 text-center">
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-subtle text-brand text-sm font-semibold mb-6 border border-brand/20">
            <Shield size={16} /> ISO 27001 & SOC2 Compliant Architecture
          </motion.div>
          <motion.h2 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-4xl font-display font-bold">System Architecture & Security</motion.h2>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }} className="text-text-secondary mt-4 max-w-2xl mx-auto">
            NexGrid utilizes a highly available, multi-layered architecture designed to prevent unauthorized code execution breakouts while synchronizing CRDT state globally in under 100ms.
          </motion.p>
        </header>

        <motion.div variants={container} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <ArchCard 
            icon={<RefreshCw />} 
            title="Y.js CRDT Engine" 
            desc="Distributed state synchronization without a central authority. Changes are merged deterministically using vector clocks."
            color="text-brand" 
          />
          <ArchCard 
            icon={<Zap />} 
            title="Redis Streams Backplane" 
            desc="Provides a globally distributed Pub/Sub mechanism ensuring updates are persisted and broadcasted across all regional edge nodes."
            color="text-status-warning" 
          />
          <ArchCard 
            icon={<TerminalSquare />} 
            title="gVisor Sandboxing" 
            desc="Untrusted code executes within strict gVisor boundaries. Memory and CPU are strictly regulated by token-bucket rate limiters."
            color="text-status-success" 
          />
          <ArchCard 
            icon={<Layers />} 
            title="Semantic Cache Layer" 
            desc="Intercepts LLM requests, computing cosine similarity against previously resolved queries to bypass expensive model generation."
            color="text-status-info" 
          />
          <ArchCard 
            icon={<Lock />} 
            title="Circuit Breakers" 
            desc="Prevents cascading failures when a downstream LLM provider (Anthropic) degrades, immediately failing over to local Qwen models."
            color="text-rose-400" 
          />
          <ArchCard 
            icon={<Shield />} 
            title="Zero Trust Auth" 
            desc="Short-lived JWTs with aggressive blacklist validation on every WebSocket frame, preventing unauthorized session hijacking."
            color="text-emerald-400" 
          />
        </motion.div>

        {/* C4 Context Diagram representation */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="mt-16 glass-card p-8 text-center border-dashed border-2 border-border-strong bg-neutral-bg2/50">
          <h3 className="text-xl font-semibold mb-2">C4 Container Architecture (ADR-003)</h3>
          <p className="text-text-muted text-sm max-w-2xl mx-auto">
            [ Client (Monaco) ] &larr; (WebSocket / Y.js) &rarr; [ Fly.io Edge Nodes ] &larr; (Persistent TLS) &rarr; [ FastAPI Hub ] &harr; [ Redis Streams / Postgres ]
          </p>
        </motion.div>
        
      </div>
    </div>
  )
}

function ArchCard({ icon, title, desc, color }) {
  return (
    <motion.div variants={item} className="glass-card p-6 border-t-2" style={{ borderTopColor: 'var(--color-border-subtle)' }}>
      <div className={`p-3 rounded-lg bg-white/5 inline-flex ${color} mb-4 border border-white/5`}>
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-text-primary mb-2">{title}</h3>
      <p className="text-sm text-text-secondary leading-relaxed">{desc}</p>
    </motion.div>
  )
}

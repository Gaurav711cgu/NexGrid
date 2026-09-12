import React from 'react'
import { Terminal, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'

export function ExecutionPanel({ result, isRunning }) {
  if (isRunning) {
    return (
      <div className="h-full flex flex-col p-4 bg-neutral-bg3 text-text-primary font-mono text-sm">
        <div className="flex items-center gap-2 mb-4 text-brand">
          <Terminal size={16} />
          <span className="font-semibold">gVisor Sandbox</span>
          <span className="ml-auto text-xs opacity-50 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-brand animate-ping" /> Container warming...
          </span>
        </div>
        <div className="flex-1 flex items-center justify-center text-text-muted">
          Executing code in isolated container...
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="h-full flex flex-col p-4 bg-neutral-bg3 text-text-primary font-mono text-sm border-t-2 border-brand/50">
        <div className="flex items-center gap-2 mb-4 text-text-secondary">
          <Terminal size={16} />
          <span className="font-semibold text-text-primary">Terminal</span>
          <span className="ml-auto text-xs bg-neutral-bg4 px-2 py-0.5 rounded text-text-muted">IDLE</span>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center text-text-muted opacity-50">
          <Terminal size={32} className="mb-2" />
          <p>Awaiting execution...</p>
        </div>
      </div>
    )
  }

  const isError = result.status === 'error'

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="h-full flex flex-col bg-[#0d0d0d] text-gray-300 font-mono text-sm relative overflow-hidden border-t-2"
      style={{ borderTopColor: isError ? '#ef4444' : '#10b981' }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-2 bg-[#1a1a1a] border-b border-white/5">
        {isError ? (
          <AlertTriangle size={14} className="text-status-error" />
        ) : (
          <CheckCircle2 size={14} className="text-status-success" />
        )}
        <span className="font-bold text-white text-xs tracking-wider">
          {isError ? 'EXECUTION FAILED' : 'EXECUTION SUCCESS'}
        </span>
        
        <div className="ml-auto flex items-center gap-4 text-xs text-gray-500">
          {result.execution_time_ms !== undefined && (
            <span className="flex items-center gap-1">
              <Clock size={12} /> {result.execution_time_ms.toFixed(2)}ms
            </span>
          )}
          {result.memory_usage_mb && (
            <span>{result.memory_usage_mb.toFixed(1)} MB</span>
          )}
        </div>
      </div>

      {/* Output Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isError ? (
          <div>
            <div className="text-status-error font-bold mb-2">Traceback (most recent call last):</div>
            <pre className="whitespace-pre-wrap break-words text-rose-300 leading-relaxed font-mono">
              {result.error}
            </pre>
          </div>
        ) : (
          <pre className="whitespace-pre-wrap break-words leading-relaxed font-mono">
            {result.output || <span className="text-gray-500 italic">Program exited with no output.</span>}
          </pre>
        )}
      </div>
    </motion.div>
  )
}

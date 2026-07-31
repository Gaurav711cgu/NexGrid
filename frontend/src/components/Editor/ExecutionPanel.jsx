import React from 'react'
import { Terminal, ShieldAlert, CheckCircle2, Clock, Cpu, MemoryStick } from 'lucide-react'

export function ExecutionPanel({ executionResult, isRunning, onClose }) {
  if (!executionResult && !isRunning) return null

  return (
    <div className="glass-panel" style={{
      borderRadius: 0, borderTop: '1px solid rgba(255,255,255,0.1)',
      background: '#0d1117', height: '220px', display: 'flex', flexDirection: 'column'
    }}>
      {/* Terminal Bar Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0.4rem 1rem', background: '#161b22', borderBottom: '1px solid rgba(255,255,255,0.08)',
        fontSize: '0.85rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Terminal size={16} color="#818cf8" />
          <span style={{ fontWeight: 600, fontFamily: 'Fira Code', color: '#e5e7eb' }}>EXECUTION CONSOLE</span>
          {executionResult && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginLeft: '1rem', fontSize: '0.75rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: executionResult.exit_code === 0 ? '#10b981' : '#f43f5e' }}>
                {executionResult.exit_code === 0 ? <CheckCircle2 size={13} /> : <ShieldAlert size={13} />}
                Exit {executionResult.exit_code}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: '#9ca3af' }}>
                <Clock size={13} /> {executionResult.execution_time_ms}ms
              </span>
              {executionResult.metadata?.memory_limit_mb && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: '#9ca3af' }}>
                  <Cpu size={13} /> {executionResult.metadata.memory_limit_mb}MB Limit
                </span>
              )}
            </div>
          )}
        </div>

        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: '0.8rem' }}>
          Dismiss
        </button>
      </div>

      {/* Output Console Body */}
      <div style={{
        padding: '1rem', flex: 1, overflowY: 'auto', fontFamily: 'Fira Code',
        fontSize: '0.85rem', lineHeight: 1.5, color: '#f3f4f6'
      }}>
        {isRunning ? (
          <div style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div className="live-dot" /> Running code inside isolated sandbox container...
          </div>
        ) : executionResult ? (
          <div>
            {executionResult.blocked && (
              <div style={{ background: 'rgba(244,63,94,0.15)', border: '1px solid rgba(244,63,94,0.3)', color: '#f43f5e', padding: '0.5rem', borderRadius: '6px', marginBottom: '0.5rem' }}>
                <ShieldAlert size={14} style={{ display: 'inline', marginRight: '0.3rem' }} />
                {executionResult.stderr}
              </div>
            )}
            {executionResult.stdout && (
              <pre style={{ whiteSpace: 'pre-wrap', color: '#34d399' }}>{executionResult.stdout}</pre>
            )}
            {executionResult.stderr && !executionResult.blocked && (
              <pre style={{ whiteSpace: 'pre-wrap', color: '#f87171', marginTop: '0.3rem' }}>{executionResult.stderr}</pre>
            )}
            {!executionResult.stdout && !executionResult.stderr && !executionResult.blocked && (
              <span style={{ color: '#6b7280' }}>[Program finished with no output]</span>
            )}
          </div>
        ) : null}
      </div>
    </div>
  )
}

import React, { useState } from 'react'
import { Sparkles, X, Code, Wrench, FileText, Check } from 'lucide-react'

export function AIPanel({ isOpen, onClose, onTriggerAI, isGenerating, output, currentCode, language, onApplyCode }) {
  if (!isOpen) return null

  const [activeTab, setActiveTab] = useState('complete')
  const [errorContext, setErrorContext] = useState('')

  const handleAction = (action) => {
    onTriggerAI(action, currentCode, language, 1, errorContext)
  }

  return (
    <aside
      aria-label="AI Pair Programmer Assistant Drawer"
      className="glass-panel"
      style={{
        width: '380px', height: '100%', borderRadius: 0,
        borderLeft: '1px solid rgba(255,255,255,0.08)', background: '#0b0f19',
        display: 'flex', flexDirection: 'column'
      }}
    >
      {/* AI Panel Header */}
      <div style={{
        padding: '0.8rem 1rem', borderBottom: '1px solid rgba(255,255,255,0.08)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'rgba(99,102,241,0.08)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sparkles size={18} color="#818cf8" aria-hidden="true" />
          <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#e5e7eb' }}>AI Pair Programmer</span>
        </div>
        <button onClick={onClose} aria-label="Close AI Assistant Drawer" style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', minWidth: '32px', minHeight: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <X size={18} aria-hidden="true" />
        </button>
      </div>

      {/* Mode Action Buttons */}
      <div style={{ padding: '0.75rem', display: 'flex', gap: '0.4rem', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <button
          onClick={() => { setActiveTab('complete'); handleAction('complete'); }}
          className={activeTab === 'complete' ? 'btn-primary' : 'btn-secondary'}
          aria-label="Trigger AI Code Refactor"
          style={{ flex: 1, padding: '0.4rem', fontSize: '0.75rem', justifyContent: 'center', minHeight: '38px' }}
        >
          <Code size={14} aria-hidden="true" /> Refactor
        </button>
        <button
          onClick={() => { setActiveTab('explain'); handleAction('explain'); }}
          className={activeTab === 'explain' ? 'btn-primary' : 'btn-secondary'}
          aria-label="Trigger AI Code Explanation"
          style={{ flex: 1, padding: '0.4rem', fontSize: '0.75rem', justifyContent: 'center', minHeight: '38px' }}
        >
          <FileText size={14} aria-hidden="true" /> Explain
        </button>
        <button
          onClick={() => { setActiveTab('fix_error'); handleAction('fix_error'); }}
          className={activeTab === 'fix_error' ? 'btn-primary' : 'btn-secondary'}
          aria-label="Trigger AI Error Fix"
          style={{ flex: 1, padding: '0.4rem', fontSize: '0.75rem', justifyContent: 'center', minHeight: '38px' }}
        >
          <Wrench size={14} aria-hidden="true" /> Fix Error
        </button>
      </div>

      {/* Optional Error Context input if fixing error */}
      {activeTab === 'fix_error' && (
        <div style={{ padding: '0.5rem 0.75rem' }}>
          <label htmlFor="ai-error-input" className="sr-only" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden' }}>Error Context</label>
          <input
            id="ai-error-input"
            type="text"
            className="input-field"
            placeholder="Paste error message..."
            value={errorContext}
            onChange={(e) => setErrorContext(e.target.value)}
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.6rem' }}
          />
        </div>
      )}

      {/* Streaming Output Box with ARIA Live Region */}
      <div
        aria-live="polite"
        style={{
          flex: 1, padding: '1rem', overflowY: 'auto', fontSize: '0.85rem',
          lineHeight: 1.6, fontFamily: 'Fira Code', color: '#d1d5db'
        }}
      >
        {isGenerating && !output && (
          <div style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={16} aria-hidden="true" /> Streaming response token by token...
          </div>
        )}

        {output ? (
          <div>
            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{output}</pre>
          </div>
        ) : !isGenerating ? (
          <div style={{ color: '#6b7280', fontSize: '0.85rem', textAlign: 'center', marginTop: '2rem' }}>
            Select an action above to stream AI assistance over WebSockets.
          </div>
        ) : null}
      </div>

      {/* Apply Code to Editor Footer */}
      {output && !isGenerating && (
        <div style={{ padding: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.08)', background: '#111827' }}>
          <button
            onClick={() => onApplyCode(output)}
            className="btn-success"
            aria-label="Apply AI generated code to Monaco Editor"
            style={{ width: '100%', justifyContent: 'center', fontSize: '0.85rem' }}
          >
            <Check size={16} aria-hidden="true" /> Apply to Editor
          </button>
        </div>
      )}
    </aside>
  )
}

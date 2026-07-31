import React, { useState } from 'react'
import { Sparkles, X, Code, Wrench, FileText, Check, ArrowRight } from 'lucide-react'

export function AIPanel({ isOpen, onClose, onTriggerAI, isGenerating, output, currentCode, language, onApplyCode }) {
  if (!isOpen) return null

  const [activeTab, setActiveTab] = useState('complete')
  const [errorContext, setErrorContext] = useState('')

  const handleAction = (action) => {
    onTriggerAI(action, currentCode, language, 1, errorContext)
  }

  return (
    <div className="glass-panel" style={{
      width: '380px', height: '100%', borderRadius: 0,
      borderLeft: '1px solid rgba(255,255,255,0.08)', background: '#0b0f19',
      display: 'flex', flexDirection: 'column'
    }}>
      {/* AI Panel Header */}
      <div style={{
        padding: '0.8rem 1rem', borderBottom: '1px solid rgba(255,255,255,0.08)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'rgba(99,102,241,0.08)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sparkles size={18} color="#818cf8" />
          <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#e5e7eb' }}>AI Pair Programmer</span>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>
          <X size={18} />
        </button>
      </div>

      {/* Mode Action Buttons */}
      <div style={{ padding: '0.75rem', display: 'flex', gap: '0.4rem', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <button
          onClick={() => { setActiveTab('complete'); handleAction('complete'); }}
          className={activeTab === 'complete' ? 'btn-primary' : 'btn-secondary'}
          style={{ flex: 1, padding: '0.4rem', fontSize: '0.75rem', justifyContent: 'center' }}
        >
          <Code size={14} /> Refactor
        </button>
        <button
          onClick={() => { setActiveTab('explain'); handleAction('explain'); }}
          className={activeTab === 'explain' ? 'btn-primary' : 'btn-secondary'}
          style={{ flex: 1, padding: '0.4rem', fontSize: '0.75rem', justifyContent: 'center' }}
        >
          <FileText size={14} /> Explain
        </button>
        <button
          onClick={() => { setActiveTab('fix_error'); handleAction('fix_error'); }}
          className={activeTab === 'fix_error' ? 'btn-primary' : 'btn-secondary'}
          style={{ flex: 1, padding: '0.4rem', fontSize: '0.75rem', justifyContent: 'center' }}
        >
          <Wrench size={14} /> Fix Error
        </button>
      </div>

      {/* Optional Error Context input if fixing error */}
      {activeTab === 'fix_error' && (
        <div style={{ padding: '0.5rem 0.75rem' }}>
          <input
            type="text"
            className="input-field"
            placeholder="Paste error message..."
            value={errorContext}
            onChange={(e) => setErrorContext(e.target.value)}
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.6rem' }}
          />
        </div>
      )}

      {/* Streaming Output Box */}
      <div style={{
        flex: 1, padding: '1rem', overflowY: 'auto', fontSize: '0.85rem',
        lineHeight: 1.6, fontFamily: 'Fira Code', color: '#d1d5db'
      }}>
        {isGenerating && !output && (
          <div style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={16} className="animate-spin" /> Streaming response token by token...
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
            style={{ width: '100%', justifyContent: 'center', fontSize: '0.85rem' }}
          >
            <Check size={16} /> Apply to Editor
          </button>
        </div>
      )}
    </div>
  )
}

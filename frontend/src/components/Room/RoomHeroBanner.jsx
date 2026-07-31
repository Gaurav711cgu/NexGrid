import React from 'react'
import { ArrowRight, ArrowUpRight, Terminal, Check, ShieldAlert, Cpu } from 'lucide-react'

export function RoomHeroBanner({ onStartClick, onViewArchitecture }) {
  return (
    <section style={{ padding: '3.5rem 2rem 2rem 2rem', maxWidth: '1280px', margin: '0 auto' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '3rem', alignItems: 'center' }}>
        
        {/* Left Side: Hero Copy */}
        <div>
          <div className="badge-capsule" style={{ marginBottom: '1.5rem' }}>
            <div className="live-dot-green" aria-hidden="true" />
            REAL-TIME CRDT PLATFORM · V1.0
          </div>

          <h1 style={{
            fontSize: '3.2rem', fontWeight: 800, lineHeight: 1.1, letterSpacing: '-0.03em',
            marginBottom: '1.25rem', color: '#ffffff'
          }}>
            Execute and collaborate on code <span style={{ color: '#888888', fontWeight: 400 }}>through a single surface.</span>
          </h1>

          <p style={{
            color: '#999999', fontSize: '1.05rem', lineHeight: 1.6, maxWidth: '540px',
            marginBottom: '2rem'
          }}>
            NexaGrid unifies CRDT document state, POSIX-isolated execution, streaming AI pair programming, and full telemetry analytics under one surface. <strong style={{ color: '#ffffff' }}>Code is the command layer.</strong> The sandbox is the execution — governed by AST policies, backed by audit logs.
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '3rem' }}>
            <button onClick={onStartClick} className="btn-solid-white" aria-label="Start Collaborating in Studio Editor">
              Start collaborating <ArrowRight size={18} aria-hidden="true" />
            </button>
            <button onClick={onViewArchitecture} className="btn-outline-white" aria-label="View System Architecture">
              See architecture <ArrowUpRight size={18} aria-hidden="true" />
            </button>
          </div>

          {/* Bottom Spaced Monospace Ticker */}
          <div style={{
            display: 'flex', gap: '2rem', fontFamily: 'Fira Code', fontSize: '0.75rem',
            color: '#666666', letterSpacing: '0.08em', textTransform: 'uppercase'
          }}>
            <span>• STREAMING AI</span>
            <span>• POSIX SANDBOX</span>
            <span>• ZERO-CONFIG CURSOR PAGINATION</span>
          </div>
        </div>

        {/* Right Side: Orggle-style Terminal Display Board Card */}
        <div className="display-card" style={{ padding: '1.25rem' }}>
          {/* Card Window Controls & Header */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            paddingBottom: '0.8rem', marginBottom: '1rem',
            borderBottom: '1px solid rgba(255,255,255,0.08)', fontFamily: 'Fira Code', fontSize: '0.75rem', color: '#666666'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#ff5f56' }} />
              <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#ffbd2e' }} />
              <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#27c93f' }} />
            </div>
            <span style={{ letterSpacing: '0.05em' }}>NEXAGRID TERMINAL · DISPLAY BOARD</span>
          </div>

          {/* Code/Terminal Content */}
          <div style={{ fontFamily: 'Fira Code', fontSize: '0.82rem', lineHeight: 1.7, color: '#cccccc' }}>
            <p style={{ color: '#888888', marginBottom: '0.4rem' }}>&gt; python3 main.py --execute --sandbox=posix</p>

            <div style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981',
              fontWeight: 600, margin: '0.4rem 0 0.8rem 0'
            }}>
              <Check size={14} aria-hidden="true" />
              <span>EXECUTED_CLEANLY</span>
              <span style={{ color: '#666666', fontWeight: 400 }}>· exit_code=0</span>
            </div>

            <p style={{ color: '#888888', marginBottom: '0.4rem' }}>&gt; benchmark --room=room-9241 --telemetry</p>
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', padding: '0.6rem 0.8rem', borderRadius: '6px', marginBottom: '0.8rem' }}>
              <div style={{ color: '#f59e0b', fontWeight: 600 }}>
                NexaGrid Metrics: <span style={{ color: '#ffffff' }}>8.1ms CRDT Latency</span> · <span style={{ color: '#ffffff' }}>120ms Execution</span>
              </div>
              <div style={{ color: '#666666', fontSize: '0.75rem', marginTop: '0.2rem' }}>
                POSIX Limits: RLIMIT_AS=128MB · RLIMIT_CPU=5s · RLIMIT_NPROC=10
              </div>
            </div>

            {/* Embedded Approval Sub-Card */}
            <div className="display-card-inner" style={{ padding: '0.8rem 1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#666666', marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <span>AST SECURITY ANALYSIS</span>
                <span style={{ color: '#10b981', fontWeight: 600 }}>PASSED</span>
              </div>
              <div style={{ color: '#ffffff', fontWeight: 600, fontSize: '0.85rem' }}>
                Static AST Filter — 0 Blocked Imports Detected
              </div>
              <div style={{ color: '#888888', fontSize: '0.75rem', marginTop: '0.2rem' }}>
                Allowed: sys, math, json · Blocked: os.system, subprocess
              </div>
            </div>

            <p style={{ color: '#ffffff', marginTop: '0.8rem' }}>&gt; <span className="live-dot-green" style={{ display: 'inline-block' }} /></p>
          </div>
        </div>

      </div>
    </section>
  )
}

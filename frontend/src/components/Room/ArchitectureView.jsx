import React, { useState } from 'react'
import { Shield, Layers, HelpCircle, ChevronDown, ChevronUp, Lock, Check } from 'lucide-react'

export function ArchitectureView() {
  const [openQ, setOpenQ] = useState(0)

  const securityLayers = [
    { layer: "Layer 1: Edge / Network", tech: "Redis Sliding Window", detail: "60 req/min rate limit per user/IP using Redis sorted-set pipelines (`zremrangebyscore`, `zcard`, `zadd`, `expire`)." },
    { layer: "Layer 2: Authentication", tech: "Dual-Token Architecture", detail: "Short-lived access JWT (15m) + `HttpOnly; SameSite=Lax` refresh cookie (7d) with automatic token rotation." },
    { layer: "Layer 3: Revocation", tech: "Redis JTI Blacklist", detail: "O(1) Redis lookup checks `blacklist:<jti>` on every request. Immediate revocation on logout." },
    { layer: "Layer 4: Code Sandbox", tech: "Python AST Security Filter", detail: "Parses AST tree (`ast.parse`) to block dangerous imports (`os`, `subprocess`, `sys`, `socket`, `ctypes`) and builtins." },
    { layer: "Layer 5: OS Constraints", tech: "POSIX setrlimit Bounds", detail: "Pre-exec hook caps memory (`RLIMIT_AS` 128MB), CPU time (`RLIMIT_CPU` 5s), max processes (`RLIMIT_NPROC` 10)." },
    { layer: "Layer 6: Data Isolation", tech: "Declarative Partitioning", detail: "PostgreSQL range-partitioned `execution_logs` with JSONB GIN indexing and composite cursor seek indexes." },
  ]

  const interviewQA = [
    {
      q: "Q1: How do you handle two users typing at the same position simultaneously?",
      a: "NexaGrid uses Y.js (YATA algorithm). Every inserted character receives a globally unique ID `{clock, clientID}`. When two concurrent inserts happen at the exact same position, YATA breaks ties deterministically using `(originLeft, originRight, clientID)` without requiring central server arbitration."
    },
    {
      q: "Q2: How does your system scale beyond one backend instance?",
      a: "WebSocket connections are stateful. NexaGrid uses Redis Pub/Sub as a message backplane (`room:{id}:updates`). When any user sends a CRDT delta, the backend publishes it to Redis. Redis broadcasts to all backend subscriber instances, which deliver it to their local WebSocket connections."
    },
    {
      q: "Q3: Walk me through your sandbox security model.",
      a: "3 defense-in-depth layers: (1) Static Python `ast` module parsing blocks dangerous imports/builtins before execution. (2) Process isolation via independent subprocesses. (3) POSIX `setrlimit` caps memory to 128MB, CPU time to 5s, and child processes to 10."
    },
    {
      q: "Q4: Explain your database partition strategy.",
      a: "The `execution_logs` table is declaratively range-partitioned by `executed_at`. Queries filtering by date prune unused partitions automatically. Purging old logs is an instant `DROP TABLE execution_logs_y2025m01` without VACUUM overhead."
    },
    {
      q: "Q5: What's the circuit breaker for and how does it work?",
      a: "Protects against LLM API outages. Has 3 states: CLOSED (normal flow), OPEN (trips after 3 consecutive failures, fast-failing requests immediately), and HALF_OPEN (tests single recovery probe after 20s)."
    },
    {
      q: "Q6: Why cursor pagination instead of OFFSET/LIMIT?",
      a: "OFFSET scans and discards `N` previous rows ($O(N)$ degradation on deep pages). Cursor pagination uses a composite index seek `WHERE (executed_at, id) < (cursor_time, cursor_id)`, executing in $O(\\log N)$ time regardless of page depth."
    },
  ]

  return (
    <section style={{ padding: '2rem', maxWidth: '1280px', margin: '0 auto' }}>
      
      {/* Header */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div className="badge-capsule" style={{ marginBottom: '1rem' }}>
          <Layers size={14} color="#10b981" aria-hidden="true" />
          ARCHITECTURE & SECURITY MATRIX
        </div>
        <h2 style={{ fontSize: '2.2rem', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: '0.5rem' }}>
          6-Layer Defense-in-Depth & Systems Interview Deep-Dive
        </h2>
        <p style={{ color: '#999999', fontSize: '1rem', maxWidth: '680px' }}>
          Comprehensive architectural security specifications and technical interview defense rationale.
        </p>
      </div>

      {/* 6-Layer Security Grid */}
      <div style={{ marginBottom: '3.5rem' }}>
        <h3 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Shield size={18} color="#10b981" aria-hidden="true" /> Security Architecture Matrix
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {securityLayers.map((sec, idx) => (
            <div key={idx} className="display-card" style={{ padding: '1.25rem' }}>
              <div style={{ fontSize: '0.75rem', fontFamily: 'Fira Code', color: '#10b981', fontWeight: 700, marginBottom: '0.4rem' }}>
                {sec.layer}
              </div>
              <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.5rem' }}>
                {sec.tech}
              </h4>
              <p style={{ color: '#999999', fontSize: '0.85rem', lineHeight: 1.5 }}>
                {sec.detail}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Systems Interview Q&A Accordion */}
      <div>
        <h3 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <HelpCircle size={18} color="#10b981" aria-hidden="true" /> Systems Engineering Interview Q&A
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {interviewQA.map((item, idx) => {
            const isOpen = openQ === idx
            return (
              <div key={idx} className="display-card" style={{ padding: '1rem 1.25rem' }}>
                <button
                  onClick={() => setOpenQ(isOpen ? null : idx)}
                  aria-expanded={isOpen}
                  style={{
                    width: '100%', background: 'none', border: 'none', color: '#ffffff',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    cursor: 'pointer', textAlign: 'left', fontWeight: 600, fontSize: '0.95rem'
                  }}
                >
                  <span>{item.q}</span>
                  {isOpen ? <ChevronUp size={18} color="#10b981" /> : <ChevronDown size={18} color="#999999" />}
                </button>

                {isOpen && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.08)', color: '#cccccc', fontSize: '0.9rem', lineHeight: 1.6, fontFamily: 'Fira Code' }}>
                    {item.a}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

    </section>
  )
}

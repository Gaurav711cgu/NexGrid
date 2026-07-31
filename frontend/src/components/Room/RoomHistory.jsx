import React, { useState, useEffect } from 'react'
import { api } from '../../lib/api'
import { History, X, Clock, ShieldAlert, CheckCircle2, ChevronRight, BarChart2, Inbox } from 'lucide-react'

export function RoomHistory({ isOpen, onClose, roomId }) {
  const [logs, setLogs] = useState([])
  const [nextCursor, setNextCursor] = useState(null)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [analytics, setAnalytics] = useState([])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  useEffect(() => {
    if (isOpen && roomId) {
      fetchLogs()
      fetchAnalytics()
    }
  }, [isOpen, roomId])

  const fetchLogs = async (cursor = null) => {
    setLoading(true)
    try {
      const res = await api.getRoomHistory(roomId, cursor)
      if (cursor) {
        setLogs((prev) => [...prev, ...res.items])
      } else {
        setLogs(res.items)
      }
      setNextCursor(res.next_cursor)
      setHasMore(res.has_more)
    } catch (err) {
      console.error("Failed to load history logs:", err)
    } finally {
      setLoading(false)
    }
  }

  const fetchAnalytics = async () => {
    try {
      const res = await api.getRoomAnalytics(roomId)
      setAnalytics(res.analytics || [])
    } catch (err) {
      console.error("Failed to load room analytics:", err)
    }
  }

  if (!isOpen) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="history-modal-title"
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(9, 13, 22, 0.85)', backdropFilter: 'blur(12px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
      }}
    >
      <div className="glass-panel" style={{ width: '680px', maxHeight: '80vh', padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <h2 id="history-modal-title" style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <History color="#818cf8" aria-hidden="true" /> Execution History & Telemetry Analytics
          </h2>
          <button onClick={onClose} aria-label="Close Execution History Modal" style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', minWidth: '36px', minHeight: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        {/* SQL Analytics Summary Card */}
        {analytics.length > 0 && (
          <div style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.85rem' }}>
            <div style={{ fontWeight: 600, color: '#818cf8', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <BarChart2 size={14} aria-hidden="true" /> Advanced SQL Telemetry Summary (Window Functions)
            </div>
            <div style={{ display: 'flex', gap: '1.5rem', color: '#d1d5db' }}>
              {analytics.map((a, idx) => (
                <div key={idx}>
                  <strong>{a.language?.toUpperCase()}:</strong> {a.total_executions} runs | Avg: {a.avg_latency_ms}ms
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Execution Logs List */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {logs.map((log) => (
            <div key={log.id} style={{
              background: '#0f172a', border: '1px solid rgba(255,255,255,0.06)',
              padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.85rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', color: '#9ca3af' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: log.exit_code === 0 ? '#10b981' : '#f43f5e', fontWeight: 600 }}>
                  {log.exit_code === 0 ? <CheckCircle2 size={14} aria-hidden="true" /> : <ShieldAlert size={14} aria-hidden="true" />}
                  Exit Code {log.exit_code} ({log.language})
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <Clock size={12} aria-hidden="true" /> {log.execution_time_ms}ms | {new Date(log.executed_at).toLocaleTimeString()}
                </span>
              </div>
              {log.stdout && <pre style={{ fontFamily: 'Fira Code', color: '#34d399', fontSize: '0.8rem', whiteSpace: 'pre-wrap' }}>{log.stdout}</pre>}
              {log.stderr && <pre style={{ fontFamily: 'Fira Code', color: '#f87171', fontSize: '0.8rem', whiteSpace: 'pre-wrap' }}>{log.stderr}</pre>}
            </div>
          ))}

          {/* Skeleton Loading State */}
          {loading && logs.length === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ height: '50px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }} />
              <div style={{ height: '50px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }} />
            </div>
          )}

          {/* Empty State Design */}
          {logs.length === 0 && !loading && (
            <div style={{ color: '#6b7280', textAlign: 'center', padding: '3rem 1rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
              <Inbox size={32} color="#4b5563" aria-hidden="true" />
              <p style={{ fontWeight: 500, color: '#9ca3af' }}>No execution logs recorded yet</p>
              <p style={{ fontSize: '0.8rem' }}>Run code inside the editor to generate execution telemetry logs.</p>
            </div>
          )}
        </div>

        {/* O(1) Cursor Pagination Load More Button */}
        {hasMore && (
          <button
            onClick={() => fetchLogs(nextCursor)}
            className="btn-secondary"
            disabled={loading}
            aria-label="Load more logs using cursor pagination"
            style={{ marginTop: '1rem', justifyContent: 'center', fontSize: '0.85rem' }}
          >
            {loading ? 'Loading...' : 'Load More Logs (Cursor Pagination)'}
            <ChevronRight size={16} aria-hidden="true" />
          </button>
        )}
      </div>
    </div>
  )
}

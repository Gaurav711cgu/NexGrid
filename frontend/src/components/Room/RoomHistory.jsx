import React, { useState, useEffect } from 'react'
import { api } from '../../lib/api'
import { History, X, Clock, ShieldAlert, CheckCircle2, ChevronRight, BarChart2 } from 'lucide-react'

export function RoomHistory({ isOpen, onClose, roomId }) {
  const [logs, setLogs] = useState([])
  const [nextCursor, setNextCursor] = useState(null)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [analytics, setAnalytics] = useState([])

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
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div className="glass-panel" style={{ width: '650px', maxHeight: '80vh', padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <History color="#818cf8" /> Execution History & Telemetry Analytics
          </h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* SQL Analytics Summary Card */}
        {analytics.length > 0 && (
          <div style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.85rem' }}>
            <div style={{ fontWeight: 600, color: '#818cf8', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <BarChart2 size={14} /> Advanced SQL Telemetry Summary (Window Functions)
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
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: log.exit_code === 0 ? '#10b981' : '#f43f5e' }}>
                  {log.exit_code === 0 ? <CheckCircle2 size={14} /> : <ShieldAlert size={14} />}
                  Exit {log.exit_code} ({log.language})
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <Clock size={12} /> {log.execution_time_ms}ms | {new Date(log.executed_at).toLocaleTimeString()}
                </span>
              </div>
              {log.stdout && <pre style={{ fontFamily: 'Fira Code', color: '#34d399', fontSize: '0.8rem', whiteSpace: 'pre-wrap' }}>{log.stdout}</pre>}
              {log.stderr && <pre style={{ fontFamily: 'Fira Code', color: '#f87171', fontSize: '0.8rem', whiteSpace: 'pre-wrap' }}>{log.stderr}</pre>}
            </div>
          ))}

          {logs.length === 0 && !loading && (
            <div style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>No execution logs recorded yet.</div>
          )}
        </div>

        {/* O(1) Cursor Pagination Load More Button */}
        {hasMore && (
          <button
            onClick={() => fetchLogs(nextCursor)}
            className="btn-secondary"
            disabled={loading}
            style={{ marginTop: '1rem', justifyContent: 'center', fontSize: '0.85rem' }}
          >
            {loading ? 'Loading...' : 'Load More Logs (Cursor Pagination)'}
            <ChevronRight size={16} />
          </button>
        )}
      </div>
    </div>
  )
}

import { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'

export function usePresence(roomId, wsHost = window.location.host) {
  const [users, setUsers] = useState([])
  const [userCursors, setUserCursors] = useState({})
  const wsRef = useRef(null)

  useEffect(() => {
    if (!roomId) return

    let isMounted = true

    async function initPresence() {
      let ticket = ''
      try {
        const ticketRes = await api.getWsTicket()
        if (ticketRes?.ticket) ticket = ticketRes.ticket
      } catch (err) {
        // Fallback for guest mode
      }

      if (!isMounted) return

      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const queryParams = ticket ? `?token=${ticket}` : ''
      const wsUrl = `${wsProtocol}//${wsHost}/rooms/${roomId}/presence${queryParams}`

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'user_joined' || msg.type === 'user_left') {
            if (msg.all_users && isMounted) setUsers(msg.all_users)
          } else if (msg.type === 'cursor_update') {
            if (isMounted) {
              setUserCursors((prev) => ({
                ...prev,
                [msg.user_id]: { line: msg.line, col: msg.col, color: msg.color }
              }))
            }
          }
        } catch (err) {
          console.error("Presence WS message parse error:", err)
        }
      }
    }

    initPresence()

    return () => {
      isMounted = false
      if (wsRef.current) wsRef.current.close()
    }
  }, [roomId, wsHost])

  const sendCursorPosition = (line, col) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'cursor_update',
        line,
        col
      }))
    }
  }

  return { users, userCursors, sendCursorPosition }
}

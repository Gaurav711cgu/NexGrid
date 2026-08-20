import { useState, useEffect, useRef, useCallback } from 'react'
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'
import { MonacoBinding } from 'y-monaco'
import { api } from '../lib/api'

export function useYjsDoc(roomId, wsHost = window.location.host) {
  const [isConnected, setIsConnected] = useState(false)
  const docRef = useRef(null)
  const providerRef = useRef(null)
  const bindingRef = useRef(null)

  useEffect(() => {
    if (!roomId) return

    let isMounted = true
    const doc = new Y.Doc()
    docRef.current = doc

    async function initProvider() {
      // 1. Fetch single-use WebSocket authentication ticket
      let ticket = ''
      try {
        const ticketRes = await api.getWsTicket()
        if (ticketRes?.ticket) ticket = ticketRes.ticket
      } catch (err) {
        // Unauthenticated / public guest room fallback
      }

      if (!isMounted) return

      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const queryParams = ticket ? `?token=${ticket}` : ''
      const wsUrl = `${wsProtocol}//${wsHost}/rooms/${roomId}`

      const provider = new WebsocketProvider(wsUrl, `collab${queryParams}`, doc, {
        connect: true,
        WebSocketPolyfill: WebSocket,
        resyncInterval: 5000,
        maxBackoffTime: 10000
      })

      provider.on('status', ({ status }) => {
        if (isMounted) setIsConnected(status === 'connected')
      })

      providerRef.current = provider
    }

    initProvider()

    return () => {
      isMounted = false
      if (bindingRef.current) bindingRef.current.destroy()
      if (providerRef.current) providerRef.current.destroy()
      doc.destroy()
    }
  }, [roomId, wsHost])

  const bindToMonaco = useCallback((editor) => {
    if (!docRef.current || !editor || !providerRef.current) return

    const yText = docRef.current.getText('monaco')
    const awareness = providerRef.current.awareness

    if (bindingRef.current) {
      bindingRef.current.destroy()
    }

    bindingRef.current = new MonacoBinding(
      yText,
      editor.getModel(),
      new Set([editor]),
      awareness
    )

    return bindingRef.current
  }, [])

  return { isConnected, bindToMonaco, doc: docRef.current, provider: providerRef.current }
}

import { useState, useEffect, useRef, useCallback } from 'react'
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'
import { MonacoBinding } from 'y-monaco'

export function useYjsDoc(roomId, wsHost = window.location.host) {
  const [isConnected, setIsConnected] = useState(false)
  const docRef = useRef(null)
  const providerRef = useRef(null)
  const bindingRef = useRef(null)

  useEffect(() => {
    if (!roomId) return

    const doc = new Y.Doc()
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//${wsHost}/rooms/${roomId}`

    const provider = new WebsocketProvider(wsUrl, 'collab', doc, {
      connect: true,
      WebSocketPolyfill: WebSocket
    })

    provider.on('status', ({ status }) => {
      setIsConnected(status === 'connected')
    })

    docRef.current = doc
    providerRef.current = provider

    return () => {
      if (bindingRef.current) bindingRef.current.destroy()
      provider.destroy()
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

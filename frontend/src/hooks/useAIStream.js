import { useState, useRef, useCallback } from 'react'

export function useAIStream(roomId, wsHost = window.location.host) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [output, setOutput] = useState('')
  const wsRef = useRef(null)

  const triggerAI = useCallback((action, code, language = 'python', cursorLine = 0, context = '') => {
    setIsGenerating(true)
    setOutput('')

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//${wsHost}/rooms/${roomId}/ai-stream`

    if (wsRef.current) wsRef.current.close()

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({
        action,
        code,
        language,
        cursor_line: cursorLine,
        context
      }))
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'token') {
          setOutput((prev) => prev + msg.delta)
        } else if (msg.type === 'complete') {
          setIsGenerating(false)
          ws.close()
        }
      } catch (e) {
        console.error("AI stream parse error:", e)
      }
    }

    ws.onerror = () => {
      setIsGenerating(false)
    }

    ws.onclose = () => {
      setIsGenerating(false)
    }
  }, [roomId, wsHost])

  return { isGenerating, output, triggerAI, setOutput }
}

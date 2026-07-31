import React, { useRef, useEffect } from 'react'
import Editor from '@monaco-editor/react'

export function CollaborativeEditor({ language, initialCode, bindToMonaco, onCursorChange, onChangeCode }) {
  const editorRef = useRef(null)

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor

    // Bind Monaco editor instance to Y.js CRDT provider
    if (bindToMonaco) {
      bindToMonaco(editor)
    }

    // Set editor initial default code if empty
    if (initialCode && !editor.getValue()) {
      editor.setValue(initialCode)
    }

    // Track local cursor movement for multi-user presence
    editor.onDidChangeCursorPosition((e) => {
      if (onCursorChange) {
        onCursorChange(e.position.lineNumber, e.position.column)
      }
    })

    // Track code changes
    editor.onDidChangeModelContent(() => {
      if (onChangeCode) {
        onChangeCode(editor.getValue())
      }
    })
  }

  return (
    <div style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      <Editor
        height="100%"
        language={language === 'python' ? 'python' : language === 'javascript' ? 'javascript' : 'go'}
        theme="vs-dark"
        options={{
          fontSize: 14,
          fontFamily: "'Fira Code', monospace",
          minimap: { enabled: true },
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          lineNumbers: 'on',
          renderLineHighlight: 'all',
          automaticLayout: true,
          padding: { top: 12, bottom: 12 }
        }}
        onMount={handleEditorDidMount}
      />
    </div>
  )
}

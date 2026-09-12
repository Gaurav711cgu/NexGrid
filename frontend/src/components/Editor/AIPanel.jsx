import React, { useState } from 'react'
import { Sparkles, X, Send, Bot, User as UserIcon, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { useAIStream } from '../../hooks/useAIStream'

export function AIPanel({ roomId, user, onClose }) {
  const [prompt, setPrompt] = useState('')
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: 'I am the NexGrid AI (Powered by Anthropic & Qwen). I have context of your entire file, the AST, and the execution logs. How can I help?' 
    }
  ])
  
  const { askQuestion, isGenerating } = useAIStream(roomId)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!prompt.trim() || isGenerating) return

    const userMsg = { role: 'user', content: prompt }
    setMessages(prev => [...prev, userMsg])
    setPrompt('')

    try {
      const response = await askQuestion(userMsg.content)
      setMessages(prev => [...prev, { role: 'assistant', content: response.answer }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }])
    }
  }

  return (
    <div className="flex flex-col h-full bg-neutral-bg2 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border-subtle bg-neutral-bg3">
        <div className="flex items-center gap-2 font-display font-semibold text-text-primary">
          <Sparkles size={18} className="text-brand" /> AI Copilot
        </div>
        <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-md transition-colors text-text-secondary">
          <X size={18} />
        </button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg, i) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            key={i} 
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-neutral-bg5 text-white' : 'bg-brand text-white shadow-glow'}`}>
              {msg.role === 'user' ? <UserIcon size={14} /> : <Bot size={14} />}
            </div>
            
            <div className={`px-4 py-2.5 rounded-2xl max-w-[85%] text-sm leading-relaxed ${
              msg.role === 'user' 
                ? 'bg-neutral-bg4 text-text-primary rounded-tr-sm' 
                : 'glass-card border-none bg-neutral-bg3 text-text-secondary rounded-tl-sm'
            }`}>
              {msg.content}
            </div>
          </motion.div>
        ))}
        {isGenerating && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-brand flex items-center justify-center text-white shadow-glow">
              <Loader2 size={14} className="animate-spin" />
            </div>
            <div className="px-4 py-2.5 rounded-2xl bg-neutral-bg3 text-text-secondary rounded-tl-sm text-sm">
              Analyzing AST...
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-neutral-bg3 border-t border-border-subtle">
        <form onSubmit={handleSubmit} className="relative">
          <input 
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask about the code..."
            className="w-full bg-neutral-bg1 border border-border-default rounded-full pl-4 pr-12 py-2.5 text-sm text-text-primary focus:border-brand focus:ring-1 focus:ring-brand outline-none transition-all placeholder:text-text-muted"
            disabled={isGenerating}
          />
          <button 
            type="submit" 
            disabled={!prompt.trim() || isGenerating}
            className="absolute right-1.5 top-1.5 bottom-1.5 w-8 flex items-center justify-center bg-brand text-white rounded-full hover:bg-brand-hover disabled:opacity-50 transition-colors"
          >
            <Send size={14} className="ml-[-2px]" />
          </button>
        </form>
      </div>
    </div>
  )
}

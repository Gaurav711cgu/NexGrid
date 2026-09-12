import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { X, Lock, Mail, Github, Loader2 } from 'lucide-react'
import api from '../../lib/api'

export function AuthModal({ onClose, onSuccess }) {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (isLogin) {
        const formData = new URLSearchParams()
        formData.append('username', email)
        formData.append('password', password)
        const res = await api.post('/auth/login', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
        localStorage.setItem('nexagrid_token', res.data.access_token)
        const userRes = await api.get('/auth/me')
        onSuccess(userRes.data)
      } else {
        const res = await api.post('/auth/register', { email, password })
        setIsLogin(true)
        setError('Registration successful! Please sign in.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center glass-overlay p-4"
    >
      <motion.div 
        initial={{ scale: 0.95, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 20 }}
        className="glass-card w-full max-w-md bg-neutral-bg2 overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)]"
      >
        <div className="flex items-center justify-between p-6 border-b border-border-subtle">
          <h2 className="text-xl font-display font-bold text-text-primary">
            {isLogin ? 'Sign In to NexGrid' : 'Create an Account'}
          </h2>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className={`p-3 rounded-md text-sm ${error.includes('successful') ? 'bg-status-success/20 text-status-success border border-status-success/50' : 'bg-status-error/20 text-status-error border border-status-error/50'}`}>
              {error}
            </div>
          )}
          
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-text-secondary">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 text-text-muted" size={18} />
              <input 
                type="email" 
                required 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-neutral-bg1 border border-border-default rounded-md pl-10 pr-4 py-2.5 text-text-primary focus:border-brand focus:ring-1 focus:ring-brand outline-none transition-all placeholder:text-text-muted"
                placeholder="developer@example.com"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-text-secondary">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 text-text-muted" size={18} />
              <input 
                type="password" 
                required 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-neutral-bg1 border border-border-default rounded-md pl-10 pr-4 py-2.5 text-text-primary focus:border-brand focus:ring-1 focus:ring-brand outline-none transition-all placeholder:text-text-muted"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full btn-solid-white bg-brand text-white border-none py-2.5 rounded-md font-semibold hover:bg-brand-hover flex justify-center items-center"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>
        </form>

        <div className="p-6 border-t border-border-subtle bg-neutral-bg1/50 text-center text-sm text-text-secondary">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button 
            type="button" 
            onClick={() => setIsLogin(!isLogin)} 
            className="text-brand font-medium hover:underline focus:outline-none"
          >
            {isLogin ? 'Sign Up' : 'Sign In'}
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

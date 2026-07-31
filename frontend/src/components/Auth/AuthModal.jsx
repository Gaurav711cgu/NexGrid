import React, { useState, useEffect, useRef } from 'react'
import { api } from '../../lib/api'
import { LogIn, UserPlus, X } from 'lucide-react'

export function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const modalRef = useRef(null)

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      let res
      if (isRegister) {
        res = await api.register({ email, password, display_name: displayName })
      } else {
        res = await api.login({ email, password })
      }
      localStorage.setItem('nexagrid_token', res.access_token)
      onAuthSuccess(res.user)
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(9, 13, 22, 0.85)', backdropFilter: 'blur(12px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
      }}
    >
      <div ref={modalRef} className="glass-panel" style={{ width: '420px', padding: '2rem', position: 'relative' }}>
        <button
          onClick={onClose}
          aria-label="Close authentication modal"
          style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', minHeight: '44px', minWidth: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
        >
          <X size={20} aria-hidden="true" />
        </button>

        <h2 id="auth-modal-title" style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {isRegister ? <UserPlus color="#6366f1" aria-hidden="true" /> : <LogIn color="#6366f1" aria-hidden="true" />}
          {isRegister ? 'Create Account' : 'Welcome Back'}
        </h2>
        <p style={{ color: '#9ca3af', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          {isRegister ? 'Sign up for real-time code collaboration' : 'Sign in to access your NexaGrid workspace'}
        </p>

        {error && (
          <div role="alert" style={{ background: 'rgba(244,63,94,0.15)', border: '1px solid rgba(244,63,94,0.3)', color: '#f43f5e', padding: '0.75rem', borderRadius: '8px', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {isRegister && (
            <div>
              <label htmlFor="display-name" style={{ fontSize: '0.85rem', color: '#9ca3af', display: 'block', marginBottom: '0.3rem', fontWeight: 500 }}>
                Display Name <span style={{ color: '#f43f5e' }}>*</span>
              </label>
              <input
                id="display-name"
                type="text"
                className="input-field"
                placeholder="Alex Developer"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
              />
            </div>
          )}

          <div>
            <label htmlFor="email-input" style={{ fontSize: '0.85rem', color: '#9ca3af', display: 'block', marginBottom: '0.3rem', fontWeight: 500 }}>
              Email Address <span style={{ color: '#f43f5e' }}>*</span>
            </label>
            <input
              id="email-input"
              type="email"
              className="input-field"
              placeholder="alex@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="password-input" style={{ fontSize: '0.85rem', color: '#9ca3af', display: 'block', marginBottom: '0.3rem', fontWeight: 500 }}>
              Password <span style={{ color: '#f43f5e' }}>*</span>
            </label>
            <input
              id="password-input"
              type="password"
              className="input-field"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading} style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
            {loading ? 'Processing...' : (isRegister ? 'Register' : 'Sign In')}
          </button>
        </form>

        <div style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.85rem', color: '#9ca3af' }}>
          {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button
            onClick={() => setIsRegister(!isRegister)}
            style={{ background: 'none', border: 'none', color: '#818cf8', fontWeight: 600, cursor: 'pointer', padding: '4px' }}
          >
            {isRegister ? 'Sign In' : 'Create One'}
          </button>
        </div>
      </div>
    </div>
  )
}

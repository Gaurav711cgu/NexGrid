import React from 'react'
import { motion } from 'framer-motion'
import { Server, Zap, Shield, GitBranch, Cpu, Globe } from 'lucide-react'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } }
}

export function RoomHeroBanner() {
  return (
    <motion.div 
      className="flex-1 flex flex-col items-center justify-center p-8 bg-neutral-bg1 relative overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Background gradients for Glassmorphism effect */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-status-info/20 rounded-full blur-[120px] pointer-events-none" />

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="max-w-5xl w-full z-10 flex flex-col items-center text-center space-y-8"
      >
        <motion.div variants={itemVariants} className="badge-capsule">
          <div className="live-dot-green" />
          Production Environment V2.0
        </motion.div>

        <motion.h1 
          variants={itemVariants}
          className="text-5xl md:text-7xl font-display font-extrabold text-transparent bg-clip-text bg-gradient-to-br from-white via-neutral-300 to-neutral-500 tracking-tight leading-tight"
        >
          Distributed Code Execution <br />
          <span className="text-brand">At The Edge.</span>
        </motion.h1>

        <motion.p 
          variants={itemVariants}
          className="text-lg md:text-xl text-text-secondary max-w-2xl leading-relaxed"
        >
          NexGrid is a Tier-1 multi-tenant code execution platform. Powered by Y.js CRDTs, Redis Streams backplane, and hybrid POSIX/Docker sandboxes for ultra-low latency pair programming.
        </motion.p>

        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-12">
          
          <div className="glass-card p-6 flex flex-col items-start text-left space-y-4 hover:border-brand/50 transition-colors">
            <div className="p-3 bg-brand-subtle rounded-lg text-brand">
              <Globe size={24} />
            </div>
            <h3 className="text-xl font-semibold text-text-primary">Global Edge Routing</h3>
            <p className="text-sm text-text-secondary">
              WebSockets terminate at the edge via Cloudflare/Fly.io. Room affinity ensures &lt;50ms latency for co-located teams globally.
            </p>
          </div>

          <div className="glass-card p-6 flex flex-col items-start text-left space-y-4 hover:border-status-info/50 transition-colors">
            <div className="p-3 bg-status-info/20 rounded-lg text-status-info">
              <Shield size={24} />
            </div>
            <h3 className="text-xl font-semibold text-text-primary">Hardened Sandboxing</h3>
            <p className="text-sm text-text-secondary">
              Multi-layered isolation. Code executes in gVisor Docker containers with strict CPU/memory token-bucket rate limiting.
            </p>
          </div>

          <div className="glass-card p-6 flex flex-col items-start text-left space-y-4 hover:border-status-success/50 transition-colors">
            <div className="p-3 bg-status-success/20 rounded-lg text-status-success">
              <Cpu size={24} />
            </div>
            <h3 className="text-xl font-semibold text-text-primary">Semantic AI Router</h3>
            <p className="text-sm text-text-secondary">
              Vector RAG and AST chunking powers the AI assistant. Intelligent multi-provider routing (Anthropic/Local) with semantic caching.
            </p>
          </div>

        </motion.div>
      </motion.div>
    </motion.div>
  )
}

import React from 'react'
import { Activity, Server, Cpu, Database, Network, Clock } from 'lucide-react'
import { motion } from 'framer-motion'

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } }
}
const item = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0 }
}

export function MetricsPipelinesView() {
  return (
    <div className="flex-1 overflow-y-auto bg-neutral-bg1 p-8 text-text-primary">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <header className="mb-10">
          <h2 className="text-3xl font-display font-bold">System Metrics & Observability</h2>
          <p className="text-text-secondary mt-2">Live telemetry from the global production clusters.</p>
        </header>

        <motion.div variants={container} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard icon={<Activity />} title="Global Active Connections" value="14,203" trend="+12% today" color="text-brand" />
          <MetricCard icon={<Clock />} title="P99 WebSocket Latency" value="48ms" trend="Optimal" color="text-status-success" />
          <MetricCard icon={<Cpu />} title="Sandbox CPU Utilization" value="62.4%" trend="-3% from avg" color="text-status-warning" />
          <MetricCard icon={<Server />} title="Semantic Cache Hit Rate" value="89.1%" trend="Saves ~$400/hr" color="text-status-info" />
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-12">
          {/* MLOps Pipeline Status */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }} className="glass-card p-6">
            <h3 className="text-xl font-semibold mb-6 flex items-center gap-3">
              <Database className="text-brand" size={20} />
              MLOps Pipeline Status
            </h3>
            <div className="space-y-4">
              <PipelineStep name="Vector DB Re-indexing" status="success" time="2 mins ago" />
              <PipelineStep name="Groundedness Eval (Golden Set)" status="success" time="15 mins ago" />
              <PipelineStep name="Lexical Jaccard Eval" status="success" time="15 mins ago" />
              <PipelineStep name="Model Failover Latency Check" status="warning" time="1 hr ago" note="Anthropic API P99 > 800ms" />
            </div>
          </motion.div>

          {/* Infrastructure Topology */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 }} className="glass-card p-6">
            <h3 className="text-xl font-semibold mb-6 flex items-center gap-3">
              <Network className="text-status-info" size={20} />
              Active Regions (Hub & Spoke)
            </h3>
            <div className="space-y-4">
              <RegionRow name="US-East (N. Virginia)" role="Primary Hub" users="8,402" health="100%" />
              <RegionRow name="EU-West (Frankfurt)" role="Edge Spoke" users="3,101" health="100%" />
              <RegionRow name="AP-South (Mumbai)" role="Edge Spoke" users="2,700" health="99.9%" />
            </div>
          </motion.div>
        </div>

      </div>
    </div>
  )
}

function MetricCard({ icon, title, value, trend, color }) {
  return (
    <motion.div variants={item} className="glass-card p-6 hover:-translate-y-1 transition-transform">
      <div className={`p-3 rounded-xl bg-white/5 inline-flex ${color} mb-4`}>
        {icon}
      </div>
      <p className="text-sm text-text-secondary font-medium">{title}</p>
      <div className="mt-2 flex items-baseline gap-3">
        <span className="text-3xl font-display font-bold text-text-primary">{value}</span>
        <span className="text-xs font-medium text-text-muted">{trend}</span>
      </div>
    </motion.div>
  )
}

function PipelineStep({ name, status, time, note }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-neutral-bg2 border border-border-subtle">
      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${status === 'success' ? 'bg-status-success' : 'bg-status-warning'}`} />
        <div>
          <p className="text-sm font-medium text-text-primary">{name}</p>
          {note && <p className="text-xs text-status-warning mt-1">{note}</p>}
        </div>
      </div>
      <span className="text-xs text-text-muted">{time}</span>
    </div>
  )
}

function RegionRow({ name, role, users, health }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-neutral-bg2 border border-border-subtle">
      <div>
        <p className="text-sm font-medium text-text-primary">{name}</p>
        <p className="text-xs text-brand mt-1">{role}</p>
      </div>
      <div className="text-right">
        <p className="text-sm text-text-primary">{users} VUs</p>
        <p className="text-xs text-status-success mt-1">{health} Uptime</p>
      </div>
    </div>
  )
}

# ADR 003: Multi-Region Edge WebSocket Routing Strategy

## Status
Accepted

## Context
NexGrid is a collaborative real-time code editor. As our user base expands globally, users collaborating on the same `Room` may connect from vastly different geographical regions. Y.js CRDT relies on WebSocket connections (`y-websocket`) to synchronize document state. If all users connect to a single central US server, users in Asia or Europe will experience high latency (150ms-300ms) leading to visible cursor lag and degraded real-time pair-programming experience.

We need a strategy to route WebSocket traffic efficiently and handle conflict resolution at the edge.

## Decision
We will adopt a **Regional Hub-and-Spoke Topology with CRDT Backplanes**.

1. **Edge WebSocket Termination**: WebSockets will terminate at the closest geographical edge region using a globally distributed Anycast network (e.g., Cloudflare Workers or Fly.io Edge).
2. **Room Affinity / Hub Selection**: 
   - When a room is created, it is pinned to the region of the creator (the "Hub").
   - Subsequent users connecting from other regions (the "Spokes") will connect to their local edge nodes.
   - Edge nodes will route CRDT updates via a dedicated, persistent long-haul connection to the Room's Hub region, minimizing TLS handshake overhead.
3. **Redis Streams as the Backplane**:
   - The Hub region will manage the authoritative Y.js document state in memory.
   - All events are persisted to Upstash Redis Streams. For global distribution, we will utilize Upstash Global Databases to replicate the streams across regions with active-active topology if needed, though initial implementation will rely on cross-region Redis pub/sub.
4. **Optimistic Local CRDT Evaluation**: 
   - Because Y.js is a CRDT, edge nodes can immediately broadcast local cursor movements and code changes to other users connected *to the same edge node* without waiting for a round-trip to the Hub, ensuring instant feedback for co-located users.

## Consequences

### Positive
- **Low Latency**: Co-located users (e.g., two developers in India) get near-zero latency because their local edge node broadcasts changes instantly.
- **Resiliency**: If the central Hub region goes down, edge nodes can maintain local collaboration while attempting to re-elect a new Hub region.
- **Scale**: Offloads thousands of idle connections from the central server to the edge.

### Negative
- **Complexity**: Managing state across distributed edge nodes and ensuring consistent tear-down of empty rooms is significantly more complex than a monolithic WebSocket server.
- **Cost**: Persistent cross-region connections incur bandwidth costs and require specialized infrastructure (e.g., Fly.io private networking).

## Alternatives Considered
- **Single Central Region**: Simplest to implement, but unacceptable latency for global teams.
- **Full Active-Active Mesh**: Every region syncs directly with every other region. Rejected due to `O(n^2)` connection scaling and extreme architectural complexity.

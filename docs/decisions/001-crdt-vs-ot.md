# ADR-001: CRDT over Operational Transform for Document Sync

## Status: Accepted

## Context
NexaGrid needs to synchronize code edits across multiple concurrent users in real-time, handling simultaneous edits to the same regions without conflicts.

Two main algorithm paradigms exist for real-time collaborative text editing: Operational Transform (OT) and Conflict-free Replicated Data Types (CRDTs).

## Options Considered

### Operational Transform (OT)
Used by Google Docs, Apache Wave, ShareDB.
- **Mechanism**: Server acts as ordering authority — every operation goes through a central arbiter and is transformed against concurrent ops using transformation functions.
- **Pros**: Sub-millisecond latency for server-authoritative scenarios.
- **Cons**: Complex $O(N^2)$ transform functions (Jupiter algorithm edge cases), requires an always-online central server, hard to implement cleanly without concurrency edge-case bugs.

### CRDT (Conflict-free Replicated Data Type)
Used by Figma (switched from OT in 2019), Notion, Liveblocks, Automerge, Y.js.
- **Mechanism**: Mathematical convergence guarantee — regardless of operation arrival order, all replicas converge to identical state without a central sequencer.
- **Pros**: Works peer-to-peer or offline, server is a lightweight relay, no complex transformation matrix required.
- **Cons**: Tombstone accumulation (deleted characters retained as metadata until compact), higher memory footprint per operation.

## Decision
CRDT via **Y.js (YATA Algorithm)**.

Rationale:
1. **Offline & Partition Tolerance**: NexaGrid client sessions can recover automatically after dropped WebSocket connections.
2. **Simplified Backend**: Server operates as an async Pub/Sub message relay rather than a complex state-sequencing arbiter.
3. **Battle-tested Ecosystem**: Y.js powers Monaco Editor binding (`y-monaco`) natively.
4. **Deterministic Tie-Breaking**: YATA algorithm orders concurrent inserts at the same position using unique IDs `{clock, clientID}`.

## Consequences
- Snapshot checkpoints needed to compact state history every 50 ops (managed via Redis Redlock + PostgreSQL).
- Binary updates are ~1.5x larger than raw text deltas (acceptable overhead at code-editor scale).

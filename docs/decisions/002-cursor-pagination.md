# ADR-002: Cursor-Based Pagination over OFFSET/LIMIT

## Status: Accepted

## Context
The execution history endpoint (`GET /api/rooms/{id}/history`) needs to return paginated execution logs from the `execution_logs` table, which can grow to millions of rows under continuous sandbox usage.

## Analysis

### OFFSET/LIMIT (Rejected)
```sql
SELECT * FROM execution_logs
WHERE room_id = $1
ORDER BY executed_at DESC
LIMIT 10 OFFSET 2000;
```
PostgreSQL must read and discard 2,000 rows before returning 10 rows.
- Page 1: $O(10)$ read cost.
- Page 100: $O(2,010)$ scan cost — scans and discards previous rows.
- Deep page queries degrade performance rapidly under scale.

### Cursor-Based Pagination (Chosen)
```sql
SELECT * FROM execution_logs
WHERE room_id = $1
  AND (executed_at, id) < ($2::timestamptz, $3::uuid)
ORDER BY executed_at DESC, id DESC
LIMIT 10;
```
With composite index `idx_exec_logs_room_cursor ON execution_logs(room_id, executed_at DESC, id DESC)`:
- PostgreSQL seeks directly to cursor position in the B-tree.
- Execution cost is $O(\log N + \text{page\_size})$ regardless of pagination depth.
- Page 100 costs the exact same as Page 1.

## Decision
Cursor-based pagination using composite tuple `(executed_at, id)` as an opaque cursor string.

-- NexaGrid PostgreSQL Schema with Advanced Partitioning, GIN Indexing, & Triggers

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    avatar_color VARCHAR(7) DEFAULT '#6366f1',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. Rooms Table with Auto-update Timestamp Trigger
CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    language VARCHAR(20) DEFAULT 'python',
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    max_participants INT DEFAULT 10,
    is_public BOOLEAN DEFAULT FALSE,
    initial_code TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_rooms_code ON rooms(code);
CREATE INDEX IF NOT EXISTS idx_rooms_expires ON rooms(expires_at);

-- Trigger for auto-updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_rooms_updated_at ON rooms;
CREATE TRIGGER trg_rooms_updated_at
BEFORE UPDATE ON rooms
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 3. Snapshots Table (CRDT state checkpoints)
CREATE TABLE IF NOT EXISTS room_snapshots (
    id SERIAL PRIMARY KEY,
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    snapshot_data BYTEA NOT NULL,
    op_count INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_room_version ON room_snapshots(room_id, op_count DESC);

-- 4. Execution Logs Table (Partitioned Declaratively by Range on executed_at)
CREATE TABLE IF NOT EXISTS execution_logs (
    id UUID DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL,
    user_id UUID,
    language VARCHAR(20) NOT NULL,
    code_hash VARCHAR(64) NOT NULL,
    stdout TEXT,
    stderr TEXT,
    exit_code INT,
    execution_time_ms FLOAT,
    blocked BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (executed_at, id)
) PARTITION BY RANGE (executed_at);

-- Partition setup for 2026
CREATE TABLE IF NOT EXISTS execution_logs_y2026m07 PARTITION OF execution_logs
    FOR VALUES FROM ('2026-07-01 00:00:00+00') TO ('2026-08-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS execution_logs_y2026m08 PARTITION OF execution_logs
    FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS execution_logs_default PARTITION OF execution_logs DEFAULT;

-- Advanced Composite Index for Cursor-Based Pagination
CREATE INDEX IF NOT EXISTS idx_exec_logs_room_cursor ON execution_logs (room_id, executed_at DESC, id DESC);

-- GIN Index on JSONB Metadata for rapid telemetry query optimization
CREATE INDEX IF NOT EXISTS idx_exec_logs_metadata_gin ON execution_logs USING gin (metadata jsonb_path_ops);

import logging
import sqlite3
import asyncpg
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger("nexagrid.database")

class DatabaseManager:
    """
    Unified Async Database Access Layer.
    Supports PostgreSQL via asyncpg with automatic fallback to SQLite for local development.
    """
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.use_sqlite: bool = False
        self.sqlite_db_path: str = "nexagrid_dev.db"

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                timeout=10.0,
                command_timeout=30.0,
            )
            logger.info("Connected to PostgreSQL database pool.")
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed ({e}). Falling back to SQLite local database.")
            self.use_sqlite = True
            self._init_sqlite()

    def _init_sqlite(self):
        conn = sqlite3.connect(self.sqlite_db_path)
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            avatar_color TEXT DEFAULT '#6366f1',
            created_at TEXT DEFAULT (datetime('now')),
            last_seen TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            language TEXT DEFAULT 'python',
            owner_id TEXT REFERENCES users(id),
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            max_participants INTEGER DEFAULT 10,
            is_public INTEGER DEFAULT 0,
            initial_code TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS room_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT REFERENCES rooms(id),
            snapshot_data BLOB NOT NULL,
            op_count INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS execution_logs (
            id TEXT PRIMARY KEY,
            room_id TEXT NOT NULL,
            user_id TEXT,
            language TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            stdout TEXT,
            stderr TEXT,
            exit_code INTEGER,
            execution_time_ms REAL,
            blocked INTEGER DEFAULT 0,
            metadata TEXT DEFAULT '{}',
            executed_at TEXT DEFAULT (datetime('now'))
        );
        """)
        conn.commit()
        conn.close()

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def execute(self, query: str, *args) -> str:
        if self.use_sqlite:
            # Replace PostgreSQL placeholders $1, $2 with SQLite ?
            sql_query = query
            for i in range(len(args), 0, -1):
                sql_query = sql_query.replace(f"${i}", "?")
            conn = sqlite3.connect(self.sqlite_db_path)
            cur = conn.cursor()
            cur.execute(sql_query, args)
            conn.commit()
            conn.close()
            return "OK"
        else:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        if self.use_sqlite:
            sql_query = query
            for i in range(len(args), 0, -1):
                sql_query = sql_query.replace(f"${i}", "?")
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sql_query, args)
            row = cur.fetchone()
            conn.close()
            return dict(row) if row else None
        else:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        if self.use_sqlite:
            sql_query = query
            for i in range(len(args), 0, -1):
                sql_query = sql_query.replace(f"${i}", "?")
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sql_query, args)
            rows = cur.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        else:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(r) for r in rows]

db = DatabaseManager()

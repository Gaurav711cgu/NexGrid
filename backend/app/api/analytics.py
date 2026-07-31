from fastapi import APIRouter, Depends
from app.auth.security import get_current_user
from app.core.database import db

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/room/{room_id}/summary")
async def get_room_analytics(room_id: str, user: dict = Depends(get_current_user)):
    """
    Advanced FAANG SQL Query Demonstration:
    Uses Window Functions (AVG, ROW_NUMBER) and CTEs to aggregate telemetry per language.
    """
    query = """
    WITH RankedExecutions AS (
        SELECT 
            language,
            execution_time_ms,
            exit_code,
            blocked,
            AVG(execution_time_ms) OVER (PARTITION BY language) AS avg_lang_latency_ms,
            ROW_NUMBER() OVER (PARTITION BY language ORDER BY executed_at DESC) AS rank_recent
        FROM execution_logs
        WHERE room_id = $1
    )
    SELECT 
        language,
        COUNT(*) AS total_executions,
        SUM(CASE WHEN exit_code = 0 THEN 1 ELSE 0 END) AS successful_runs,
        SUM(CASE WHEN blocked = 1 THEN 1 ELSE 0 END) AS blocked_runs,
        ROUND(AVG(execution_time_ms)::numeric, 2) AS avg_latency_ms,
        ROUND(MAX(avg_lang_latency_ms)::numeric, 2) AS overall_lang_avg_ms
    FROM RankedExecutions
    GROUP BY language;
    """
    rows = await db.fetch(query, room_id)
    return {"room_id": room_id, "analytics": rows}

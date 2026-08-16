"""
Asynchronous SQLite checkpoint store for persisting and resuming CircleRunState.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import aiosqlite
import structlog

from aztec_circle.config import settings
from aztec_circle.domain.models import CircleRunState

log = structlog.get_logger(__name__)


class CheckpointStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.CHECKPOINT_DB_PATH

    async def _init_db(self, db: aiosqlite.Connection) -> None:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                task_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        await db.commit()

    async def save(self, state: CircleRunState) -> None:
        """Persist state to SQLite."""
        state.updated_at = datetime.now(timezone.utc)
        payload = state.model_dump_json()
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            await db.execute(
                """
                INSERT OR REPLACE INTO runs (task_id, state_json, updated_at)
                VALUES (?, ?, ?)
                """,
                (state.task_id, payload, state.updated_at.isoformat()),
            )
            await db.commit()
            log.debug("checkpoint.saved", task_id=state.task_id, phase=state.current_phase.value)

    async def load(self, task_id: str) -> Optional[CircleRunState]:
        """Load state from SQLite by task_id."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            async with db.execute(
                "SELECT state_json FROM runs WHERE task_id = ?",
                (task_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return CircleRunState.model_validate_json(row[0])
        return None

    async def list_runs(self) -> List[Dict[str, Any]]:
        """List all saved run summaries."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            async with db.execute(
                "SELECT task_id, updated_at, state_json FROM runs ORDER BY updated_at DESC"
            ) as cursor:
                runs = []
                async for row in cursor:
                    try:
                        state_dict = CircleRunState.model_validate_json(row[2])
                        runs.append({
                            "task_id": row[0],
                            "updated_at": row[1],
                            "goal": state_dict.goal,
                            "phase": state_dict.current_phase.value,
                            "loops": state_dict.loop_count,
                            "cost_usd": state_dict.total_cost_usd,
                        })
                    except Exception:
                        runs.append({
                            "task_id": row[0],
                            "updated_at": row[1],
                            "goal": "Unknown",
                            "phase": "Unknown",
                        })
                return runs

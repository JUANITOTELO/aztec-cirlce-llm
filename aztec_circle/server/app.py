"""
FastAPI server and WebSocket broadcaster for Aztec Decision Circle Web Inspector.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import structlog

from aztec_circle.domain.models import CircleRunState, FallbackPolicy
from aztec_circle.engine.checkpoint import CheckpointStore
from aztec_circle.engine.state_machine import AztecOrchestrator

log = structlog.get_logger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


class TaskRunRequest(BaseModel):
    goal: str
    budget_limit_usd: float = 1.00
    max_loops: int = 2
    fallback_policy: FallbackPolicy = FallbackPolicy.HUMAN_IN_THE_LOOP


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.discard(d)


manager = ConnectionManager()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Aztec Decision Circle Inspector",
        version="0.1.0",
        description="Real-time multi-generational LLM debate inspector",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    store = CheckpointStore()

    @app.get("/", response_class=HTMLResponse)
    async def get_index():
        html_file = STATIC_DIR / "index.html"
        if not html_file.exists():
            return "<h1>Aztec Web Inspector</h1><p>Static index.html not found.</p>"
        return html_file.read_text(encoding="utf-8")

    @app.websocket("/ws/events")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                # Keepalive / receive client pings
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception:
            manager.disconnect(websocket)

    @app.post("/api/tasks/run")
    async def run_task(req: TaskRunRequest):
        state = CircleRunState(
            goal=req.goal,
            budget_limit_usd=req.budget_limit_usd,
            max_loops=req.max_loops,
            fallback_policy=req.fallback_policy,
        )
        event_queue: asyncio.Queue = asyncio.Queue()

        async def _forward_events():
            try:
                while True:
                    event = await event_queue.get()
                    await manager.broadcast(event)
                    event_queue.task_done()
            except asyncio.CancelledError:
                pass

        forwarder = asyncio.create_task(_forward_events())
        orchestrator = AztecOrchestrator(
            state=state,
            event_queue=event_queue,
            checkpoint_store=store,
        )

        try:
            result = await orchestrator.run()
            return result
        except Exception as exc:
            log.error("api.run_task_failed", error=str(exc))
            return {"task_id": state.task_id, "error": str(exc), "phase": state.current_phase.value}
        finally:
            forwarder.cancel()

    @app.get("/api/tasks/runs")
    async def list_runs():
        return await store.list_runs()

    @app.get("/api/tasks/runs/{task_id}")
    async def get_run(task_id: str):
        state = await store.load(task_id)
        if not state:
            raise HTTPException(status_code=404, detail="Run not found")
        return state.model_dump()

    @app.post("/api/tasks/resume/{task_id}")
    async def resume_task(task_id: str):
        state = await store.load(task_id)
        if not state:
            raise HTTPException(status_code=404, detail="Run not found")

        event_queue: asyncio.Queue = asyncio.Queue()

        async def _forward_events():
            try:
                while True:
                    event = await event_queue.get()
                    await manager.broadcast(event)
                    event_queue.task_done()
            except asyncio.CancelledError:
                pass

        forwarder = asyncio.create_task(_forward_events())
        orchestrator = AztecOrchestrator(
            state=state,
            event_queue=event_queue,
            checkpoint_store=store,
        )

        try:
            result = await orchestrator.run()
            return result
        finally:
            forwarder.cancel()

    return app

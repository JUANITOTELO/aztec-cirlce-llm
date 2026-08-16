"""
Tests for FastAPI Web Inspector server endpoints and WebSocket communication.
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient
from aztec_circle.domain.models import CirclePhase, CircleRunState
from aztec_circle.engine.checkpoint import CheckpointStore
from aztec_circle.server.app import create_app, manager


@pytest.mark.asyncio
async def test_server_index():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "Aztec Decision Circle" in resp.text


@pytest.mark.asyncio
async def test_server_list_runs():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/tasks/runs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_server_get_run(temp_db_path):
    store = CheckpointStore(db_path=temp_db_path)
    state = CircleRunState(goal="API Test Goal", current_phase=CirclePhase.RESOLVED)
    await store.save(state)

    with patch("aztec_circle.config.settings.CHECKPOINT_DB_PATH", temp_db_path):
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/tasks/runs/{state.task_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["task_id"] == state.task_id
            assert data["goal"] == "API Test Goal"


@pytest.mark.asyncio
async def test_server_get_non_existent_run():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/tasks/runs/fake-id-999")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_server_run_task_endpoint(temp_db_path):
    mock_run_result = {"status": "APPROVED", "task_id": "test-123"}
    with patch("aztec_circle.config.settings.CHECKPOINT_DB_PATH", temp_db_path), \
         patch("aztec_circle.engine.state_machine.AztecOrchestrator.run", new_callable=AsyncMock) as mock_orch:
        mock_orch.return_value = mock_run_result
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/tasks/run",
                json={"goal": "Build rate limiter", "budget_limit_usd": 1.0, "max_loops": 2},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_server_run_task_endpoint_error_handling(temp_db_path):
    with patch("aztec_circle.config.settings.CHECKPOINT_DB_PATH", temp_db_path), \
         patch("aztec_circle.engine.state_machine.AztecOrchestrator.run", side_effect=Exception("Execution Failed")):
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/tasks/run",
                json={"goal": "Error Goal", "budget_limit_usd": 1.0, "max_loops": 2},
            )
            assert resp.status_code == 200
            assert "Execution Failed" in resp.json()["error"]


@pytest.mark.asyncio
async def test_server_resume_task_endpoint(temp_db_path):
    store = CheckpointStore(db_path=temp_db_path)
    state = CircleRunState(goal="Resume via API", current_phase=CirclePhase.RESOLVED)
    await store.save(state)

    mock_run_result = {"status": "APPROVED", "task_id": state.task_id}
    with patch("aztec_circle.config.settings.CHECKPOINT_DB_PATH", temp_db_path), \
         patch("aztec_circle.engine.state_machine.AztecOrchestrator.run", new_callable=AsyncMock) as mock_orch:
        mock_orch.return_value = mock_run_result
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Valid resume
            resp = await client.post(f"/api/tasks/resume/{state.task_id}")
            assert resp.status_code == 200

            # Non-existent resume
            resp_404 = await client.post("/api/tasks/resume/non-existent-123")
            assert resp_404.status_code == 404


def test_server_websocket_endpoint():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/events") as websocket:
        websocket.send_text("ping")
        # Connection established successfully
        assert websocket is not None

"""
Tests for SQLite checkpoint persistence store.
"""

import pytest
from aztec_circle.domain.models import CirclePhase, CircleRunState
from aztec_circle.engine.checkpoint import CheckpointStore


@pytest.mark.asyncio
async def test_checkpoint_save_and_load(temp_db_path):
    store = CheckpointStore(db_path=temp_db_path)
    state = CircleRunState(
        goal="Design a multi-region replicated key-value database",
        current_phase=CirclePhase.PEER_DRAFTING,
        loop_count=1,
        total_cost_usd=0.045,
    )

    await store.save(state)

    loaded = await store.load(state.task_id)
    assert loaded is not None
    assert loaded.task_id == state.task_id
    assert loaded.goal == state.goal
    assert loaded.current_phase == CirclePhase.PEER_DRAFTING
    assert loaded.loop_count == 1
    assert loaded.total_cost_usd == 0.045


@pytest.mark.asyncio
async def test_checkpoint_list_runs(temp_db_path):
    store = CheckpointStore(db_path=temp_db_path)
    s1 = CircleRunState(goal="Task 1", current_phase=CirclePhase.RESOLVED)
    s2 = CircleRunState(goal="Task 2", current_phase=CirclePhase.EMERGENCY_HALTED)

    await store.save(s1)
    await store.save(s2)

    runs = await store.list_runs()
    assert len(runs) == 2
    task_ids = [r["task_id"] for r in runs]
    assert s1.task_id in task_ids
    assert s2.task_id in task_ids

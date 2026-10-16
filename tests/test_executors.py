"""
Tests for LocalExecutor and SSHExecutor
"""

import pytest
from app.remote.local_executor import LocalExecutor

@pytest.mark.asyncio
async def test_local_executor_run():
    executor = LocalExecutor()
    assert await executor.is_connected() is True

    code, stdout, stderr = await executor.run("echo 'hello melodi'")
    assert code == 0
    assert "hello melodi" in stdout

    conn_res = await executor.test_connection()
    assert conn_res["success"] is True
    assert conn_res["latency_ms"] >= 0

@pytest.mark.asyncio
async def test_local_executor_explicit_timeout():
    executor = LocalExecutor()
    code, stdout, stderr = await executor.run("sleep 2", timeout=0.2)
    assert code == -1
    assert "Timeout" in stderr

@pytest.mark.asyncio
async def test_local_executor_no_timeout_by_default():
    executor = LocalExecutor()
    # Runs fine without specifying timeout
    code, stdout, stderr = await executor.run("echo 'no timeout'")
    assert code == 0
    assert "no timeout" in stdout

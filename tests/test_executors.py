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

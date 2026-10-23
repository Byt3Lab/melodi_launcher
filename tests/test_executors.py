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

@pytest.mark.asyncio
async def test_local_executor_upload_file(tmp_path):
    executor = LocalExecutor()
    src = tmp_path / "source.txt"
    src.write_text("melodi payload content", encoding="utf-8")
    dest = tmp_path / "subdir" / "destination.txt"

    success, err = await executor.upload_file(str(src), str(dest))
    assert success is True
    assert err == ""
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "melodi payload content"

@pytest.mark.asyncio
async def test_local_executor_upload_nonexistent_file(tmp_path):
    executor = LocalExecutor()
    src = tmp_path / "does_not_exist.txt"
    dest = tmp_path / "out.txt"

    success, err = await executor.upload_file(str(src), str(dest))
    assert success is False
    assert "n'existe pas" in err

@pytest.mark.asyncio
async def test_local_executor_download_file(tmp_path):
    executor = LocalExecutor()
    src = tmp_path / "origin.txt"
    src.write_text("downloaded via url test", encoding="utf-8")
    dest = tmp_path / "target_downloaded.txt"

    file_url = f"file://{src.absolute()}"
    success, err = await executor.download_file(file_url, str(dest))
    assert success is True
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "downloaded via url test"



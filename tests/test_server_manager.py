"""
Tests for ServerManager
"""

import os
import pytest
from app.core.server_manager import ServerManager

def test_server_manager_crud_and_auth(tmp_path):
    servers_file = os.path.join(tmp_path, "servers.json")
    sm = ServerManager(servers_file)

    servers = sm.get_all_servers()
    assert len(servers) >= 1
    assert servers[0]["id"] == "local"

    # Add remote server with key auth
    add_key_res = sm.add_server({
        "name": "Prod Server Key",
        "host": "192.168.1.100",
        "port": 22,
        "username": "ubuntu",
        "auth_method": "key",
        "key_path": "~/.ssh/id_ed25519"
    })
    assert add_key_res["success"] is True
    srv_key_id = add_key_res["server"]["id"]

    # Add remote server with password auth
    add_pwd_res = sm.add_server({
        "name": "Prod Server Pwd",
        "host": "192.168.1.101",
        "port": 22,
        "username": "admin",
        "auth_method": "password",
        "password": "secretpassword"
    })
    assert add_pwd_res["success"] is True
    srv_pwd_id = add_pwd_res["server"]["id"]

    # Check executor instantiation for password auth
    executor_pwd = sm.get_executor(srv_pwd_id)
    assert executor_pwd.password == "secretpassword"
    assert executor_pwd.key_path is None

    # Delete server
    del_res = sm.delete_server(srv_pwd_id)
    assert del_res["success"] is True
    assert sm.get_server(srv_pwd_id) is None

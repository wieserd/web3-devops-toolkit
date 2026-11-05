import pytest
from unittest.mock import patch, MagicMock
import subprocess

from src.actions.proxy import manage_proxy
from src.actions.common import get_contracts_dir

@patch('subprocess.run')
def test_manage_proxy_deploy_success(mock_run):
    mock_run.return_value = MagicMock(
        stdout="[📦] Implementation deployed to 0x1111111111111111111111111111111111111111\nProxy deployed to 0x2222222222222222222222222222222222222222",
        stderr="",
        returncode=0
    )
    params = {
        'network': 'localhost',
        'contract': 'TokenV1',
        'operation': 'deploy',
        'init_args': ['TokenName', 'TKN']
    }
    deployed_contracts = {}
    result = manage_proxy(params, deployed_contracts=deployed_contracts)
    assert result['status'] == 'success'
    assert result['operation'] == 'deploy'
    assert result['proxy_address'] == '0x2222222222222222222222222222222222222222'
    assert result['implementation_address'] == '0x1111111111111111111111111111111111111111'
    assert deployed_contracts['TokenV1'] == '0x2222222222222222222222222222222222222222'

@patch('subprocess.run')
def test_manage_proxy_upgrade_success(mock_run):
    mock_run.return_value = MagicMock(
        stdout="[📦] Implementation deployed to 0x3333333333333333333333333333333333333333\nProxy upgraded to 0x3333333333333333333333333333333333333333",
        stderr="",
        returncode=0
    )
    params = {
        'network': 'localhost',
        'contract': 'TokenV1',
        'operation': 'upgrade',
        'proxy_address': '0x2222222222222222222222222222222222222222'
    }
    result = manage_proxy(params)
    assert result['status'] == 'success'
    assert result['operation'] == 'upgrade'

def test_manage_proxy_missing_contract():
    result = manage_proxy({})
    assert result['status'] == 'failure'
    assert "Missing 'contract' parameter" in result['error']

def test_manage_proxy_upgrade_missing_proxy_address():
    params = {
        'contract': 'TokenV2',
        'operation': 'upgrade'
    }
    result = manage_proxy(params, deployed_contracts={})
    assert result['status'] == 'failure'
    assert "Missing 'proxy_address' for upgrade" in result['error']

import pytest
import os
import json
import subprocess
from unittest.mock import patch, MagicMock

from src.actions.smoke_test import smoke_test
from src.actions.common import get_contracts_dir, clean_env

@patch('subprocess.run')
def test_smoke_test_success(mock_run):
    mock_run.return_value = MagicMock(stdout="All on-chain smoke tests passed", stderr="", returncode=0)
    params = {
        'network': 'localhost',
        'contract': 'MyContract',
        'address': '0x1234567890123456789012345678901234567890',
        'calls': [{'method': 'greet', 'expected': 'Hello'}]
    }
    result = smoke_test(params)

    expected_env = clean_env(os.environ.copy())
    expected_env["CONTRACT_NAME"] = "MyContract"
    expected_env["CONTRACT_ADDRESS"] = "0x1234567890123456789012345678901234567890"
    expected_env["SMOKE_CALLS"] = json.dumps([{'method': 'greet', 'expected': 'Hello'}])

    mock_run.assert_called_once_with(
        ["npx", "hardhat", "run", "scripts/smoke_test.js", "--network", "localhost"],
        cwd=get_contracts_dir(),
        capture_output=True,
        text=True,
        check=True,
        env=expected_env
    )
    assert result['status'] == 'success'
    assert result['address'] == '0x1234567890123456789012345678901234567890'

@patch('subprocess.run')
def test_smoke_test_address_fallback_from_registry(mock_run):
    mock_run.return_value = MagicMock(stdout="All passed", stderr="", returncode=0)
    params = {
        'network': 'localhost',
        'contract': 'MyContract'
    }
    deployed_contracts = {'MyContract': '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd'}
    result = smoke_test(params, deployed_contracts=deployed_contracts)
    assert result['status'] == 'success'
    assert result['address'] == '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd'

def test_smoke_test_missing_network():
    result = smoke_test({'contract': 'MyContract'})
    assert result['status'] == 'failure'
    assert "Missing 'network' parameter" in result['error']

def test_smoke_test_missing_contract():
    result = smoke_test({'network': 'localhost'})
    assert result['status'] == 'failure'
    assert "Missing 'contract' parameter" in result['error']

def test_smoke_test_missing_address():
    result = smoke_test({'network': 'localhost', 'contract': 'MyContract'}, deployed_contracts={})
    assert result['status'] == 'failure'
    assert 'No address to smoke test' in result['error']

@patch('subprocess.run')
def test_smoke_test_failure_exit(mock_run):
    err = subprocess.CalledProcessError(returncode=1, cmd="npx hardhat run")
    err.stdout = "Assertion failed on MyContract.greet()"
    err.stderr = ""
    mock_run.side_effect = err

    params = {
        'network': 'localhost',
        'contract': 'MyContract',
        'address': '0x1234567890123456789012345678901234567890'
    }
    result = smoke_test(params)
    assert result['status'] == 'failure'
    assert 'Assertion failed on MyContract.greet()' in result['error']

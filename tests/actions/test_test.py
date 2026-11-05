import pytest
from unittest.mock import patch, MagicMock
import subprocess

from src.actions.test import test_contracts as execute_contract_tests
from src.actions.common import get_contracts_dir

@patch('subprocess.run')
def test_test_contracts_hardhat_success(mock_run):
    mock_run.return_value = MagicMock(stdout="5 passing", stderr="", returncode=0)
    params = {'tool': 'hardhat', 'network': 'localhost'}
    result = execute_contract_tests(params)
    mock_run.assert_called_once()
    assert result == {'status': 'success'}

@patch('subprocess.run')
def test_test_contracts_hardhat_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="npx hardhat test", stderr="1 failing")
    params = {'tool': 'hardhat'}
    result = execute_contract_tests(params)
    assert result == {'status': 'failure', 'error': '1 failing'}

@patch('subprocess.run')
def test_test_contracts_foundry_success(mock_run):
    mock_run.return_value = MagicMock(stdout="Test result: ok.", stderr="", returncode=0)
    params = {'tool': 'foundry', 'test_files': ['test/MyContract.t.sol']}
    result = execute_contract_tests(params)
    mock_run.assert_called_once()
    assert result == {'status': 'success'}

@patch('subprocess.run')
def test_test_contracts_foundry_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="forge test", stderr="Test failed")
    params = {'tool': 'foundry'}
    result = execute_contract_tests(params)
    assert result == {'status': 'failure', 'error': 'Test failed'}

def test_test_contracts_unsupported_tool():
    params = {'tool': 'unknown_tool'}
    result = execute_contract_tests(params)
    assert result['status'] == 'failure'
    assert 'Unsupported testing tool' in result['error']

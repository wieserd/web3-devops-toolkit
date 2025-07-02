import pytest
from unittest.mock import patch, MagicMock
import subprocess

from src.actions.compile import compile_contracts

@patch('subprocess.run')
def test_compile_contracts_success(mock_run):
    mock_run.return_value = MagicMock(stdout="Compilation successful", stderr="", returncode=0)
    params = {'tool': 'hardhat'}
    result = compile_contracts(params)
    mock_run.assert_called_once_with(
        ["npx", "hardhat", "compile"],
        cwd="/Users/dw2022/web3-devops-toolkit/contracts",
        capture_output=True,
        text=True,
        check=True
    )
    assert result == {'status': 'success'}

@patch('subprocess.run')
def test_compile_contracts_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="npx hardhat compile", stderr="Compilation failed")
    params = {'tool': 'hardhat'}
    result = compile_contracts(params)
    assert result == {'status': 'failure', 'error': 'Compilation failed'}

@patch('subprocess.run', side_effect=FileNotFoundError)
def test_compile_contracts_npx_not_found(mock_run):
    params = {'tool': 'hardhat'}
    result = compile_contracts(params)
    assert result == {'status': 'failure', 'error': 'npx/hardhat not found'}

def test_compile_contracts_unsupported_tool():
    params = {'tool': 'foundry'}
    result = compile_contracts(params)
    assert result == {'status': 'failure', 'error': f'Unsupported tool: foundry'}
import pytest
from unittest.mock import patch, MagicMock
import subprocess

from src.actions.compile import compile_contracts
from src.actions.common import get_contracts_dir

@patch('subprocess.run')
def test_compile_contracts_hardhat_success(mock_run):
    mock_run.return_value = MagicMock(stdout="Compilation successful", stderr="", returncode=0)
    params = {'tool': 'hardhat'}
    result = compile_contracts(params)
    mock_run.assert_called_once_with(
        ["npx", "hardhat", "compile"],
        cwd=get_contracts_dir(),
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

@patch('subprocess.run')
def test_compile_contracts_foundry_success(mock_run):
    mock_run.return_value = MagicMock(stdout="Compiler run successful", stderr="", returncode=0)
    params = {'tool': 'foundry'}
    result = compile_contracts(params)
    mock_run.assert_called_once_with(
        ["forge", "build"],
        cwd=get_contracts_dir(),
        capture_output=True,
        text=True,
        check=True
    )
    assert result == {'status': 'success'}

@patch('subprocess.run')
def test_compile_contracts_foundry_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="forge build", stderr="Build failed")
    params = {'tool': 'foundry'}
    result = compile_contracts(params)
    assert result == {'status': 'failure', 'error': 'Build failed'}

def test_compile_contracts_unsupported_tool():
    params = {'tool': 'truffle'}
    result = compile_contracts(params)
    assert result == {'status': 'failure', 'error': 'Unsupported tool: truffle'}

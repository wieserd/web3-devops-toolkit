import pytest
from unittest.mock import patch, MagicMock
import subprocess

from src.actions.gas_check import gas_check
from src.actions.common import get_contracts_dir

@patch('subprocess.run')
def test_gas_check_within_budget(mock_run):
    mock_run.return_value = MagicMock(
        stdout="[⛽] Estimated Gas Units: 1500000\n[⛽] Gas Price (Wei): 20000000000\n[⛽] Estimated Cost (Wei): 30000000000000000",
        stderr="",
        returncode=0
    )
    params = {
        'network': 'localhost',
        'contract': 'MyContract',
        'max_gas_limit': 2000000
    }
    result = gas_check(params)
    assert result['status'] == 'success'
    assert result['estimated_gas'] == 1500000

@patch('subprocess.run')
def test_gas_check_exceeds_budget(mock_run):
    mock_run.return_value = MagicMock(
        stdout="[⛽] Estimated Gas Units: 2500000\n[⛽] Gas Price (Wei): 20000000000",
        stderr="",
        returncode=0
    )
    params = {
        'network': 'localhost',
        'contract': 'MyContract',
        'max_gas_limit': 2000000,
        'fail_on_exceed': True
    }
    result = gas_check(params)
    assert result['status'] == 'failure'
    assert 'Gas budget exceeded' in result['error']
    assert result['estimated_gas'] == 2500000

def test_gas_check_missing_contract():
    result = gas_check({})
    assert result['status'] == 'failure'
    assert "Missing 'contract' parameter" in result['error']

@patch('subprocess.run')
def test_gas_check_unparseable_output(mock_run):
    mock_run.return_value = MagicMock(stdout="Some other output without gas", stderr="", returncode=0)
    params = {'contract': 'MyContract'}
    result = gas_check(params)
    assert result['status'] == 'failure'
    assert 'Gas estimation output not parseable' in result['error']

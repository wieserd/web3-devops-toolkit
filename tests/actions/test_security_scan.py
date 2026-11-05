import pytest
from unittest.mock import patch, MagicMock
import subprocess

from src.actions.security_scan import security_scan

@patch('subprocess.run')
def test_security_scan_solhint_success(mock_run):
    mock_run.return_value = MagicMock(stdout="No warnings or errors", stderr="", returncode=0)
    params = {'tool': 'solhint'}
    result = security_scan(params)
    mock_run.assert_called_once()
    assert result == {'status': 'success'}

@patch('subprocess.run')
def test_security_scan_solhint_failure(mock_run):
    err = subprocess.CalledProcessError(returncode=1, cmd="solhint")
    err.stdout = "Error on line 5"
    err.stderr = ""
    mock_run.side_effect = err
    params = {'tool': 'solhint'}
    result = security_scan(params)
    assert result['status'] == 'failure'
    assert 'Error on line 5' in result['error']

@patch('subprocess.run')
def test_security_scan_slither_success(mock_run):
    mock_run.return_value = MagicMock(stdout="0 detectors triggered", stderr="", returncode=0)
    params = {'tool': 'slither'}
    result = security_scan(params)
    mock_run.assert_called_once()
    assert result == {'status': 'success'}

@patch('subprocess.run')
def test_security_scan_slither_failure(mock_run):
    err = subprocess.CalledProcessError(returncode=1, cmd="slither .")
    err.stdout = "Vulnerability detected"
    err.stderr = ""
    mock_run.side_effect = err
    params = {'tool': 'slither'}
    result = security_scan(params)
    assert result['status'] == 'failure'

def test_security_scan_unsupported_tool():
    params = {'tool': 'mythril'}
    result = security_scan(params)
    assert result['status'] == 'failure'
    assert 'Unsupported security tool' in result['error']

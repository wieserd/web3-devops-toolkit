import pytest
import os
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open

from src.actions.deploy import deploy_contract, _clean_env

# Mock networks.json content
MOCK_NETWORKS_CONTENT = {
  "localhost": {
    "rpc_url": "http://127.0.0.1:8545",
    "chain_id": 31337
  }
}

@patch('subprocess.run')
def test_deploy_contract_success(mock_run):
    mock_run.return_value = MagicMock(stdout="MyContract deployed to 0x1234567890123456789012345678901234567890", stderr="", returncode=0)
    params = {'network': 'localhost', 'contract': 'MyContract', 'args': ["Hello"]}
    deployed_contracts = {}
    result = deploy_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=MOCK_NETWORKS_CONTENT)

    expected_env = _clean_env(os.environ.copy())
    expected_env["INITIAL_GREETING"] = "Hello"

    mock_run.assert_called_once_with(
        ["npx", "hardhat", "run", "scripts/deploy.js", "--network", "localhost"],
        cwd="/Users/dw2022/web3-devops-toolkit/contracts",
        capture_output=True,
        text=True,
        check=True,
        env=expected_env
    )
    assert result == {'status': 'success', 'address': '0x1234567890123456789012345678901234567890'}
    assert deployed_contracts['MyContract'] == '0x1234567890123456789012345678901234567890'

@patch('subprocess.run')
def test_deploy_contract_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="npx hardhat run", stderr="Deployment failed")
    params = {'network': 'localhost', 'contract': 'MyContract'}
    deployed_contracts = {}
    result = deploy_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=MOCK_NETWORKS_CONTENT)
    assert result == {'status': 'failure', 'error': 'Deployment failed'}

def test_deploy_contract_networks_file_not_found():
    params = {'network': 'localhost', 'contract': 'MyContract'}
    deployed_contracts = {}
    result = deploy_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=None) # Simulate file not found
    assert result == {'status': 'failure', 'error': 'Network config not found'}

def test_deploy_contract_network_not_found():
    params = {'network': 'nonexistent', 'contract': 'MyContract'}
    deployed_contracts = {}
    result = deploy_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=MOCK_NETWORKS_CONTENT)
    assert result == {'status': 'failure', 'error': 'Network nonexistent not found'}

def test_deploy_contract_rpc_url_not_configured():
    params = {'network': 'localhost', 'contract': 'MyContract'}
    deployed_contracts = {}
    networks_config_missing_rpc = {"localhost": {}}
    result = deploy_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=networks_config_missing_rpc)
    assert result == {'status': 'failure', 'error': 'RPC URL not configured'}
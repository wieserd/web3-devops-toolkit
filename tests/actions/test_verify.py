import pytest
import os
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open

from src.actions.verify import verify_contract, _clean_env

# Mock networks.json content
MOCK_NETWORKS_CONTENT = {
  "localhost": {
    "rpc_url": "http://127.0.0.1:8545",
    "chain_id": 31337,
    "etherscan_api_key": "mock_etherscan_key"
  }
}

@patch('subprocess.run')
def test_verify_contract_success_with_address_param(mock_run):
    mock_run.return_value = MagicMock(stdout="Verification successful", stderr="", returncode=0)
    params = {'network': 'localhost', 'contract': 'MyContract', 'address': '0xabcdef'}
    deployed_contracts = {}
    result = verify_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=MOCK_NETWORKS_CONTENT)

    expected_env = _clean_env(os.environ.copy())
    expected_env["ETHERSCAN_API_KEY"] = "mock_etherscan_key"

    mock_run.assert_called_once_with(
        ["npx", "hardhat", "verify", "--network", "localhost", "0xabcdef"],
        cwd="/Users/dw2022/web3-devops-toolkit/contracts",
        capture_output=True,
        text=True,
        check=True,
        env=expected_env
    )
    assert result == {'status': 'success'}

@patch('subprocess.run')
def test_verify_contract_success_with_deployed_contracts(mock_run):
    mock_run.return_value = MagicMock(stdout="Verification successful", stderr="", returncode=0)
    params = {'network': 'localhost', 'contract': 'MyContract'}
    deployed_contracts = {'MyContract': '0xabcdef'}
    result = verify_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=MOCK_NETWORKS_CONTENT)

    expected_env = _clean_env(os.environ.copy())
    expected_env["ETHERSCAN_API_KEY"] = "mock_etherscan_key"

    mock_run.assert_called_once_with(
        ["npx", "hardhat", "verify", "--network", "localhost", "0xabcdef"],
        cwd="/Users/dw2022/web3-devops-toolkit/contracts",
        capture_output=True,
        text=True,
        check=True,
        env=expected_env
    )
    assert result == {'status': 'success'}

@patch('subprocess.run')
def test_verify_contract_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="npx hardhat verify", stderr="Verification failed")
    params = {'network': 'localhost', 'contract': 'MyContract', 'address': '0xabcdef'}
    deployed_contracts = {}
    result = verify_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=MOCK_NETWORKS_CONTENT)
    assert result == {'status': 'failure', 'error': 'Verification failed'}

def test_verify_contract_networks_file_not_found():
    params = {'network': 'localhost', 'contract': 'MyContract', 'address': '0xabcdef'}
    deployed_contracts = {}
    result = verify_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=None) # Simulate file not found
    assert result == {'status': 'failure', 'error': 'Network config not found'}

def test_verify_contract_network_not_found():
    params = {'network': 'nonexistent', 'contract': 'MyContract', 'address': '0xabcdef'}
    deployed_contracts = {}
    result = verify_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=MOCK_NETWORKS_CONTENT)
    assert result == {'status': 'failure', 'error': 'Network nonexistent not found'}

def test_verify_contract_etherscan_api_key_not_configured():
    params = {'network': 'localhost', 'contract': 'MyContract', 'address': '0xabcdef'}
    deployed_contracts = {}
    networks_config_missing_key = {"localhost": {"rpc_url": "http://127.0.0.1:8545"}}
    result = verify_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=networks_config_missing_key)
    assert result == {'status': 'failure', 'error': 'Etherscan API key missing'}

def test_verify_contract_no_address_provided():
    params = {'network': 'localhost', 'contract': 'MyContract'}
    deployed_contracts = {}
    result = verify_contract(params, "/mock/pipeline/path/pipeline.yaml", deployed_contracts, networks_config=MOCK_NETWORKS_CONTENT)
    assert result == {'status': 'failure', 'error': 'No address to verify'}

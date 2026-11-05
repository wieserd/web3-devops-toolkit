import pytest
import os
import json
from src.actions.export_abi import export_abi

MOCK_ARTIFACT = {
    "_format": "hh-sol-artifact-1",
    "contractName": "MyContract",
    "sourceName": "contracts/MyContract.sol",
    "abi": [
        {
            "inputs": [{"name": "greeting", "type": "string"}],
            "stateMutability": "nonpayable",
            "type": "constructor"
        },
        {
            "inputs": [],
            "name": "greet",
            "outputs": [{"name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function"
        }
    ],
    "bytecode": "0x608060405234801561001057600080fd5b50..."
}

MOCK_NETWORKS = {
    "sepolia": {
        "rpc_url": "https://sepolia.infura.io/v3/MOCK",
        "chain_id": 11155111
    }
}

def test_export_abi_success(tmp_path):
    # Set up mock artifacts folder
    artifacts_dir = tmp_path / "artifacts"
    contract_dir = artifacts_dir / "MyContract.sol"
    contract_dir.mkdir(parents=True)
    artifact_file = contract_dir / "MyContract.json"
    artifact_file.write_text(json.dumps(MOCK_ARTIFACT))

    dest_dir = tmp_path / "exports"

    params = {
        "contract": "MyContract",
        "destination": str(dest_dir),
        "artifacts_dir": str(artifacts_dir),
        "network": "sepolia",
        "address": "0x1234567890123456789012345678901234567890",
        "typescript": True,
        "include_bytecode": True
    }

    result = export_abi(params, networks_config=MOCK_NETWORKS)
    assert result['status'] == 'success'
    assert result['contract'] == 'MyContract'

    # Verify ABI JSON
    abi_json_file = dest_dir / "MyContract.abi.json"
    assert abi_json_file.exists()
    abi_data = json.loads(abi_json_file.read_text())
    assert len(abi_data) == 2
    assert abi_data[1]['name'] == 'greet'

    # Verify Deployment Package JSON
    pkg_file = dest_dir / "MyContract.sepolia.json"
    assert pkg_file.exists()
    pkg_data = json.loads(pkg_file.read_text())
    assert pkg_data['address'] == "0x1234567890123456789012345678901234567890"
    assert pkg_data['network'] == "sepolia"
    assert pkg_data['chainId'] == 11155111
    assert "bytecode" in pkg_data

    # Verify TypeScript Export
    ts_file = dest_dir / "MyContract.ts"
    assert ts_file.exists()
    ts_content = ts_file.read_text()
    assert "export const MyContractABI =" in ts_content
    assert "as const;" in ts_content
    assert 'export const MyContractAddress = "0x1234567890123456789012345678901234567890" as const;' in ts_content

def test_export_abi_missing_contract_param():
    params = {}
    result = export_abi(params)
    assert result['status'] == 'failure'
    assert "Missing 'contract' parameter" in result['error']

def test_export_abi_artifact_not_found(tmp_path):
    empty_artifacts = tmp_path / "empty_artifacts"
    empty_artifacts.mkdir()

    params = {
        "contract": "NonExistent",
        "artifacts_dir": str(empty_artifacts)
    }
    result = export_abi(params)
    assert result['status'] == 'failure'
    assert "Artifact for 'NonExistent' not found" in result['error']

def test_export_abi_address_fallback_from_deployed_contracts(tmp_path):
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    artifact_file = artifacts_dir / "Token.json"
    artifact_file.write_text(json.dumps(MOCK_ARTIFACT))

    dest_dir = tmp_path / "exports"

    params = {
        "contract": "Token",
        "destination": str(dest_dir),
        "artifacts_dir": str(artifacts_dir)
    }
    deployed_contracts = {"Token": "0xABCDEF1234567890ABCDEF1234567890ABCDEF12"}

    result = export_abi(params, deployed_contracts=deployed_contracts)
    assert result['status'] == 'success'

    pkg_file = dest_dir / "Token.deployment.json"
    assert pkg_file.exists()
    pkg_data = json.loads(pkg_file.read_text())
    assert pkg_data['address'] == "0xABCDEF1234567890ABCDEF1234567890ABCDEF12"

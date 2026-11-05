import pytest
import os
import json
from src.actions.safe_stage import safe_stage

def test_safe_stage_success(tmp_path):
    output_file = tmp_path / "safe-batch.json"
    params = {
        'contract': 'Treasury',
        'network': 'sepolia',
        'safe_address': '0x1234567890123456789012345678901234567890',
        'output': str(output_file)
    }
    networks_config = {
        'sepolia': {'chain_id': 11155111}
    }
    result = safe_stage(params, networks_config=networks_config)
    assert result['status'] == 'success'
    assert result['chain_id'] == '11155111'
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data['version'] == '1.0'
    assert data['chainId'] == '11155111'
    assert data['meta']['createdFromSafeAddress'] == '0x1234567890123456789012345678901234567890'
    assert len(data['transactions']) == 1

def test_safe_stage_custom_transactions(tmp_path):
    output_file = tmp_path / "custom-safe-batch.json"
    custom_txs = [
        {"to": "0xAAA", "value": "100", "data": "0x123"},
        {"to": "0xBBB", "value": "0", "data": "0x456"}
    ]
    params = {
        'network': 'mainnet',
        'transactions': custom_txs,
        'output': str(output_file)
    }
    networks_config = {
        'mainnet': {'chain_id': 1}
    }
    result = safe_stage(params, networks_config=networks_config)
    assert result['status'] == 'success'
    assert result['transactions_count'] == 2

    data = json.loads(output_file.read_text())
    assert len(data['transactions']) == 2
    assert data['transactions'][0]['to'] == "0xAAA"

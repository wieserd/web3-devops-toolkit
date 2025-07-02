import pytest
import os
import yaml
import json
from unittest.mock import patch, mock_open

from src.pipeline_runner import PipelineRunner

# Mock pipeline file content
MOCK_PIPELINE_CONTENT = """
name: Test Pipeline
jobs:
  - name: Test Compile
    uses: actions/compile@v1
    with:
      tool: hardhat
  - name: Test Deploy
    uses: actions/deploy@v1
    with:
      network: localhost
      contract: MyContract
      args: ["Hello"]
  - name: Test Verify
    uses: actions/verify@v1
    with:
      network: localhost
      contract: MyContract
      address: ${{ jobs.Test Deploy.output.address }}
"""

# Mock networks.json content
MOCK_NETWORKS_CONTENT = {
  "localhost": {
    "rpc_url": "http://127.0.0.1:8545",
    "chain_id": 31337,
    "etherscan_api_key": "mock_etherscan_key"
  }
}

@pytest.fixture
def mock_pipeline_file(tmp_path):
    pipeline_file = tmp_path / "test_pipeline.yaml"
    pipeline_file.write_text(MOCK_PIPELINE_CONTENT)
    return str(pipeline_file)

@pytest.fixture
def mock_networks_file(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    networks_file = config_dir / "networks.json"
    networks_file.write_text(json.dumps(MOCK_NETWORKS_CONTENT))
    return str(networks_file)

@patch('src.pipeline_runner.compile_contracts', return_value={'status': 'success'})
@patch('src.pipeline_runner.deploy_contract', return_value={'status': 'success', 'address': '0x1234567890123456789012345678901234567890'})
@patch('src.pipeline_runner.verify_contract', return_value={'status': 'success'})
def test_pipeline_runner_run_success(mock_verify, mock_deploy, mock_compile, mock_pipeline_file, mock_networks_file):
    # Mock os.path.exists for networks.json
    with patch('os.path.exists', side_effect=lambda path: True if "networks.json" in path or "test_pipeline.yaml" in path else False):
        # Mock open for networks.json
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(MOCK_NETWORKS_CONTENT)) as mocked_open:
            # Ensure the correct file is opened for networks.json
            mocked_open.side_effect = lambda filename, *args, **kwargs: (
                mock_open(read_data=MOCK_PIPELINE_CONTENT).return_value if "test_pipeline.yaml" in filename else
                mock_open(read_data=json.dumps(MOCK_NETWORKS_CONTENT)).return_value
            )
            runner = PipelineRunner(mock_pipeline_file)
            runner.run()

            mock_compile.assert_called_once()
            mock_deploy.assert_called_once()
            mock_verify.assert_called_once()
            assert runner.job_outputs['Test Deploy']['address'] == '0x1234567890123456789012345678901234567890'

def test_pipeline_runner_file_not_found():
    with pytest.raises(FileNotFoundError):
        PipelineRunner("/nonexistent/pipeline.yaml")

@patch('src.pipeline_runner.deploy_contract', return_value={'status': 'failure'})
def test_pipeline_runner_dynamic_param_resolution_failure(mock_deploy, mock_pipeline_file, mock_networks_file):
    # Modify pipeline content to simulate a failed deploy that doesn't return an address
    failed_deploy_pipeline = """
name: Test Pipeline Failed Deploy
jobs:
  - name: Test Deploy Failed
    uses: actions/deploy@v1
    with:
      network: localhost
      contract: MyContract
  - name: Test Verify After Failed Deploy
    uses: actions/verify@v1
    with:
      network: localhost
      contract: MyContract
      address: ${{ jobs.Test Deploy Failed.output.address }}
"""
    with patch('os.path.exists', side_effect=lambda path: True if "networks.json" in path or "test_pipeline.yaml" in path else False):
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(MOCK_NETWORKS_CONTENT)) as mocked_open:
            mocked_open.side_effect = lambda filename, *args, **kwargs: (
                mock_open(read_data=failed_deploy_pipeline).return_value if "test_pipeline.yaml" in filename else
                mock_open(read_data=json.dumps(MOCK_NETWORKS_CONTENT)).return_value
            )
            runner = PipelineRunner(mock_pipeline_file)
            runner.run()
            # Verify that the address for verification is None or not set due to failed deploy
            assert runner.job_outputs['Test Deploy Failed']['status'] == 'failure'
            # The verify action should have been called with address=None or similar
            # (depending on how verify_contract handles None address)

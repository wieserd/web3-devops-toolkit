import os
import yaml
import json
import subprocess
import re

from .actions.compile import compile_contracts
from .actions.deploy import deploy_contract
from .actions.verify import verify_contract

class PipelineRunner:
    def __init__(self, pipeline_path):
        self.pipeline_path = pipeline_path
        self.pipeline_data = self._load_pipeline()
        self.deployed_contracts = {} # To store deployed contract addresses
        self.job_outputs = {} # To store outputs from each job
        self.networks_config = self._load_networks_config()

    def _load_networks_config(self):
        networks_config_path = os.path.join(os.path.dirname(self.pipeline_path), '..', 'config', 'networks.json')
        networks_config_path = os.path.abspath(networks_config_path)
        if not os.path.exists(networks_config_path):
            print(f"Warning: Network configuration file not found: {networks_config_path}")
            return {}
        with open(networks_config_path, 'r') as f:
            return json.load(f)

    def _load_pipeline(self):
        if not os.path.exists(self.pipeline_path):
            raise FileNotFoundError(f"Pipeline file not found: {self.pipeline_path}")
        with open(self.pipeline_path, 'r') as f:
            return yaml.safe_load(f)

    def _resolve_params(self, params):
        resolved_params = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith('${{') and value.endswith('}}'):
                # Expected format: ${{ jobs.<job_name>.output.<key> }}
                try:
                    parts = value[3:-2].strip().split('.')
                    if len(parts) == 4 and parts[0] == 'jobs' and parts[2] == 'output':
                        job_name = parts[1]
                        output_key = parts[3]
                        if job_name in self.job_outputs and output_key in self.job_outputs[job_name]:
                            resolved_params[key] = self.job_outputs[job_name][output_key]
                        else:
                            print(f"  [⚠️] Warning: Could not resolve dynamic parameter '{value}'. Job output not found.")
                            resolved_params[key] = None # Or keep original value, depending on desired behavior
                    else:
                        resolved_params[key] = value # Not a recognized dynamic parameter format
                except Exception as e:
                    print(f"  [⚠️] Warning: Error resolving dynamic parameter '{value}': {e}")
                    resolved_params[key] = value
            else:
                resolved_params[key] = value
        return resolved_params

    def run(self):
        print(f"\n--- Running Pipeline: {self.pipeline_data.get('name', 'Unnamed Pipeline')} ---")
        jobs = self.pipeline_data.get('jobs', [])
        for job in jobs:
            self._execute_job(job)
        print("\n--- Pipeline Finished ---")

    def _execute_job(self, job):
        job_name = job.get('name', 'Unnamed Job')
        uses_action = job.get('uses')
        with_params = job.get('with', {})
        resolved_params = self._resolve_params(with_params)

        print(f"\n>>> Executing Job: {job_name} ({uses_action}) <<<")

        job_output = None
        if uses_action == "actions/compile@v1":
            job_output = compile_contracts(resolved_params)
        elif uses_action == "actions/deploy@v1":
            job_output = deploy_contract(resolved_params, self.pipeline_path, self.deployed_contracts, networks_config=self.networks_config)
        elif uses_action == "actions/verify@v1":
            job_output = verify_contract(resolved_params, self.pipeline_path, self.deployed_contracts, networks_config=self.networks_config)
        else:
            print(f"  [❌] Unknown action: {uses_action}")
            job_output = None

        if job_output is not None:
            self.job_outputs[job_name] = job_output

    

    

    
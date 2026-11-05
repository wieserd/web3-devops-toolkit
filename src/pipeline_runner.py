import os
import yaml
import json
import subprocess
import re
from datetime import datetime, timezone

from .actions.compile import compile_contracts
from .actions.deploy import deploy_contract
from .actions.verify import verify_contract
from .actions.test import test_contracts
from .actions.security_scan import security_scan
from .actions.export_abi import export_abi
from .actions.smoke_test import smoke_test
from .actions.notify import send_notification
from .actions.gas_check import gas_check
from .actions.safe_stage import safe_stage
from .actions.proxy import manage_proxy

SUPPORTED_ACTIONS = {
    "actions/compile@v1": compile_contracts,
    "actions/deploy@v1": deploy_contract,
    "actions/verify@v1": verify_contract,
    "actions/test@v1": test_contracts,
    "actions/security_scan@v1": security_scan,
    "actions/export_abi@v1": export_abi,
    "actions/smoke_test@v1": smoke_test,
    "actions/notify@v1": send_notification,
    "actions/gas_check@v1": gas_check,
    "actions/safe_stage@v1": safe_stage,
    "actions/proxy@v1": manage_proxy,
}

class PipelineRunner:
    def __init__(self, pipeline_path, manifest_path=None, dry_run=False):
        self.pipeline_path = os.path.abspath(pipeline_path)
        self.manifest_path = manifest_path
        self.dry_run = dry_run
        self.pipeline_data = self._load_pipeline()
        self.deployed_contracts = {}  # contract_name -> address
        self.deployed_details = {}   # contract_name -> {address, network, timestamp}
        self.job_outputs = {}        # job_name -> output dict
        self.networks_config = self._load_networks_config()

    def _load_networks_config(self):
        # 1. Try relative to pipeline file
        networks_config_path = os.path.abspath(os.path.join(os.path.dirname(self.pipeline_path), '..', 'config', 'networks.json'))
        if not os.path.exists(networks_config_path):
            # 2. Try relative to project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            networks_config_path = os.path.join(project_root, 'config', 'networks.json')

        if not os.path.exists(networks_config_path):
            return {}
        try:
            with open(networks_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load networks config at {networks_config_path}: {e}")
            return {}

    def _load_pipeline(self):
        if not os.path.exists(self.pipeline_path):
            raise FileNotFoundError(f"Pipeline file not found: {self.pipeline_path}")
        with open(self.pipeline_path, 'r') as f:
            return yaml.safe_load(f) or {}

    def validate(self):
        """
        Validates pipeline structure, required keys, and action support without running.
        Returns (is_valid: bool, issues: list).
        """
        issues = []
        if not isinstance(self.pipeline_data, dict):
            return False, ["Pipeline YAML root must be a mapping/dict"]

        if 'jobs' not in self.pipeline_data or not isinstance(self.pipeline_data['jobs'], list):
            issues.append("Pipeline must contain a 'jobs' list")
            return False, issues

        for i, job in enumerate(self.pipeline_data['jobs']):
            if not isinstance(job, dict):
                issues.append(f"Job #{i+1} is not a valid dictionary")
                continue
            name = job.get('name', f'Job #{i+1}')
            uses = job.get('uses')
            if not uses:
                issues.append(f"Job '{name}' missing required 'uses' action")
            elif uses not in SUPPORTED_ACTIONS:
                issues.append(f"Job '{name}' specifies unsupported action '{uses}'. Supported: {list(SUPPORTED_ACTIONS.keys())}")

        return (len(issues) == 0), issues

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
                            resolved_params[key] = None
                    else:
                        resolved_params[key] = value
                except Exception as e:
                    print(f"  [⚠️] Warning: Error resolving dynamic parameter '{value}': {e}")
                    resolved_params[key] = value
            else:
                resolved_params[key] = value
        return resolved_params

    def _apply_env(self, env_vars):
        if env_vars and isinstance(env_vars, dict):
            for k, v in env_vars.items():
                if v is not None:
                    os.environ[str(k)] = str(v)

    def _should_run_job(self, condition, pipeline_failed):
        """
        Evaluates execution conditions ('success()', 'failure()', 'always()').
        """
        if not condition or condition.strip() == "success()":
            return not pipeline_failed
        cond = condition.strip().lower()
        if cond == "failure()":
            return pipeline_failed
        elif cond == "always()":
            return True
        return not pipeline_failed

    def run(self):
        pipeline_name = self.pipeline_data.get('name', 'Unnamed Pipeline')
        print(f"\n--- Running Pipeline: {pipeline_name} ---")

        # Apply global pipeline env if present
        self._apply_env(self.pipeline_data.get('env', {}))

        jobs = self.pipeline_data.get('jobs', [])
        pipeline_failed = False

        for job in jobs:
            job_name = job.get('name', 'Unnamed Job')
            condition = job.get('if')
            continue_on_error = job.get('continue-on-error', False) or job.get('continue_on_error', False)

            # Check job condition
            if not self._should_run_job(condition, pipeline_failed):
                print(f"  [⏭️] Skipping Job: {job_name} (condition '{condition or 'success()'}' not met)")
                self.job_outputs[job_name] = {'status': 'skipped'}
                continue

            # Apply job-level env if present
            self._apply_env(job.get('env', {}))

            if self.dry_run:
                print(f"  [DRY-RUN] Would execute job: {job_name} ({job.get('uses')})")
                self.job_outputs[job_name] = {'status': 'dry_run_success'}
                continue

            job_output = self._execute_job(job)
            is_job_failure = isinstance(job_output, dict) and job_output.get('status') == 'failure'

            if is_job_failure:
                pipeline_failed = True
                if not continue_on_error:
                    print(f"  [🛑] Job '{job_name}' failed. Subsequent success-only jobs will be skipped.")
                else:
                    print(f"  [⚠️] Job '{job_name}' failed but continue-on-error is enabled.")

        success = not pipeline_failed
        if success:
            print("\n--- Pipeline Finished Successfully ---")
        else:
            print("\n--- Pipeline Finished With Errors ---")

        # Export manifest if requested
        self._export_manifest_if_configured()

        return success

    def _execute_job(self, job):
        job_name = job.get('name', 'Unnamed Job')
        uses_action = job.get('uses')
        with_params = job.get('with', {}) or {}
        resolved_params = self._resolve_params(with_params)

        print(f"\n>>> Executing Job: {job_name} ({uses_action}) <<<")

        job_output = None
        if uses_action == "actions/compile@v1":
            job_output = compile_contracts(resolved_params)
        elif uses_action == "actions/deploy@v1":
            job_output = deploy_contract(
                resolved_params,
                self.pipeline_path,
                self.deployed_contracts,
                networks_config=self.networks_config
            )
            # Track deployment details if successful
            if isinstance(job_output, dict) and job_output.get('status') == 'success' and 'address' in job_output:
                contract_name = resolved_params.get('contract', 'UnknownContract')
                network_name = resolved_params.get('network', 'unknown')
                self.deployed_details[contract_name] = {
                    "address": job_output['address'],
                    "network": network_name,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        elif uses_action == "actions/verify@v1":
            job_output = verify_contract(
                resolved_params,
                self.pipeline_path,
                self.deployed_contracts,
                networks_config=self.networks_config
            )
        elif uses_action == "actions/test@v1":
            job_output = test_contracts(resolved_params)
        elif uses_action == "actions/security_scan@v1":
            job_output = security_scan(resolved_params)
        elif uses_action == "actions/export_abi@v1":
            job_output = export_abi(
                resolved_params,
                self.pipeline_path,
                self.deployed_contracts,
                networks_config=self.networks_config
            )
        elif uses_action == "actions/smoke_test@v1":
            job_output = smoke_test(
                resolved_params,
                self.pipeline_path,
                self.deployed_contracts,
                networks_config=self.networks_config
            )
        elif uses_action == "actions/notify@v1":
            job_output = send_notification(
                resolved_params,
                self.pipeline_path,
                self.deployed_contracts,
                networks_config=self.networks_config
            )
        elif uses_action == "actions/gas_check@v1":
            job_output = gas_check(
                resolved_params,
                self.pipeline_path,
                self.deployed_contracts,
                networks_config=self.networks_config
            )
        elif uses_action == "actions/safe_stage@v1":
            job_output = safe_stage(
                resolved_params,
                self.pipeline_path,
                self.deployed_contracts,
                networks_config=self.networks_config
            )
        elif uses_action == "actions/proxy@v1":
            job_output = manage_proxy(
                resolved_params,
                self.pipeline_path,
                self.deployed_contracts,
                networks_config=self.networks_config
            )
        else:
            print(f"  [❌] Unknown action: {uses_action}")
            job_output = {'status': 'failure', 'error': f'Unknown action: {uses_action}'}

        if job_output is not None:
            self.job_outputs[job_name] = job_output

        return job_output

    def _export_manifest_if_configured(self):
        target_path = self.manifest_path or self.pipeline_data.get('manifest')
        if not target_path:
            return

        target_abs_path = os.path.abspath(target_path)
        os.makedirs(os.path.dirname(target_abs_path), exist_ok=True)

        manifest_data = {
            "pipeline": self.pipeline_data.get('name', 'Pipeline'),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contracts": self.deployed_details,
            "jobs_summary": {k: v.get('status') for k, v in self.job_outputs.items() if isinstance(v, dict)}
        }

        with open(target_abs_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)

        print(f"  [📦] Deployment manifest exported to {target_abs_path}")

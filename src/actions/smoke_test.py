import os
import json
import subprocess
from .common import clean_env, get_contracts_dir

def smoke_test(params, pipeline_path=None, deployed_contracts=None, networks_config=None):
    """
    Executes live on-chain smoke tests (getter calls & assertion checks) against a deployed contract.
    """
    network = params.get('network')
    contract = params.get('contract')
    address = params.get('address')
    calls = params.get('calls', [])
    script_path = params.get('script', 'scripts/smoke_test.js')
    contracts_dir = get_contracts_dir(params)

    if not network:
        print("  [❌] Missing required parameter 'network' for smoke_test action.")
        return {'status': 'failure', 'error': "Missing 'network' parameter"}

    if not contract:
        print("  [❌] Missing required parameter 'contract' for smoke_test action.")
        return {'status': 'failure', 'error': "Missing 'contract' parameter"}

    # Resolve address from deployed_contracts registry if not explicitly provided
    if not address and deployed_contracts and contract in deployed_contracts:
        address = deployed_contracts[contract]

    if not address:
        print(f"  [❌] No contract address provided or found for '{contract}' to smoke test.")
        return {'status': 'failure', 'error': 'No address to smoke test'}

    print(f"  [🧪] Running on-chain smoke test for {contract} at {address} on {network}...")

    env = os.environ.copy()
    env = clean_env(env)
    env["CONTRACT_NAME"] = contract
    env["CONTRACT_ADDRESS"] = address
    env["SMOKE_CALLS"] = json.dumps(calls)

    try:
        result = subprocess.run(
            ["npx", "hardhat", "run", script_path, "--network", network],
            cwd=contracts_dir,
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        print(result.stdout)
        print(f"  [✅] Smoke tests successfully verified on-chain state for {contract}.")
        return {'status': 'success', 'contract': contract, 'address': address, 'network': network}
    except subprocess.CalledProcessError as e:
        print(f"  [❌] On-chain smoke test failed for {contract} at {address}.")
        print(f"  Stdout: {e.stdout}")
        print(f"  Stderr: {e.stderr}")
        return {'status': 'failure', 'error': e.stderr or e.stdout}
    except FileNotFoundError:
        print("  [❌] npx or hardhat command not found. Ensure Hardhat is installed.")
        return {'status': 'failure', 'error': 'npx/hardhat not found'}

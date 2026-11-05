import os
import json
import re
import subprocess
from .common import clean_env, get_contracts_dir

def gas_check(params, pipeline_path=None, deployed_contracts=None, networks_config=None):
    """
    Estimates contract deployment gas and enforces gas budget constraints.
    """
    network = params.get('network', 'localhost')
    contract = params.get('contract')
    args = params.get('args', [])
    max_gas_limit = params.get('max_gas_limit')
    fail_on_exceed = params.get('fail_on_exceed', True)
    script_path = params.get('script', 'scripts/gas_estimate.js')
    contracts_dir = get_contracts_dir(params)

    if not contract:
        print("  [❌] Missing required parameter 'contract' in gas_check action.")
        return {'status': 'failure', 'error': "Missing 'contract' parameter"}

    print(f"  [⛽] Checking deployment gas budget for '{contract}' on '{network}'...")

    env = os.environ.copy()
    env = clean_env(env)
    env["CONTRACT_NAME"] = contract
    env["CONTRACT_ARGS"] = json.dumps(args)

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

        # Parse estimated gas
        match = re.search(r'Estimated Gas Units: (\d+)', result.stdout)
        if not match:
            print("  [❌] Could not extract estimated gas units from output.")
            return {'status': 'failure', 'error': 'Gas estimation output not parseable'}

        estimated_gas = int(match.group(1))

        # Check gas price and cost
        gas_price_match = re.search(r'Gas Price \(Wei\): (\d+)', result.stdout)
        gas_price_wei = int(gas_price_match.group(1)) if gas_price_match else 0

        cost_match = re.search(r'Estimated Cost \(Wei\): (\d+)', result.stdout)
        cost_wei = int(cost_match.group(1)) if cost_match else 0

        # Check budget
        if max_gas_limit is not None:
            max_limit = int(max_gas_limit)
            if estimated_gas > max_limit:
                msg = f"Gas budget exceeded for {contract}! Estimated: {estimated_gas:,} units > Max allowed: {max_limit:,} units"
                print(f"  [❌] {msg}")
                if fail_on_exceed:
                    return {
                        'status': 'failure',
                        'error': msg,
                        'estimated_gas': estimated_gas,
                        'max_gas_limit': max_limit
                    }
            else:
                print(f"  [✅] Gas check passed: {estimated_gas:,} units <= budget of {max_limit:,} units.")
        else:
            print(f"  [ℹ️] Estimated gas: {estimated_gas:,} units (no max limit enforced).")

        return {
            'status': 'success',
            'contract': contract,
            'network': network,
            'estimated_gas': estimated_gas,
            'gas_price_wei': gas_price_wei,
            'estimated_cost_wei': cost_wei,
            'max_gas_limit': max_gas_limit
        }

    except subprocess.CalledProcessError as e:
        print(f"  [❌] Gas check execution failed: {e.stderr or e.stdout}")
        return {'status': 'failure', 'error': e.stderr or e.stdout}
    except FileNotFoundError:
        print("  [❌] npx or hardhat command not found.")
        return {'status': 'failure', 'error': 'npx/hardhat not found'}

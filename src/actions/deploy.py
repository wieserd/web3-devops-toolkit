import os
import json
import subprocess
import re
from .common import clean_env as _clean_env, get_contracts_dir

def deploy_contract(params, pipeline_path, deployed_contracts, networks_config=None):
    network = params.get('network')
    contract = params.get('contract')
    args = params.get('args', [])
    contracts_dir = get_contracts_dir(params)
    script_path = params.get('script', 'scripts/deploy.js')

    print(f"  [⚙️] Deploying {contract} to {network}...")

    # Load network configuration
    if networks_config is None:
        networks_config_path = os.path.join(os.path.dirname(pipeline_path), '..', 'config', 'networks.json')
        networks_config_path = os.path.abspath(networks_config_path)

        if not os.path.exists(networks_config_path):
            print(f"  [❌] Network configuration file not found: {networks_config_path}")
            return {'status': 'failure', 'error': 'Network config not found'}

        with open(networks_config_path, 'r') as f:
            networks_config = json.load(f)

    network_details = networks_config.get(network)
    if network_details is None:
        print(f"  [❌] Network '{network}' not found in networks.json")
        return {'status': 'failure', 'error': f'Network {network} not found'}

    rpc_url = network_details.get('rpc_url')
    if not rpc_url:
        print(f"  [❌] RPC URL not configured for network '{network}'")
        return {'status': 'failure', 'error': 'RPC URL not configured'}

    try:
        # Pass contract name and arguments to deployment script
        env = os.environ.copy()
        env = _clean_env(env)  # Clean the environment
        env["CONTRACT_NAME"] = contract
        env["CONTRACT_ARGS"] = json.dumps(args)
        if args:
            env["INITIAL_GREETING"] = str(args[0])

        # Run npx hardhat run scripts/deploy.js --network <network>
        result = subprocess.run(
            ["npx", "hardhat", "run", script_path, "--network", network],
            cwd=contracts_dir,
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        print(result.stdout)
        # Extract deployed address (support named contract or generic deployed to)
        match = re.search(rf'{re.escape(contract)} deployed to (0x[a-fA-F0-9]{{40}})', result.stdout)
        if not match:
            match = re.search(r'deployed to (0x[a-fA-F0-9]{40})', result.stdout)

        if match:
            deployed_address = match.group(1)
            print(f"  [✅] Deployment successful. Address: {deployed_address}")
            deployed_contracts[contract] = deployed_address  # Keep for internal tracking
            return {'status': 'success', 'address': deployed_address}
        else:
            print("  [❌] Deployment successful, but could not extract contract address.")
            return {'status': 'failure', 'error': 'Could not extract address'}

    except subprocess.CalledProcessError as e:
        print(f"  [❌] Hardhat deployment failed.")
        print(f"  Stderr: {e.stderr}")
        print(f"  Stdout: {e.stdout}")
        return {'status': 'failure', 'error': e.stderr}
    except FileNotFoundError:
        print("  [❌] npx or hardhat command not found. Make sure Hardhat is installed.")
        return {'status': 'failure', 'error': 'npx/hardhat not found'}
    except json.JSONDecodeError:
        print(f"  [❌] Error parsing networks.json: {networks_config_path}")
        return {'status': 'failure', 'error': 'Invalid networks.json'}

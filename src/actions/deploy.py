import os
import json
import subprocess
import re

def _clean_env(env):
    # Remove pytest-specific and other volatile environment variables
    keys_to_remove = [
        k for k in env if k.startswith('PYTEST_') or k.startswith('TERM_') or k.startswith('SHLVL') or
        k.startswith('OLDPWD') or k.startswith('PWD') or k.startswith('_') or k.startswith('CONDA_') or
        k.startswith('HOMEBREW_') or k.startswith('INFOPATH') or k.startswith('DISPLAY') or
        k.startswith('npm_') or k.startswith('XPC_') or k.startswith('__CF_') or k.startswith('SSH_') or
        k.startswith('LOGNAME') or k.startswith('USER') or k.startswith('TMPDIR') or k.startswith('SHELL') or
        k.startswith('INIT_CWD') or k.startswith('NODE') or k.startswith('COLOR') or k.startswith('LANG') or
        k.startswith('EDITOR') or k.startswith('__CFBundleIdentifier') or
        k.startswith('OBJC_DISABLE_INITIALIZE_FORK_SAFETY') or k.startswith('__PYVENV_LAUNCHER__') or
        k.startswith('__VIRTUAL_ENV__') or k.startswith('VIRTUAL_ENV')
    ]
    for key in keys_to_remove:
        env.pop(key, None)
    return env

def deploy_contract(params, pipeline_path, deployed_contracts, networks_config=None):
    network = params.get('network')
    contract = params.get('contract')
    args = params.get('args', [])

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
        # Pass arguments as environment variables for now
        env = os.environ.copy()
        env = _clean_env(env) # Clean the environment
        if args:
            env["INITIAL_GREETING"] = args[0] # Assuming first arg is initial greeting

        # Run npx hardhat run scripts/deploy.js --network <network>
        result = subprocess.run(
            ["npx", "hardhat", "run", "scripts/deploy.js", "--network", network],
            cwd="/Users/dw2022/web3-devops-toolkit/contracts",
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        print(result.stdout)
        # Extract deployed address (simple regex for now)
        match = re.search(r'MyContract deployed to (0x[a-fA-F0-9]{40})', result.stdout)
        if match:
            deployed_address = match.group(1)
            print(f"  [✅] Deployment successful. Address: {deployed_address}")
            deployed_contracts[contract] = deployed_address # Keep for internal tracking
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
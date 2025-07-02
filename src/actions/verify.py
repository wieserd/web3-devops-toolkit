import os
import json
import subprocess

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

def verify_contract(params, pipeline_path, deployed_contracts, networks_config=None):
    network = params.get('network')
    contract = params.get('contract')
    address = params.get('address') # This will come from the pipeline output or direct param

    print(f"  [⚙️] Verifying {contract} on {network}...")

    if not address:
        # Try to get the address from previously deployed contracts
        address = deployed_contracts.get(contract)
        if not address:
            print(f"  [❌] No contract address provided or found for {contract} to verify.")
            return {'status': 'failure', 'error': 'No address to verify'}

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
    if not network_details:
        print(f"  [❌] Network '{network}' not found in networks.json")
        return {'status': 'failure', 'error': f'Network {network} not found'}

    etherscan_api_key = network_details.get('etherscan_api_key')
    if not etherscan_api_key:
        print(f"  [❌] Etherscan API key not configured for network '{network}'. Cannot verify.")
        return {'status': 'failure', 'error': 'Etherscan API key missing'}

    try:
        # Set Etherscan API key as environment variable for Hardhat
        env = os.environ.copy()
        env = _clean_env(env) # Clean the environment
        env["ETHERSCAN_API_KEY"] = etherscan_api_key

        # Run npx hardhat verify --network <network> <address>
        result = subprocess.run(
            ["npx", "hardhat", "verify", "--network", network, address],
            cwd="/Users/dw2022/web3-devops-toolkit/contracts",
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        print(result.stdout)
        print("  [✅] Verification successful.")
        return {'status': 'success'}

    except subprocess.CalledProcessError as e:
        print(f"  [❌] Hardhat verification failed.")
        print(f"  Stderr: {e.stderr}")
        print(f"  Stdout: {e.stdout}")
        return {'status': 'failure', 'error': e.stderr}
    except FileNotFoundError:
        print("  [❌] npx or hardhat command not found. Make sure Hardhat is installed.")
        return {'status': 'failure', 'error': 'npx/hardhat not found'}
    except json.JSONDecodeError:
        print(f"  [❌] Error parsing networks.json: {networks_config_path}")
        return {'status': 'failure', 'error': 'Invalid networks.json'}

import os
import json
import re
import subprocess
from .common import clean_env, get_contracts_dir

def manage_proxy(params, pipeline_path=None, deployed_contracts=None, networks_config=None):
    """
    Deploys or upgrades ERC-1967 / UUPS upgradeable proxies and implementation contracts.
    """
    network = params.get('network', 'localhost')
    contract = params.get('contract')
    operation = params.get('operation', 'deploy').lower()
    proxy_address = params.get('proxy_address')
    init_args = params.get('init_args', [])
    script_path = params.get('script', 'scripts/proxy_manage.js')
    contracts_dir = get_contracts_dir(params)

    if not contract:
        print("  [❌] Missing required parameter 'contract' in proxy action.")
        return {'status': 'failure', 'error': "Missing 'contract' parameter"}

    if operation == "upgrade":
        # Resolve proxy address from registry if not provided directly
        if not proxy_address and deployed_contracts and contract in deployed_contracts:
            proxy_address = deployed_contracts[contract]
        if not proxy_address:
            print(f"  [❌] Missing required 'proxy_address' for upgrade operation on '{contract}'.")
            return {'status': 'failure', 'error': "Missing 'proxy_address' for upgrade"}

    print(f"  [🔄] Proxy operation '{operation}' for '{contract}' on '{network}'...")

    env = os.environ.copy()
    env = clean_env(env)
    env["CONTRACT_NAME"] = contract
    env["PROXY_OPERATION"] = operation
    env["INIT_ARGS"] = json.dumps(init_args)
    if proxy_address:
        env["PROXY_ADDRESS"] = proxy_address

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

        # Extract implementation address
        impl_match = re.search(r'Implementation deployed to (0x[a-fA-F0-9]{40})', result.stdout)
        implementation_address = impl_match.group(1) if impl_match else None

        # Extract proxy address
        proxy_match = re.search(r'Proxy (?:deployed|upgraded) to (0x[a-fA-F0-9]{40})', result.stdout)
        resolved_proxy_address = proxy_match.group(1) if proxy_match else proxy_address

        if deployed_contracts is not None and resolved_proxy_address:
            deployed_contracts[contract] = resolved_proxy_address

        print(f"  [✅] Proxy {operation} completed. Proxy: {resolved_proxy_address}, Impl: {implementation_address}")
        return {
            'status': 'success',
            'contract': contract,
            'network': network,
            'operation': operation,
            'address': resolved_proxy_address,
            'proxy_address': resolved_proxy_address,
            'implementation_address': implementation_address
        }

    except subprocess.CalledProcessError as e:
        print(f"  [❌] Proxy management failed: {e.stderr or e.stdout}")
        return {'status': 'failure', 'error': e.stderr or e.stdout}
    except FileNotFoundError:
        print("  [❌] npx or hardhat command not found.")
        return {'status': 'failure', 'error': 'npx/hardhat not found'}

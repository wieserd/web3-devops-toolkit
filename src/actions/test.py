import os
import subprocess
from .common import clean_env, get_contracts_dir

def test_contracts(params):
    """
    Executes smart contract tests using Hardhat or Foundry.
    """
    tool = params.get('tool', 'hardhat')
    contracts_dir = get_contracts_dir(params)
    network = params.get('network')
    test_files = params.get('test_files', [])

    print(f"  [🧪] Running contract tests using {tool} in {contracts_dir}...")

    env = clean_env(os.environ.copy())

    if tool == 'hardhat':
        cmd = ["npx", "hardhat", "test"]
        if network:
            cmd.extend(["--network", network])
        if test_files:
            if isinstance(test_files, list):
                cmd.extend(test_files)
            elif isinstance(test_files, str):
                cmd.append(test_files)

        try:
            result = subprocess.run(
                cmd,
                cwd=contracts_dir,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            print(result.stdout)
            print("  [✅] All smart contract tests passed.")
            return {'status': 'success'}
        except subprocess.CalledProcessError as e:
            print(f"  [❌] Hardhat tests failed.")
            print(f"  Stderr: {e.stderr}")
            print(f"  Stdout: {e.stdout}")
            return {'status': 'failure', 'error': e.stderr or e.stdout}
        except FileNotFoundError:
            print("  [❌] npx or hardhat command not found.")
            return {'status': 'failure', 'error': 'npx/hardhat not found'}

    elif tool == 'foundry':
        cmd = ["forge", "test"]
        if test_files:
            if isinstance(test_files, list) and test_files:
                cmd.extend(["--match-path", test_files[0]])
            elif isinstance(test_files, str):
                cmd.extend(["--match-path", test_files])

        try:
            result = subprocess.run(
                cmd,
                cwd=contracts_dir,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            print(result.stdout)
            print("  [✅] All Foundry tests passed.")
            return {'status': 'success'}
        except subprocess.CalledProcessError as e:
            print(f"  [❌] Foundry tests failed.")
            print(f"  Stderr: {e.stderr}")
            print(f"  Stdout: {e.stdout}")
            return {'status': 'failure', 'error': e.stderr or e.stdout}
        except FileNotFoundError:
            print("  [❌] forge command not found.")
            return {'status': 'failure', 'error': 'forge not found'}

    else:
        print(f"  [❌] Unsupported testing tool: {tool}")
        return {'status': 'failure', 'error': f'Unsupported testing tool: {tool}'}

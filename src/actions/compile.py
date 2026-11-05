import subprocess
from .common import get_contracts_dir

def compile_contracts(params):
    tool = params.get('tool', 'hardhat')
    contracts_dir = get_contracts_dir(params)

    if tool == 'hardhat':
        print(f"  [⚙️] Compiling contracts with Hardhat in {contracts_dir}...")
        try:
            result = subprocess.run(
                ["npx", "hardhat", "compile"],
                cwd=contracts_dir,
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            print("  [✅] Compilation successful.")
            return {'status': 'success'}
        except subprocess.CalledProcessError as e:
            print(f"  [❌] Hardhat compilation failed.")
            print(f"  Stderr: {e.stderr}")
            print(f"  Stdout: {e.stdout}")
            return {'status': 'failure', 'error': e.stderr}
        except FileNotFoundError:
            print("  [❌] npx or hardhat command not found. Make sure Hardhat is installed.")
            return {'status': 'failure', 'error': 'npx/hardhat not found'}

    elif tool == 'foundry':
        print(f"  [⚙️] Compiling contracts with Foundry (forge build) in {contracts_dir}...")
        try:
            result = subprocess.run(
                ["forge", "build"],
                cwd=contracts_dir,
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            print("  [✅] Foundry compilation successful.")
            return {'status': 'success'}
        except subprocess.CalledProcessError as e:
            print(f"  [❌] Foundry compilation failed.")
            print(f"  Stderr: {e.stderr}")
            print(f"  Stdout: {e.stdout}")
            return {'status': 'failure', 'error': e.stderr}
        except FileNotFoundError:
            print("  [❌] forge command not found. Make sure Foundry is installed.")
            return {'status': 'failure', 'error': 'forge not found'}

    else:
        print(f"  [❌] Unsupported compilation tool: {tool}")
        return {'status': 'failure', 'error': f'Unsupported tool: {tool}'}

import os
import subprocess
from .common import clean_env, get_contracts_dir

def security_scan(params):
    """
    Executes security and quality scanning for smart contracts (Slither, Solhint).
    """
    tool = params.get('tool', 'solhint')
    contracts_dir = get_contracts_dir(params)
    env = clean_env(os.environ.copy())

    print(f"  [🛡️] Running security scan with {tool} in {contracts_dir}...")

    if tool == 'solhint':
        path_pattern = params.get('pattern', '**/*.sol')
        cmd = ["npx", "solhint", path_pattern]
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
            print("  [✅] Solhint scan passed with no critical errors.")
            return {'status': 'success'}
        except subprocess.CalledProcessError as e:
            print(f"  [⚠️] Solhint found issues.")
            print(f"  Stdout: {e.stdout}")
            print(f"  Stderr: {e.stderr}")
            return {'status': 'failure', 'error': e.stdout or e.stderr}
        except FileNotFoundError:
            print("  [❌] npx or solhint command not found.")
            return {'status': 'failure', 'error': 'npx/solhint not found'}

    elif tool == 'slither':
        target = params.get('target', '.')
        cmd = ["slither", target]
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
            print("  [✅] Slither analysis passed.")
            return {'status': 'success'}
        except subprocess.CalledProcessError as e:
            print(f"  [⚠️] Slither detected potential vulnerabilities.")
            print(f"  Stdout: {e.stdout}")
            return {'status': 'failure', 'error': e.stdout or e.stderr}
        except FileNotFoundError:
            print("  [❌] Slither command not found. Ensure python slither-analyzer is installed.")
            return {'status': 'failure', 'error': 'slither not found'}

    else:
        print(f"  [❌] Unsupported security scan tool: {tool}")
        return {'status': 'failure', 'error': f'Unsupported security tool: {tool}'}

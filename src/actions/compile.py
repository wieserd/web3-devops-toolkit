import subprocess

def compile_contracts(params):
    tool = params.get('tool')
    if tool == 'hardhat':
        print("  [⚙️] Compiling contracts with Hardhat...")
        try:
            # Run npx hardhat compile in the contracts directory
            result = subprocess.run(
                ["npx", "hardhat", "compile"],
                cwd="/Users/dw2022/web3-devops-toolkit/contracts",
                capture_output=True,
                text=True,
                check=True  # Raise an exception for non-zero exit codes
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
    else:
        print(f"  [❌] Unsupported compilation tool: {tool}")
        return {'status': 'failure', 'error': f'Unsupported tool: {tool}'}

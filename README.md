# Web3 DevOps Toolkit

A streamlined, modular DevOps pipeline system for building, testing, security scanning, deploying, and verifying smart contracts across multiple blockchain networks.

---

## Highlights & Features

- **Declarative YAML Pipelines**: Define end-to-end Web3 workflows with dependencies, step ordering, and failure handling.
- **Universal Contract Deployer**: Deploy arbitrary smart contracts with arbitrary constructor argument types (strings, numbers, addresses, arrays) without rewriting JavaScript deploy scripts.
- **Dynamic Multi-Network Auto-Configuration**: Any EVM network defined in `config/networks.json` is automatically mapped into Hardhat's runtime configuration.
- **Dynamic Output Chaining**: Pass contract addresses and deploy outputs seamlessly to subsequent jobs using `${{ jobs.<job_name>.output.<key> }}`.
- **Dual Framework Support**: First-class support for both **Hardhat** and **Foundry** (`forge build`, `forge test`).
- **Comprehensive Modular Actions**:
  - `actions/compile@v1`: Smart contract compilation with Hardhat or Foundry.
  - `actions/test@v1`: Automated contract unit testing (Hardhat & Foundry).
  - `actions/security_scan@v1`: Static analysis and security scanning (Solhint, Slither).
  - `actions/deploy@v1`: Multi-network deployment with dynamic constructor arguments and address capture.
  - `actions/verify@v1`: Automated contract verification on Etherscan/block explorers with constructor argument support.
- **Deployment Manifest Export**: Export machine-readable deployment manifests (`--manifest`) with deployed addresses, network IDs, and timestamps.
- **Safe Pipeline Execution**:
  - `--dry-run` flag to validate execution flow without triggering blockchain transactions or subprocesses.
  - Syntax and schema validation command (`validate-pipeline`).
  - Job-level `continue-on-error: true` support.
  - Environment variable injection at pipeline and job levels.

---

## Supported Networks (Out of the Box)

Networks are configured in `config/networks.json` and automatically synchronized with the Hardhat runner:

| Network | Chain ID | Default RPC / Explorer |
|---|---|---|
| `localhost` | 31337 | `http://127.0.0.1:8545` (Hardhat / Anvil) |
| `sepolia` | 11155111 | Ethereum Sepolia Testnet |
| `arbitrum-sepolia` | 421614 | Arbitrum Sepolia Rollup |
| `optimism-sepolia` | 11155420 | Optimism Sepolia Rollup |
| `base-sepolia` | 84532 | Base Sepolia Rollup |
| `polygon-amoy` | 80002 | Polygon Amoy Testnet |
| `mainnet` | 1 | Ethereum Mainnet |

*To add any other network, simply add an entry to `config/networks.json`. Hardhat will detect and configure it automatically.*

---

## Installation & Setup

### 1. Environment Setup

Copy `.env.example` to `.env` and fill in your RPC URLs and private keys:
```bash
cp .env.example .env
```

### 2. Quickstart (`start.sh`)

Run the automated setup script from the project root:
```bash
./start.sh
```

This script will:
1. Verify Python 3 and npm dependencies.
2. Initialize or activate a Python virtual environment (`.venv`).
3. Install Python dependencies (`requirements.txt`).
4. Install Node.js dependencies (`contracts/package.json`).
5. Execute the example deployment pipeline.

### 3. Package Installation (Optional)

Install the toolkit as a CLI command in your virtual environment:
```bash
pip install -e .
web3-devops --help
```

---

## CLI Usage

### Run a Pipeline
```bash
# Execute deployment pipeline
python3 src/cli.py run-pipeline --pipeline pipelines/example_pipeline.yaml

# Dry-run without side effects (no compilers or transactions executed)
python3 src/cli.py run-pipeline --pipeline pipelines/example_pipeline.yaml --dry-run

# Run and export deployment manifest JSON
python3 src/cli.py run-pipeline --pipeline pipelines/example_pipeline.yaml --manifest deployments/sepolia.json
```

### Validate a Pipeline
```bash
# Check YAML structure and action schemas without executing
python3 src/cli.py validate-pipeline --pipeline pipelines/example_pipeline.yaml
```

### List Configured Networks
```bash
# Display formatted table of all available blockchain networks
python3 src/cli.py list-networks
```

### Scaffold a New Pipeline
```bash
# Generate a new pipeline template
python3 src/cli.py init --output pipelines/production.yaml
```

---

## Action Reference

### `actions/compile@v1`
Compiles smart contracts.
- `tool`: `hardhat` (default) or `foundry`.
- `contracts_dir`: (Optional) Path to contracts directory.

### `actions/test@v1`
Executes contract unit tests.
- `tool`: `hardhat` (default) or `foundry`.
- `network`: (Optional) Network for forked testing.
- `test_files`: (Optional) List or single test file path.

### `actions/security_scan@v1`
Runs security auditing and linting.
- `tool`: `solhint` (default) or `slither`.
- `pattern`: (Optional) Glob pattern for Solhint (default: `**/*.sol`).
- `target`: (Optional) Target directory for Slither (default: `.`).

### `actions/deploy@v1`
Deploys contracts to a specified network.
- `network`: Target network name (matching `config/networks.json`).
- `contract`: Solidity contract name.
- `args`: Array of constructor arguments (supports any JSON serializable types).
- `script`: (Optional) Custom deployment script (default: `scripts/deploy.js`).

### `actions/smoke_test@v1`
Executes on-chain getter calls against a deployed contract and asserts state.
- `network`: Target network name.
- `contract`: Contract name.
- `address`: Contract address (passed directly or dynamic `${{ jobs.<DeployJob>.output.address }}`).
- `calls`: Array of method calls with optional expected return values:
  ```yaml
  calls:
    - method: greet
      args: []
      expected: "Hello from Web3 DevOps!"
  ```

### `actions/verify@v1`
Verifies contract source code on block explorers (Etherscan, Arbiscan, Basescan, etc.).
- `network`: Target network name.
- `contract`: Contract name.
- `address`: Contract address (typically passed via dynamic parameter `${{ jobs.<DeployJob>.output.address }}`).
- `args`: (Optional) Constructor arguments matching deployment.

### `actions/export_abi@v1`
Extracts and packages clean contract ABIs, deployment metadata, and TypeScript typings.
- `contract`: Solidity contract name.
- `destination`: (Optional) Output directory (default: `exports`).
- `address`: (Optional) Deployed contract address (passed directly or dynamic `${{ jobs.<DeployJob>.output.address }}`).
- `network`: (Optional) Target network name.
- `typescript`: (Optional) Generate typed TypeScript definitions with `as const` for Viem / Wagmi (default: `true`).
- `include_bytecode`: (Optional) Include compiled bytecode in JSON package (default: `false`).

### `actions/gas_check@v1`
Estimates contract deployment gas and enforces CI gas budgets.
- `contract`: Solidity contract name.
- `network`: (Optional) Target network (default: `localhost`).
- `max_gas_limit`: (Optional) Maximum allowable gas units (fails if exceeded).
- `args`: (Optional) Constructor arguments matching deployment.

### `actions/safe_stage@v1`
Stages contract deployments or calls into a Gnosis Safe Transaction Batch JSON format for multi-sig signing.
- `contract`: Solidity contract name.
- `network`: Target network.
- `safe_address`: Target Safe multi-sig address.
- `output`: (Optional) Output file path (default: `exports/safe-batch.json`).
- `transactions`: (Optional) Custom transaction payload array.

### `actions/proxy@v1`
Manages ERC-1967 and UUPS upgradeable contract deployments and implementation upgrades.
- `contract`: Implementation contract name.
- `network`: (Optional) Target network (default: `localhost`).
- `operation`: `'deploy'` (default) or `'upgrade'`.
- `proxy_address`: (Required for `upgrade`) Address of the existing proxy contract.
- `init_args`: (Optional) Array of arguments for initialization.

### `actions/notify@v1`
Dispatches formatted deployment alerts to Discord, Slack, or generic webhooks.
- `webhook_url`: (Optional) Webhook URL (or set via `DISCORD_WEBHOOK_URL` / `SLACK_WEBHOOK_URL` in `.env`).
- `channel`: (Optional) `'discord'`, `'slack'`, or auto-detected.
- `title`: Alert title.
- `contract`: Deployed contract name.
- `network`: Network name (automatically generates explorer link if available).
- `address`: Deployed address.

---

## Example Pipeline Definition

```yaml
name: Example Web3 Pipeline

env:
  NODE_ENV: production

jobs:
  - name: Security Scan
    uses: actions/security_scan@v1
    continue-on-error: true
    with:
      tool: solhint
      pattern: "**/*.sol"

  - name: Compile Contracts
    uses: actions/compile@v1
    with:
      tool: hardhat

  - name: Run Tests
    uses: actions/test@v1
    with:
      tool: hardhat

  - name: Deploy to Localhost
    uses: actions/deploy@v1
    with:
      network: localhost
      contract: MyContract
      args: ["Hello Web3 DevOps!"]

  - name: Smoke Test Live Contract
    uses: actions/smoke_test@v1
    with:
      network: localhost
      contract: MyContract
      address: ${{ jobs.Deploy to Localhost.output.address }}
      calls:
        - method: greet
          expected: "Hello Web3 DevOps!"

  - name: Verify Contract
    uses: actions/verify@v1
    with:
      network: localhost
      contract: MyContract
      address: ${{ jobs.Deploy to Localhost.output.address }}
      args: ["Hello Web3 DevOps!"]

  - name: Export ABI & TypeScript Types
    uses: actions/export_abi@v1
    with:
      contract: MyContract
      destination: exports
      network: localhost
      address: ${{ jobs.Deploy to Localhost.output.address }}
      typescript: true

  - name: Send Notification
    uses: actions/notify@v1
    continue-on-error: true
    with:
      title: "🚀 Contract Deployed Successfully"
      network: localhost
      contract: MyContract
      address: ${{ jobs.Deploy to Localhost.output.address }}
```

---

## Continuous Integration (GitHub Actions)

A pre-configured CI/CD workflow is included at `.github/workflows/web3-devops.yml`:

- **Automated PR Checks**: Validates pipeline schemas, runs Solhint security audits, and executes the unit test suite on every pull request.
- **Contract & Toolkit Tests**: Runs both contract tests (`hardhat test`) and toolkit tests (`pytest`).
- **End-to-End Pipeline Execution**: Spins up a local test node in CI, runs the complete deployment pipeline, and uploads deployment manifests and generated ABIs as workflow artifacts.

---

## Running the Test Suite

Execute the unit test suite via `pytest`:
```bash
pytest -v
```

All 62 unit tests pass:
```
============================== 62 passed in 0.18s ==============================
```

---

## Project Structure

```
web3-devops-toolkit/
├── .env.example             # Template for environment variables
├── .gitignore               # Git ignore rules
├── pyproject.toml           # Package configuration & CLI script registration
├── conftest.py              # Pytest setup and path injection
├── pipelines/               # Pipeline YAML workflow definitions
│   └── example_pipeline.yaml
├── config/                  # Network RPC and chain configs
│   └── networks.json
├── contracts/               # Smart contracts and Hardhat/Foundry workspace
│   ├── contracts/
│   │   └── MyContract.sol
│   ├── test/
│   │   └── MyContract.test.js
│   ├── package.json
│   └── hardhat.config.js    # Dynamically loads config/networks.json
├── scripts/                 # Universal deployment scripts
│   └── deploy.js
├── src/                     # Core application source
│   ├── __init__.py
│   ├── cli.py               # CLI interface (run, validate, list-networks, init)
│   ├── pipeline_runner.py   # Workflow engine, parameter resolver, manifest exporter
│   └── actions/             # Action definitions
│       ├── __init__.py
│       ├── common.py        # Path resolution & environment utilities
│       ├── compile.py       # Hardhat & Foundry compilation
│       ├── test.py          # Hardhat & Foundry contract test runner
│       ├── security_scan.py # Solhint & Slither static analysis
│       ├── deploy.py        # Universal multi-network contract deployer
│       └── verify.py        # Block explorer verification with args
├── tests/                   # Comprehensive unit test suite (36 tests)
│   ├── test_pipeline_runner.py
│   └── actions/
│       ├── test_compile.py
│       ├── test_deploy.py
│       ├── test_security_scan.py
│       ├── test_test.py
│       └── test_verify.py
├── requirements.txt         # Python dependencies
└── start.sh                 # Self-contained setup & bootstrap script
```

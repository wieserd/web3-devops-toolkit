# Web3 DevOps Toolkit

A streamlined, modular system for building, testing, and deploying smart contracts across multiple blockchain networks.

## Getting Started

To get started with the Web3 DevOps Toolkit, simply run the `start.sh` script from the project root:

```bash
./start.sh
```

This script will:
1.  Check for necessary dependencies (Python 3 and npm).
2.  Install Python project dependencies.
3.  Install Node.js dependencies for the smart contracts.
4.  Execute the example deployment pipeline.

## Running Tests

To run the unit tests, navigate to the root of the project and execute:
```bash
pytest
```

## Project Structure

```
web3-devops-toolkit/
├── .env.example             # Template for environment variables
├── conftest.py             # Pytest configuration for test discovery and path setup
├── pipelines/              # Directory for pipeline YAML definitions
│   └── example_pipeline.yaml
├── config/                 # Network configurations
│   └── networks.json
├── contracts/              # Smart contract source code and Hardhat project
│   ├── MyContract.sol
│   ├── package.json
│   └── hardhat.config.js
├── scripts/                # Helper scripts for deployment, etc.
│   └── deploy.js
├── src/                    # Core CLI application source code
│   ├── __init__.py         # Makes src a Python package
│   ├── cli.py              # Main CLI entry point
│   ├── pipeline_runner.py  # Handles pipeline loading and execution logic
│   └── actions/            # Modular action functions
│       ├── __init__.py     # Makes actions a Python package
│       ├── compile.py      # Logic for compiling smart contracts
│       ├── deploy.py       # Logic for deploying smart contracts
│       └── verify.py       # Logic for verifying smart contracts
├── tests/                  # Unit and integration tests
│   ├── test_pipeline_runner.py
│   └── actions/
│       ├── test_compile.py
│       ├── test_deploy.py
│       └── test_verify.py
├── requirements.txt        # Python dependencies
└── start.sh                # One-shot setup and run script
```

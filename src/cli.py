#!/usr/bin/env python3

import argparse
import os
import sys
import json
import yaml
from dotenv import load_dotenv

if __name__ == "__main__" and __package__ is None:
    # Allow running directly as a script (e.g., ./src/cli.py or python3 src/cli.py)
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.pipeline_runner import PipelineRunner
else:
    from .pipeline_runner import PipelineRunner

SAMPLE_PIPELINE_TEMPLATE = """name: New Web3 Deployment Pipeline

env:
  NODE_ENV: production

jobs:
  - name: Security Scan
    uses: actions/security_scan@v1
    continue-on-error: true
    with:
      tool: solhint
      pattern: "**/*.sol"

  - name: Compile Smart Contracts
    uses: actions/compile@v1
    with:
      tool: hardhat

  - name: Run Test Suite
    uses: actions/test@v1
    with:
      tool: hardhat

  - name: Deploy Contract
    uses: actions/deploy@v1
    with:
      network: localhost
      contract: MyContract
      args: ["Hello Web3!"]

  - name: Verify Contract
    uses: actions/verify@v1
    with:
      network: localhost
      contract: MyContract
      address: ${{ jobs.Deploy Contract.output.address }}

  - name: Export ABI and Types
    uses: actions/export_abi@v1
    with:
      contract: MyContract
      destination: exports
      network: localhost
      address: ${{ jobs.Deploy Contract.output.address }}
      typescript: true
"""

def handle_run_pipeline(args):
    if not args.pipeline:
        print("Error: --pipeline argument is required for 'run-pipeline'.")
        sys.exit(1)

    pipeline_abs_path = os.path.abspath(args.pipeline)

    try:
        runner = PipelineRunner(
            pipeline_abs_path,
            manifest_path=args.manifest,
            dry_run=args.dry_run
        )
        success = runner.run()
        if not success:
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML pipeline: {e}")
        sys.exit(1)

def handle_validate_pipeline(args):
    if not args.pipeline:
        print("Error: --pipeline argument is required for 'validate-pipeline'.")
        sys.exit(1)

    pipeline_abs_path = os.path.abspath(args.pipeline)
    try:
        runner = PipelineRunner(pipeline_abs_path)
        is_valid, issues = runner.validate()
        if is_valid:
            print(f"✅ Pipeline '{args.pipeline}' is valid.")
        else:
            print(f"❌ Pipeline '{args.pipeline}' has validation errors:")
            for issue in issues:
                print(f"   - {issue}")
            sys.exit(1)
    except Exception as e:
        print(f"Error validating pipeline: {e}")
        sys.exit(1)

def handle_list_networks(args):
    # Determine config path relative to script or cwd
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(root_dir, 'config', 'networks.json')

    if not os.path.exists(config_path):
        print(f"Error: Networks configuration not found at {config_path}")
        sys.exit(1)

    with open(config_path, 'r') as f:
        networks = json.load(f)

    print("\nConfigured Blockchain Networks:")
    print("-" * 65)
    print(f"{'Network':<15} | {'Chain ID':<10} | {'RPC URL'}")
    print("-" * 65)
    for name, details in networks.items():
        chain_id = str(details.get('chain_id', 'N/A'))
        rpc_url = details.get('rpc_url', 'N/A')
        print(f"{name:<15} | {chain_id:<10} | {rpc_url}")
    print("-" * 65)

def handle_init_pipeline(args):
    target_path = args.output or "pipelines/new_pipeline.yaml"
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    if os.path.exists(target_path) and not args.force:
        print(f"Error: File '{target_path}' already exists. Use --force to overwrite.")
        sys.exit(1)
    with open(target_path, 'w') as f:
        f.write(SAMPLE_PIPELINE_TEMPLATE)
    print(f"✅ Generated new pipeline scaffold at '{target_path}'.")

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Web3 DevOps Toolkit CLI - Automate contract building, testing, deploying, and verifying."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: run-pipeline
    run_parser = subparsers.add_parser("run-pipeline", help="Execute a YAML pipeline workflow")
    run_parser.add_argument("--pipeline", required=True, help="Path to pipeline YAML file")
    run_parser.add_argument("--dry-run", action="store_true", help="Parse and validate without running actions")
    run_parser.add_argument("--manifest", help="Optional path to output deployment manifest JSON")

    # Command: validate-pipeline
    val_parser = subparsers.add_parser("validate-pipeline", help="Validate pipeline syntax and schema")
    val_parser.add_argument("--pipeline", required=True, help="Path to pipeline YAML file")

    # Command: list-networks
    subparsers.add_parser("list-networks", help="List all configured blockchain networks")

    # Command: init
    init_parser = subparsers.add_parser("init", help="Scaffold a new pipeline definition")
    init_parser.add_argument("--output", default="pipelines/new_pipeline.yaml", help="Destination file path")
    init_parser.add_argument("--force", action="store_true", help="Overwrite destination if it already exists")

    # Backward compatibility: if no subcommand matched but positional arg passed
    args = parser.parse_args()

    if args.command == "run-pipeline":
        handle_run_pipeline(args)
    elif args.command == "validate-pipeline":
        handle_validate_pipeline(args)
    elif args.command == "list-networks":
        handle_list_networks(args)
    elif args.command == "init":
        handle_init_pipeline(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()

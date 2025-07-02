#!/usr/bin/env python3

import argparse
import os
import sys
import yaml
from dotenv import load_dotenv

from .pipeline_runner import PipelineRunner

def main():
    load_dotenv() # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Web3 DevOps Toolkit CLI")
    parser.add_argument("command", help="Command to execute (e.g., 'run-pipeline')")
    parser.add_argument("--pipeline", help="Path to the pipeline YAML file")

    args = parser.parse_args()

    if args.command == "run-pipeline":
        if not args.pipeline:
            print("Error: --pipeline argument is required for 'run-pipeline' command.")
            sys.exit(1)
        
        # Ensure the pipeline path is absolute
        pipeline_abs_path = os.path.abspath(args.pipeline)

        try:
            runner = PipelineRunner(pipeline_abs_path)
            runner.run()
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML pipeline: {e}")
            sys.exit(1)

    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    main()

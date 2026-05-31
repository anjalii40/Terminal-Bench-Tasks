#!/bin/bash
set -e

# Create the verifier output directory expected by Harbor.
mkdir -p /logs/verifier

# Run the oracle patch, then execute the strict pytest suite.
if bash /solution/solve.sh && python3 -m pytest -q /tests/test_outputs.py; then
  printf '1\n' > /logs/verifier/reward.txt
else
  printf '0\n' > /logs/verifier/reward.txt
  exit 1
fi

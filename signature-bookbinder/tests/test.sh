#!/bin/sh
set -eu

# Verifier entrypoint: run the strict pytest suite and emit Harbor reward.txt.
if python -m pytest -q /tests/test_outputs.py; then
  printf '1.0\n' > /logs/verifier/reward.txt
else
  status=$?
  printf '0.0\n' > /logs/verifier/reward.txt
  exit "$status"
fi

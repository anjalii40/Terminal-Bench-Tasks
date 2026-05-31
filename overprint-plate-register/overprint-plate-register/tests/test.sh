#!/bin/sh
set -eu

reward_dir=/logs/verifier
if ! mkdir -p "$reward_dir" 2>/dev/null; then
  reward_dir=logs/verifier
  mkdir -p "$reward_dir"
fi

test_file=/tests/test_outputs.py
if [ ! -f "$test_file" ]; then
  test_file=tests/test_outputs.py
fi

python_bin=python
if ! command -v "$python_bin" >/dev/null 2>&1; then
  python_bin=python3
fi

if "$python_bin" -m pytest -q "$test_file"; then
  printf '1\n' > "$reward_dir/reward.txt"
else
  status=$?
  printf '0\n' > "$reward_dir/reward.txt"
  exit "$status"
fi

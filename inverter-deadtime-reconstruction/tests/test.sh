#!/bin/sh
set -eu

mkdir -p /logs/verifier

# Verifier entrypoint for the repaired inverter program.
# It compiles the candidate source, runs the strict visible and hidden fixture suite,
# checks exact timeline/report outputs for dead-time persistence behavior, and writes
# Harbor reward.txt from the pytest result. Verifier-side fixtures live under
# /tests/fixtures and are intentionally not copied into /environment.
# 
# Specific behaviors tested include:
# 1. Correct dead-time window restarts.
# 2. Delayed commitment when current sustains the previously established command's diode family.
# 3. Z-state transitions where no diode family is sustained.
# 4. Correct derivation of line voltages from node levels.
# Failure modes tested include naive immediate commitment after dead-time expiry,
# and incorrect persistence state capture (e.g. tracking last_realized_node instead of established command).
if python3 -m pytest -q /tests/test_outputs.py --junitxml=/logs/verifier/results.xml; then
    printf '1.0
' > /logs/verifier/reward.txt
else
    status=$?
    printf '0.0
' > /logs/verifier/reward.txt
    exit "$status"
fi

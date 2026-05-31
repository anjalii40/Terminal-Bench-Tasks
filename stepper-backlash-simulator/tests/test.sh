#!/bin/sh
set -eu

mkdir -p /logs/verifier

# Verifier entrypoint for the repaired stepper motor program.
# It compiles the candidate source, runs the strict visible and hidden fixture suite,
# checks exact timeline/report outputs for physical persistence behavior, and writes
# Harbor reward.txt from the pytest result. Verifier-side fixtures live under
# /tests/fixtures and are intentionally not copied into /environment.
# 
# Specific behaviors tested include:
# 1. Correct un-interruptible slew execution.
# 2. Correct backlash delay application upon direction reversal.
# 3. Second-order reversion: instantly aborting backlash if the target direction flips
#    back to match the physically engaged gear direction.
# Failure modes tested include naive immediate commitment of target variables that overwrites
# the historical mechanical engagement direction, causing the abort trap to fail.

if python3 -m pytest -q /tests/test_outputs.py --junitxml=/logs/verifier/results.xml; then
    printf '1.0\n' > /logs/verifier/reward.txt
else
    status=$?
    printf '0.0\n' > /logs/verifier/reward.txt
    exit "$status"
fi

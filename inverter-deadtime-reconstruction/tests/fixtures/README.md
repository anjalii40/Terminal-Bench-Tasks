# Verifier Fixture Inventory

This directory contains repository-backed verifier assets used by `tests/test_outputs.py`.

- Hidden case inputs live under `tests/fixtures/<case>/input/`.
- Hidden expected outputs live under `tests/fixtures/<case>/expected_timeline.tsv` and `expected_report.json`.
- These files are verifier-side assets and are intentionally not copied into `/environment` by `environment/Dockerfile`.
- The candidate program only receives `/environment/inverter.cpp` and `/environment/sample_job/` inside the runtime image.

import json
import subprocess
from pathlib import Path

import pytest

CHECKPOINT_PATH = Path("/app/checkpoint.json")
REPLICA_PATHS = [
    Path("/app/replica_a.jsonl"),
    Path("/app/replica_b.jsonl"),
    Path("/app/replica_c.jsonl"),
]
SCRIPT_PATH = Path("/app/reconcile.py")
LEDGER_PATH = Path("/app/state/ledger.json")
REPORT_PATH = Path("/app/output/reconciliation_report.json")

ORIGINAL_CHECKPOINT = CHECKPOINT_PATH.read_text(encoding="utf-8")
ORIGINAL_REPLICAS = {
    path: path.read_text(encoding="utf-8")
    for path in REPLICA_PATHS
}

EXPECTED_SEED_LEDGER = {
    "balances": {
        "acct-amber": 128,
        "acct-cinder": 39,
        "acct-dusk": 70,
    },
    "applied_ops": [
        "op-100",
        "op-101",
        "op-102",
        "op-200",
        "op-201",
        "op-204",
        "op-208",
        "op-210",
    ],
}

EXPECTED_SEED_REPORT = {
    "accepted": [
        "op-100",
        "op-200",
        "op-201",
        "op-204",
        "op-208",
        "op-210",
    ],
    "rejected": [
        "op-202",
        "op-203",
        "op-207",
    ],
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_script():
    return subprocess.run(
        ["python3", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
    )


@pytest.fixture(autouse=True)
def restore_inputs():
    """Restore the task inputs before each test case runs."""
    CHECKPOINT_PATH.write_text(ORIGINAL_CHECKPOINT, encoding="utf-8")
    for path, content in ORIGINAL_REPLICAS.items():
        path.write_text(content, encoding="utf-8")
    LEDGER_PATH.unlink(missing_ok=True)
    REPORT_PATH.unlink(missing_ok=True)


def test_seeded_outputs_match_exact_expected_values():
    """Validate the seeded ledger and report against the fixed baseline."""
    result = run_script()
    assert result.returncode == 0, result.stderr
    ledger = load_json(LEDGER_PATH)
    report = load_json(REPORT_PATH)
    assert ledger == EXPECTED_SEED_LEDGER
    assert report == EXPECTED_SEED_REPORT


def test_output_files_exist_and_are_valid_json():
    """Ensure the script creates both required output files as valid JSON."""
    run_script()
    assert LEDGER_PATH.exists(), "/app/state/ledger.json was not created"
    assert REPORT_PATH.exists(), "/app/output/reconciliation_report.json was not created"
    assert isinstance(load_json(LEDGER_PATH), dict)
    assert isinstance(load_json(REPORT_PATH), dict)


def test_output_schema_is_exact():
    """Check that the top-level output schema and value container types are exact."""
    run_script()
    ledger = load_json(LEDGER_PATH)
    report = load_json(REPORT_PATH)
    assert sorted(ledger.keys()) == ["applied_ops", "balances"]
    assert sorted(report.keys()) == ["accepted", "rejected"]
    assert isinstance(ledger["balances"], dict)
    assert isinstance(ledger["applied_ops"], list)
    assert isinstance(report["accepted"], list)
    assert isinstance(report["rejected"], list)
    assert all(isinstance(value, int) for value in ledger["balances"].values())


def test_single_replica_and_conflicting_operations_are_rejected():
    """Reject operations that lack quorum or appear with conflicting payloads."""
    run_script()
    report = load_json(REPORT_PATH)
    assert report["rejected"] == ["op-202", "op-203", "op-207"]
    assert "op-202" not in report["accepted"]
    assert "op-203" not in report["accepted"]
    assert "op-207" not in report["accepted"]


def test_checkpointed_operations_are_not_replayed():
    """Confirm checkpointed operations may be accepted without changing balances again."""
    run_script()
    ledger = load_json(LEDGER_PATH)
    report = load_json(REPORT_PATH)
    assert "op-100" in report["accepted"]
    assert ledger["balances"]["acct-amber"] == 128


def test_sorted_lists_are_emitted_in_both_outputs():
    """Require deterministic sorted lists in both output files."""
    run_script()
    ledger = load_json(LEDGER_PATH)
    report = load_json(REPORT_PATH)
    assert ledger["applied_ops"] == sorted(ledger["applied_ops"])
    assert report["accepted"] == sorted(report["accepted"])
    assert report["rejected"] == sorted(report["rejected"])


def test_rerun_is_idempotent():
    """Verify that rerunning the repaired script produces identical outputs."""
    first = run_script()
    assert first.returncode == 0, first.stderr
    first_ledger = load_json(LEDGER_PATH)
    first_report = load_json(REPORT_PATH)
    second = run_script()
    assert second.returncode == 0, second.stderr
    assert load_json(LEDGER_PATH) == first_ledger
    assert load_json(REPORT_PATH) == first_report


def test_replica_line_order_does_not_change_result():
    """Ensure replica line ordering does not affect the canonical outputs."""
    reversed_lines = list(reversed(ORIGINAL_REPLICAS[REPLICA_PATHS[1]].splitlines()))
    REPLICA_PATHS[1].write_text("\n".join(reversed_lines) + "\n", encoding="utf-8")
    result = run_script()
    assert result.returncode == 0, result.stderr
    assert load_json(LEDGER_PATH) == EXPECTED_SEED_LEDGER
    assert load_json(REPORT_PATH) == EXPECTED_SEED_REPORT


def test_quorum_mutation_changes_balances_without_hardcoding():
    """Check that adding a new quorum-confirmed operation changes the outputs."""
    appended = {
        "op_id": "op-250",
        "kind": "credit",
        "account": "acct-cinder",
        "amount": 4,
    }
    line = json.dumps(appended, separators=(",", ":")) + "\n"
    REPLICA_PATHS[0].write_text(ORIGINAL_REPLICAS[REPLICA_PATHS[0]] + line, encoding="utf-8")
    REPLICA_PATHS[2].write_text(ORIGINAL_REPLICAS[REPLICA_PATHS[2]] + line, encoding="utf-8")
    result = run_script()
    assert result.returncode == 0, result.stderr
    ledger = load_json(LEDGER_PATH)
    report = load_json(REPORT_PATH)
    assert ledger["balances"]["acct-cinder"] == 43
    assert ledger["balances"]["acct-amber"] == 128
    assert ledger["balances"]["acct-dusk"] == 70
    assert "op-250" in report["accepted"]
    assert "op-250" in ledger["applied_ops"]
    assert "op-250" not in report["rejected"]

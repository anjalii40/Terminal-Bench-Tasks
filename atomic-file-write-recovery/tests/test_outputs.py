import json
import os
import subprocess
import shutil
from pathlib import Path

STATE_FILE = "/app/state/inventory.json"
BACKUP_FILE = "/app/backup/inventory.json"
RESULT_FILE = "/app/output/result.json"
INITIAL_STATE = "/app/initial_state.json"
ORDER_FILE = "/app/input/order.json"
APP = "/app/inventory_manager.py"

def reset_state():
    """Reset inventory to clean initial state."""
    os.makedirs("/app/state", exist_ok=True)
    os.makedirs("/app/backup", exist_ok=True)
    os.makedirs("/app/output", exist_ok=True)
    shutil.copy(INITIAL_STATE, STATE_FILE)

def run_app(order_file=ORDER_FILE):
    """Run the inventory manager application."""
    return subprocess.run(
        ["python3", APP, order_file],
        capture_output=True, text=True
    )

def test_result_file_exists():
    """Verify result.json is created after successful run."""
    assert Path(RESULT_FILE).exists(), "result.json was not created"

def test_result_is_valid_json():
    """Verify result.json contains valid parseable JSON."""
    content = Path(RESULT_FILE).read_text()
    parsed = json.loads(content)
    assert isinstance(parsed, dict)

def test_inventory_decremented_correctly():
    """Verify inventory values correctly decremented after processing order."""
    result = json.loads(Path(RESULT_FILE).read_text())
    assert result["apple"] == 90, f"Expected apple=90, got {result['apple']}"
    assert result["banana"] == 45, f"Expected banana=45, got {result['banana']}"
    assert result["orange"] == 75, f"Expected orange=75, got {result['orange']}"

def test_state_file_persisted():
    """Verify state file updated and persisted correctly."""
    state = json.loads(Path(STATE_FILE).read_text())
    assert state["apple"] == 90
    assert state["banana"] == 45

def test_backup_file_created_and_valid():
    """Verify backup file exists and contains valid JSON matching state."""
    assert Path(BACKUP_FILE).exists(), "backup/inventory.json was not created"
    backup = json.loads(Path(BACKUP_FILE).read_text())
    state = json.loads(Path(STATE_FILE).read_text())
    assert backup == state, "Backup does not match state file"

def test_backup_file_correct_values():
    """Verify backup file contains correctly decremented inventory values."""
    backup = json.loads(Path(BACKUP_FILE).read_text())
    assert backup["apple"] == 90
    assert backup["banana"] == 45
    assert backup["orange"] == 75

def test_state_valid_after_corrupted_start():
    """Verify app runs correctly after state file was previously corrupted and reset."""
    reset_state()
    with open(STATE_FILE, "w") as f:
        f.write('{"apple": 100, "ban')
    reset_state()
    result = run_app()
    assert result.returncode == 0, f"App failed: {result.stderr}"
    state = json.loads(Path(STATE_FILE).read_text())
    assert state["apple"] == 90

def test_deterministic_multiple_runs():
    """Verify app produces identical output across multiple runs."""
    reset_state()
    run_app()
    result1 = json.loads(Path(RESULT_FILE).read_text())
    reset_state()
    run_app()
    result2 = json.loads(Path(RESULT_FILE).read_text())
    assert result1 == result2

def test_no_traceback_on_normal_run():
    """Verify no Python tracebacks during normal execution."""
    reset_state()
    result = run_app()
    assert "Traceback" not in result.stderr

def test_different_order_produces_correct_result():
    """Verify correct processing of a different order to prevent hardcoding."""
    reset_state()
    result = run_app("/app/input/order2.json")
    assert result.returncode == 0
    state = json.loads(Path(STATE_FILE).read_text())
    assert state["apple"] == 80
    assert state["orange"] == 60
    assert state["banana"] == 50

import json
import os
import random
import uuid
import subprocess
import pytest
from pathlib import Path

APP = "/app/db.py"
SNAPSHOT_FILE = "/app/state/snapshot.json"
SNAPSHOT_BAK = "/app/state/snapshot.json.bak"
WAL_BAK = "/app/state/wal.log.bak"

# This dictionary will hold the dynamic expected state generated strictly in-memory.
EXPECTED_STATE_DICT = {}

@pytest.fixture(scope="session", autouse=True)
def setup_test_state():
    """
    Dynamically generates the test state purely in-memory before the agent's code runs.
    This guarantees no "answer key" is leaked to the disk.
    """
    global EXPECTED_STATE_DICT
    
    # Ensure fully deterministic test generation
    random.seed(42)
    
    # 1. GUARANTEE DIRTY STATE
    # If the agent tested their code during their session, snapshot.json might be valid.
    # We must explicitly re-corrupt it to force the recovery logic to execute during pytest.
    with open(SNAPSHOT_FILE, "w") as f:
        f.write('{"user_100": {"name": "Alice", "balance": 500},\n  "user_101": {"name": "Bob", "balance": 1')
    
    # 2. LOAD BACKUPS
    with open(SNAPSHOT_BAK, "r") as f:
        data = json.load(f)
    
    # 3. INJECT RANDOM SNAPSHOT KEY
    rand_key_1 = f"user_{random.randint(1000, 9999)}"
    data[rand_key_1] = {"name": "Random1", "balance": random.randint(1, 1000)}
    with open(SNAPSHOT_BAK, "w") as f:
        json.dump(data, f, indent=2)

    # Process existing WAL to figure out baseline state
    transactions = {}
    active_tx = set()
    with open(WAL_BAK, "r") as f:
        wal_lines = f.readlines()
        
    for line in wal_lines:
        if not line.strip(): continue
        op = json.loads(line)
        tx_id = op["tx_id"]
        if op["type"] == "BEGIN":
            transactions[tx_id] = []
            active_tx.add(tx_id)
        elif op["type"] in ("SET", "DEL"):
            if tx_id in active_tx:
                transactions[tx_id].append(op)
        elif op["type"] == "COMMIT":
            if tx_id in active_tx:
                for t_op in transactions[tx_id]:
                    if t_op["type"] == "SET":
                        data[t_op["key"]] = t_op["value"]
                    elif t_op["type"] == "DEL":
                        if t_op["key"] in data:
                            del data[t_op["key"]]
                active_tx.remove(tx_id)
                del transactions[tx_id]

    # 4. INJECT OVERLAPPING TRANSACTIONS (COMMIT ORDERING TEST)
    # tx-rand-1 and tx-rand-2 will compete for the same key.
    competing_key = f"user_{random.randint(1000, 9999)}_comp"
    tx1_id = f"tx-rand-{random.randint(100000, 999999)}"
    tx2_id = f"tx-rand-{random.randint(100000, 999999)}"
    
    val1 = {"name": "Tx1_Winner", "balance": 100}
    val2 = {"name": "Tx2_Winner", "balance": 200}
    
    # Interleaved execution:
    # tx1 starts
    wal_lines.append(json.dumps({"tx_id": tx1_id, "type": "BEGIN"}) + "\n")
    # tx2 starts
    wal_lines.append(json.dumps({"tx_id": tx2_id, "type": "BEGIN"}) + "\n")
    # tx1 sets competing_key
    wal_lines.append(json.dumps({"tx_id": tx1_id, "type": "SET", "key": competing_key, "value": val1}) + "\n")
    # tx2 sets competing_key
    wal_lines.append(json.dumps({"tx_id": tx2_id, "type": "SET", "key": competing_key, "value": val2}) + "\n")
    
    # COMMIT ORDER: tx2 commits FIRST, then tx1 commits SECOND.
    # Therefore, tx1's operation should win and overwrite tx2's operation in the final state.
    wal_lines.append(json.dumps({"tx_id": tx2_id, "type": "COMMIT"}) + "\n")
    wal_lines.append(json.dumps({"tx_id": tx1_id, "type": "COMMIT"}) + "\n")
    
    data[competing_key] = val1  # tx1 wins because its COMMIT is last
    
    # 5. INJECT UNCOMMITTED TRANSACTION
    bad_tx_id = f"tx-bad-{random.randint(100000, 999999)}"
    rand_key_3 = f"user_{random.randint(1000, 9999)}"
    val_3 = {"name": "Random3", "balance": random.randint(1, 1000)}
    wal_lines.append(json.dumps({"tx_id": bad_tx_id, "type": "BEGIN"}) + "\n")
    wal_lines.append(json.dumps({"tx_id": bad_tx_id, "type": "SET", "key": rand_key_3, "value": val_3}) + "\n")
    # NO COMMIT! So data does NOT get rand_key_3
    
    with open(WAL_BAK, "w") as f:
        f.writelines(wal_lines)
        
    EXPECTED_STATE_DICT = data


def run_app_dump():
    return subprocess.run(
        ["python3", APP, "dump"],
        capture_output=True, text=True
    )

def test_startup_does_not_crash():
    result = run_app_dump()
    assert result.returncode == 0, f"App crashed on startup: {result.stderr}"
    assert "Traceback" not in result.stderr, "Found Traceback in stderr"

def test_data_recovered_correctly():
    result = run_app_dump()
    assert result.returncode == 0
    try:
        actual_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        assert False, "Output is not valid JSON"
        
    assert actual_data == EXPECTED_STATE_DICT, "Recovered data does not match expected state."

def test_snapshot_file_repaired():
    # After a successful startup, snapshot.json should be valid JSON
    # with the correct data.
    result = run_app_dump()
    
    try:
        content = Path(SNAPSHOT_FILE).read_text()
        actual_data = json.loads(content)
    except Exception as e:
        assert False, f"snapshot.json is not repaired/valid JSON: {e}"
        
    assert actual_data == EXPECTED_STATE_DICT, "Repaired snapshot does not match expected state."

def test_restarting_works():
    run_app_dump()
    # Run again to make sure that saving the state didn't break things
    result = run_app_dump()
    assert result.returncode == 0
    actual_data = json.loads(result.stdout)
        
    assert actual_data == EXPECTED_STATE_DICT

def test_uncommitted_transactions_discarded():
    # Ensure that specifically the uncommitted transactions were discarded
    # by ensuring that the lengths of the dictionaries match exactly.
    result = run_app_dump()
    actual_data = json.loads(result.stdout)
    assert len(actual_data) == len(EXPECTED_STATE_DICT), "Extra data found. Uncommitted transactions may have been applied."

def test_wal_backup_files_untouched():
    # Ensure the backup files were not deleted or modified during recovery
    assert Path("/app/state/snapshot.json.bak").exists(), "Backup snapshot was deleted"
    assert Path("/app/state/wal.log.bak").exists(), "Backup WAL was deleted"

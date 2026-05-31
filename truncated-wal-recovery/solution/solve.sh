#!/bin/bash
cat << 'EOF' > /app/db.py
import json
import os
import sys

STATE_DIR = "/app/state"
SNAPSHOT_FILE = os.path.join(STATE_DIR, "snapshot.json")
SNAPSHOT_BAK = os.path.join(STATE_DIR, "snapshot.json.bak")
WAL_FILE = os.path.join(STATE_DIR, "wal.log")
WAL_BAK = os.path.join(STATE_DIR, "wal.log.bak")

class KVStore:
    def __init__(self):
        self.data = {}

    def startup(self):
        try:
            with open(SNAPSHOT_FILE, "r") as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Recovery process
            if os.path.exists(SNAPSHOT_BAK):
                with open(SNAPSHOT_BAK, "r") as f:
                    self.data = json.load(f)
            
            if os.path.exists(WAL_BAK):
                self.apply_wal(WAL_BAK)
            
            # Save repaired state
            self.save_snapshot()

    def save_snapshot(self):
        with open(SNAPSHOT_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def apply_wal(self, filepath):
        if not os.path.exists(filepath):
            return
            
        transactions = {}
        active_tx = set()
        
        with open(filepath, "r") as f:
            for line in f:
                if not line.strip():
                    continue
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
                        # Apply to state
                        for t_op in transactions[tx_id]:
                            if t_op["type"] == "SET":
                                self.data[t_op["key"]] = t_op["value"]
                            elif t_op["type"] == "DEL":
                                if t_op["key"] in self.data:
                                    del self.data[t_op["key"]]
                        active_tx.remove(tx_id)
                        del transactions[tx_id]

    def get(self, key):
        return self.data.get(key)

    def dump(self):
        return json.dumps(self.data, indent=2)

if __name__ == "__main__":
    db = KVStore()
    db.startup()
    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        print(db.dump())
EOF

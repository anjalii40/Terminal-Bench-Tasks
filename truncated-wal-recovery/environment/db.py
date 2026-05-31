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
        # BUG: Blindly loads corrupted snapshot without fallback
        with open(SNAPSHOT_FILE, "r") as f:
            self.data = json.load(f)

    def apply_wal(self, filepath):
        if not os.path.exists(filepath):
            return
        with open(filepath, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                op = json.loads(line)
                # BUG: Blindly applies operations without respecting transactions!
                if op.get("type") == "SET":
                    self.data[op["key"]] = op["value"]
                elif op.get("type") == "DEL":
                    if op["key"] in self.data:
                        del self.data[op["key"]]

    def get(self, key):
        return self.data.get(key)

    def dump(self):
        return json.dumps(self.data, indent=2)

if __name__ == "__main__":
    db = KVStore()
    db.startup()
    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        print(db.dump())

import json
import os

STATE_FILE = "/app/state/inventory.json"
BACKUP_FILE = "/app/backup/inventory.json"

def corrupt_both():
    """Simulate crash during write — corrupts both state and backup."""
    os.makedirs("/app/backup", exist_ok=True)
    partial = '{"apple": 100, "ban'
    with open(STATE_FILE, "w") as f:
        f.write(partial)
    with open(BACKUP_FILE, "w") as f:
        f.write(partial)

if __name__ == "__main__":
    corrupt_both()

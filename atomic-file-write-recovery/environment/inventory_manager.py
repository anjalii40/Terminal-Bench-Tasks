import json
import os
import sys

STATE_FILE = "/app/state/inventory.json"
BACKUP_FILE = "/app/backup/inventory.json"

class StateManager:
    def __init__(self, path):
        self.path = path

    def load(self):
        with open(self.path, "r") as f:
            return json.load(f)

    def save(self, data):
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

class BackupManager:
    def __init__(self, path):
        self.path = path

    def sync(self, data):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

def process_order(order, state_mgr, backup_mgr):
    state = state_mgr.load()
    for item, qty in order.items():
        if item not in state:
            raise ValueError(f"Unknown item: {item}")
        if state[item] < qty:
            raise ValueError(f"Insufficient stock: {item}")
        state[item] -= qty
    state_mgr.save(state)
    backup_mgr.sync(state)
    return state

if __name__ == "__main__":
    order_file = sys.argv[1] if len(sys.argv) > 1 else "/app/input/order.json"
    state_mgr = StateManager(STATE_FILE)
    backup_mgr = BackupManager(BACKUP_FILE)
    with open(order_file) as f:
        order = json.load(f)
    result = process_order(order, state_mgr, backup_mgr)
    os.makedirs("/app/output", exist_ok=True)
    with open("/app/output/result.json", "w") as f:
        json.dump(result, f, indent=2)

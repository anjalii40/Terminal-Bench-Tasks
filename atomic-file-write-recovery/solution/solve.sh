#!/bin/bash
python3 - << 'PYEOF'
with open("/app/inventory_manager.py", "r") as f:
    source = f.read()

fixed = source.replace(
    """    def save(self, data):
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)""",
    """    def save(self, data):
        import tempfile
        dir_name = os.path.dirname(self.path)
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, suffix=".tmp") as tmp:
            json.dump(data, tmp, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, self.path)"""
)

fixed = fixed.replace(
    """    def sync(self, data):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)""",
    """    def sync(self, data):
        import tempfile
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        dir_name = os.path.dirname(self.path)
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, suffix=".tmp") as tmp:
            json.dump(data, tmp, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, self.path)"""
)

with open("/app/inventory_manager.py", "w") as f:
    f.write(fixed)
PYEOF

cp /app/initial_state.json /app/state/inventory.json
mkdir -p /app/backup /app/output
python3 /app/inventory_manager.py /app/input/order.json

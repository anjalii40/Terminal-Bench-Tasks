#!/bin/bash
set -e

cat > /app/reconcile.py <<'PY'
import json
import os

BASE_DIR = "/app"
CHECKPOINT_FILE = os.path.join(BASE_DIR, "checkpoint.json")
REPLICA_FILES = [
    os.path.join(BASE_DIR, "replica_a.jsonl"),
    os.path.join(BASE_DIR, "replica_b.jsonl"),
    os.path.join(BASE_DIR, "replica_c.jsonl"),
]
LEDGER_FILE = os.path.join(BASE_DIR, "state", "ledger.json")
REPORT_FILE = os.path.join(BASE_DIR, "output", "reconciliation_report.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path):
    entries = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                entries.append(json.loads(stripped))
    return entries


def apply_operation(op, balances):
    amount = op["amount"]
    account = op["account"]
    if op["kind"] == "credit":
        balances[account] = balances.get(account, 0) + amount
    elif op["kind"] == "debit":
        balances[account] = balances.get(account, 0) - amount


def collect_candidates():
    occurrences = {}
    for replica_file in REPLICA_FILES:
        source = os.path.basename(replica_file)
        for op in load_jsonl(replica_file):
            op_id = op["op_id"]
            payload_map = occurrences.setdefault(op_id, {})
            payload_key = json.dumps(op, sort_keys=True)
            entry = payload_map.setdefault(payload_key, {"op": op, "sources": set()})
            entry["sources"].add(source)
    accepted = {}
    rejected = set()
    for op_id, payload_map in occurrences.items():
        if len(payload_map) != 1:
            rejected.add(op_id)
            continue
        entry = next(iter(payload_map.values()))
        if len(entry["sources"]) >= 2:
            accepted[op_id] = entry["op"]
        else:
            rejected.add(op_id)
    return accepted, rejected


def write_outputs(ledger, report):
    os.makedirs(os.path.dirname(LEDGER_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(LEDGER_FILE, "w", encoding="utf-8") as handle:
        json.dump(ledger, handle, indent=2, sort_keys=True)
        handle.write("\n")
    with open(REPORT_FILE, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    checkpoint = load_json(CHECKPOINT_FILE)
    balances = dict(checkpoint["balances"])
    checkpoint_ops = dict(checkpoint["applied_ops"])
    checkpoint_ids = set(checkpoint_ops)
    accepted, rejected = collect_candidates()

    for op_id in sorted(accepted):
        if op_id in checkpoint_ids:
            continue
        apply_operation(accepted[op_id], balances)

    ledger = {
        "balances": balances,
        "applied_ops": sorted(checkpoint_ids | set(accepted)),
    }
    report = {
        "accepted": sorted(accepted),
        "rejected": sorted(rejected),
    }
    write_outputs(ledger, report)


if __name__ == "__main__":
    main()
PY

python3 /app/reconcile.py

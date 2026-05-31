import json
import os
from collections import defaultdict

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
    items = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                items.append(json.loads(stripped))
    return items


def apply_operation(op, balances):
    amount = op["amount"]
    account = op["account"]
    if op["kind"] == "credit":
        balances[account] = balances.get(account, 0) + amount
    elif op["kind"] == "debit":
        balances[account] = balances.get(account, 0) - amount


def write_outputs(ledger, report):
    os.makedirs(os.path.dirname(LEDGER_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(LEDGER_FILE, "w", encoding="utf-8") as handle:
        json.dump(ledger, handle, indent=2)
        handle.write("\n")
    with open(REPORT_FILE, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")


def main():
    checkpoint = load_json(CHECKPOINT_FILE)
    balances = dict(checkpoint["balances"])
    checkpoint_ops = dict(checkpoint["applied_ops"])
    accepted = []
    rejected = []
    raw_ops = {}
    counts = defaultdict(int)

    for replica_file in REPLICA_FILES:
        for op in load_jsonl(replica_file):
            op_id = op["op_id"]
            raw_ops.setdefault(op_id, op)
            counts[op_id] += 1

    for op_id in raw_ops:
        if counts[op_id] >= 1:
            accepted.append(op_id)
        else:
            rejected.append(op_id)

    for op_id in accepted:
        apply_operation(raw_ops[op_id], balances)

    for op in checkpoint_ops.values():
        apply_operation(op, balances)

    ledger = {
        "balances": balances,
        "applied_ops": list(set(checkpoint_ops) | set(accepted)),
    }
    report = {
        "accepted": accepted,
        "rejected": rejected,
    }
    write_outputs(ledger, report)


if __name__ == "__main__":
    main()

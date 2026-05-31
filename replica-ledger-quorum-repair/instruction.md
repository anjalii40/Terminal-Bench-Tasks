A replica ledger repair utility lives at `/app/reconcile.py`.

It must rebuild a canonical ledger from:
- `/app/checkpoint.json`
- `/app/replica_a.jsonl`
- `/app/replica_b.jsonl`
- `/app/replica_c.jsonl`

Run it with:
- `python3 /app/reconcile.py`

The checkpoint is trusted. `checkpoint.json` contains:
- `balances`: the current account balances
- `applied_ops`: a mapping from `op_id` to the original applied operation payload

Replica logs contain JSON lines. Each operation has an `op_id` and one of these shapes:
- `{"op_id":"op-204","kind":"credit","account":"acct-amber","amount":15}`
- `{"op_id":"op-205","kind":"debit","account":"acct-cinder","amount":9}`

Repair `/app/reconcile.py` so it writes:
- `/app/state/ledger.json`
- `/app/output/reconciliation_report.json`

Rules:
- Credits add `amount`.
- Debits subtract `amount`.
- All amounts are positive integers.
- An operation is accepted only if the same full payload for the same `op_id` appears in at least two different replica logs.
- If the same `op_id` appears with different payloads anywhere in the replica logs, that `op_id` is rejected completely.
- Any `op_id` already present in `checkpoint.json` under `applied_ops` must not change balances again.
- After acceptance is determined, apply accepted operations in lexicographic `op_id` order.
- Final outputs must be deterministic and sorted.

Output format:
- `/app/state/ledger.json` must be valid JSON with exactly these top-level keys:
  - `balances`
  - `applied_ops`
- In `/app/state/ledger.json`:
  - `balances` must be an object whose values are integers
  - `applied_ops` must be a lexicographically sorted list of operation ids
- `/app/output/reconciliation_report.json` must be valid JSON with exactly these top-level keys:
  - `accepted`
  - `rejected`
- In `/app/output/reconciliation_report.json`:
  - `accepted` must be a lexicographically sorted list of accepted operation ids
  - `rejected` must be a lexicographically sorted list of rejected operation ids

Constraints:
- Do not use the internet.
- Do not install additional packages.
- Use the existing Python standard library only.

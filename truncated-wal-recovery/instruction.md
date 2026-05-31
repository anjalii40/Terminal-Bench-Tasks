A custom key-value store service located at `/app/db.py` relies on an append-only Write-Ahead Log (WAL) and periodic snapshots.

Every hour, a compaction job reads `/app/state/wal.log`, updates the base `/app/state/snapshot.json`, backs up the logs, and then empties the WAL. 

A simulated hardware crash has occurred *during* the compaction process. As a result:
- `/app/state/snapshot.json` is corrupted (partially written JSON).
- `/app/state/wal.log` is empty.
- However, the pre-compaction backups are intact: `/app/state/snapshot.json.bak` and `/app/state/wal.log.bak`.

Currently, the service crashes on startup with a `JSONDecodeError` because it blindly attempts to load the corrupted snapshot.

**WAL Schema:**
The WAL contains JSON-lines with the following fields: `tx_id`, `type`, `key` (optional), and `value` (optional).
- `{"tx_id": "tx-1", "type": "BEGIN"}`
- `{"tx_id": "tx-1", "type": "SET", "key": "k1", "value": "v1"}`
- `{"tx_id": "tx-1", "type": "DEL", "key": "k2"}`
- `{"tx_id": "tx-1", "type": "COMMIT"}`

**Critical Requirement:**
Transactions in the WAL can be interleaved or incomplete. 
1. **Any operations belonging to a transaction that does not have a corresponding `COMMIT` must be discarded during recovery.**
2. **If multiple transactions update the same key, the final state is strictly determined by the order of their `COMMIT` records in the log, regardless of the order of their `SET` operations.**

**Task:**
Modify `/app/db.py` so that its `startup()` method detects the corruption and successfully recovers the state. The recovery process must:
1. Fall back to `/app/state/snapshot.json.bak`.
2. Parse and replay the committed transactions from `/app/state/wal.log.bak` correctly.
3. Save the successfully recovered state to `/app/state/snapshot.json`.

After the fix, running `python3 /app/db.py dump` should print the repaired, valid JSON state reflecting all completed transactions.

A Python inventory management application at `/app/inventory_manager.py` reads and writes JSON state using two components: `StateManager` (primary state) and `BackupManager` (backup copy).

The application has a bug: both `StateManager.save()` and `BackupManager.sync()` write directly to their target files, making them vulnerable to corruption if the process is interrupted mid-write.

Fix the bug in `/app/inventory_manager.py` so that all file writes are atomic and crash-safe.

## Files

- `/app/inventory_manager.py` — application to fix
- `/app/initial_state.json` — starting inventory (`{"apple": 100, "banana": 50, "orange": 75}`)
- `/app/input/order.json` — order to process (`{"apple": 10, "banana": 5}`)
- `/app/state/inventory.json` — primary state file
- `/app/backup/inventory.json` — backup copy
- `/app/output/result.json` — final result output

## Output format

All JSON files must contain valid JSON after every run.

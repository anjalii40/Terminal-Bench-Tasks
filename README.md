# Benchmark Task Portfolio

This repository collects a set of self-contained debugging and reasoning tasks I authored during freelance benchmark work.

Each task is packaged as a hermetic evaluation problem with its own:

- `instruction.md` task brief
- `environment/` runtime and input files
- `solution/` reference solver
- `tests/` verifier suite
- `task.toml` metadata

The goal of this repo is to present the work in a clean portfolio format instead of a loose set of submission ZIPs.

## What This Shows

- Task design for agent evaluation and benchmarking
- Debugging scenarios around concurrency, crash safety, and recovery
- Reasoning-heavy simulation tasks with strict output validation
- Cross-language task authoring in Python, shell, and C++
- Hermetic test design with deterministic outputs

## Task Catalog

| Task | Focus Area | Language | Difficulty | Highlights |
| --- | --- | --- | --- | --- |
| `atomic-file-write-recovery` | Crash-safe persistence | Python | Medium | Atomic JSON writes, primary/backup state coordination, interruption safety |
| `borrowed-faces-archive` | Filesystem archiving | Python | Hard | Hardlinks/symlinks, preserving inode on replace, literal target checks |
| `fix-async-race-condition` | Concurrency debugging | Python | Medium | Async workers, shared-state races, deterministic counter validation |
| `inverter-deadtime-reconstruction` | Systems simulation | C++ | Medium | Three-phase inverter state reconstruction, dead-time windows, line-voltage derivation |
| `overprint-plate-register` | Process simulation | Python | Medium | ASCII-grid print passes, drag behavior, feed-direction changes |
| `replica-ledger-quorum-repair` | Distributed state repair | Python | Medium | Replica quorum rules, conflict rejection, deterministic reconciliation |
| `signature-bookbinder` | Spatial reasoning | Python | Hard | Fold simulation, panel orientation, tab visibility rules |
| `stepper-backlash-simulator` | Physical control simulation | C++ | Medium | Mechanical gear backlash, direction switches, aborted transitions |
| `truncated-wal-recovery` | Storage recovery | Python | Hard | Snapshot fallback, WAL replay, committed-transaction filtering |

## Repository Structure

```text
atomic-file-write-recovery/
borrowed-faces-archive/
fix-async-race-condition/
inverter-deadtime-reconstruction/
overprint-plate-register/
replica-ledger-quorum-repair/
signature-bookbinder/
stepper-backlash-simulator/
truncated-wal-recovery/
```

## Notes

- These are synthetic benchmark tasks prepared for hermetic execution.
- No internet access or external package installation is required by the tasks unless explicitly stated.
- The original submission ZIPs are intentionally not included here; this repo contains the unpacked, readable project form instead.

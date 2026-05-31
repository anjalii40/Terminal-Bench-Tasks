# Terminal-Bench-Tasks: AI Coding Agent Evaluation Portfolio

This repository showcases a set of self-contained debugging, systems-recovery, and reasoning tasks designed to evaluate the problem-solving capabilities of AI coding agents in a terminal-based environment. 

Rather than standard competitive programming or syntax patching, each task here is a realistic, packaged software engineering problem containing a starter codebase, a Docker environment, clear instructions, and a strict verification suite.

---

## The Core Philosophy

The focus of this project is **adversarial evaluation and benchmark design**:
- **Beyond Syntax Patching:** Testing if agents can inspect state, reason through timed race conditions, or handle database recovery scenarios.
- **Hermetic & Deterministic:** Tasks run within controlled container environments with zero external network dependencies and precise automated testing.
- **Difficulty Tuning:** Refined to prevent "code compression" (where models bypass constraints and rewrite logic from scratch), forcing agents to understand and preserve existing software architectures.

---

## Task Catalog

### Systems & Recovery
*Focused on state recovery, timing bugs, filesystem consistency, and distributed consensus.*

| Task | Focus Area | Language | Difficulty | Highlights |
| --- | --- | --- | --- | --- |
| [`atomic-file-write-recovery`](./atomic-file-write-recovery) | Crash-safe persistence | Python | Medium | Atomic JSON writes, primary/backup state coordination, interruption safety |
| [`fix-async-race-condition`](./fix-async-race-condition) | Concurrency debugging | Python | Medium | Async workers, shared-state races, deterministic counter validation |
| [`replica-ledger-quorum-repair`](./replica-ledger-quorum-repair) | Distributed state repair | Python | Medium | Replica quorum rules, conflict rejection, deterministic reconciliation |
| [`truncated-wal-recovery`](./truncated-wal-recovery) | Storage recovery | Python | Hard | Snapshot fallback, WAL replay, committed-transaction filtering |

### Reasoning & Simulation
*Focused on temporal logic, spatial rules, state transitions, and step-by-step physical models.*

| Task | Focus Area | Language | Difficulty | Highlights |
| --- | --- | --- | --- | --- |
| [`borrowed-faces-archive`](./borrowed-faces-archive) | Filesystem archiving | Python | Hard | Hardlinks/symlinks, preserving inode on replace, literal target checks |
| [`inverter-deadtime-reconstruction`](./inverter-deadtime-reconstruction) | Systems simulation | C++ | Medium | Three-phase inverter state reconstruction, dead-time windows, line-voltage derivation |
| [`overprint-plate-register`](./overprint-plate-register) | Process simulation | Python | Medium | ASCII-grid print passes, drag behavior, feed-direction changes |
| [`signature-bookbinder`](./signature-bookbinder) | Spatial reasoning | Python | Hard | Fold simulation, panel orientation, tab visibility rules |
| [`stepper-backlash-simulator`](./stepper-backlash-simulator) | Physical control simulation | C++ | Medium | Mechanical gear backlash, direction switches, aborted transitions |

---

## Task Architecture

Each folder in this repository represents a complete evaluation package:

```text
[task-directory]/
  ├── instruction.md   # Task description, requirements, and constraints
  ├── task.toml        # Metadata (author, tags, estimated time, verifier limits)
  ├── environment/     # Starter files and execution environment config
  ├── solution/        # Reference solution or patching script (solve.sh)
  └── tests/           # Verification suite containing visible and hidden test fixtures
```

---

## Key Development Insights

- **Reproducibility:** Ensuring all execution environments are hermetic, with permissions and path behaviors defined deterministically across runtimes.
- **Visible vs. Deceptive Fixtures:** Balancing test visibility so agents are guided on expected input formats, but checked against edge cases to ensure they implement robust, generalizable code.
- **Historical State Preservation:** Designing verification tests that fail when agents ignore edge cases, write partial files, or fail to handle interrupted processing correctly.

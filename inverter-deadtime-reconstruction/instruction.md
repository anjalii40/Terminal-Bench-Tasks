# Three-Phase Inverter Dead-Time Reconstruction

Repair or replace `environment/inverter.cpp`.

The repaired program must compile with:

```text
g++ -std=c++17 -O2 -Wall -Wextra -o /tmp/inverter /environment/inverter.cpp
```

The compiled binary will be executed as:

```text
/tmp/inverter INPUT_DIR TIMELINE_PATH REPORT_PATH
```

`INPUT_DIR` contains:

- `config.json`
- `commands.tsv`
- `currents.tsv`

`config.json` contains exactly one required key:

- `dead_time_ticks`: positive integer

`commands.tsv` is tab-separated with header:

```text
tick	A	B	C
```

Each phase command is:

- `U`: request the upper transistor
- `L`: request the lower transistor

`currents.tsv` is tab-separated with the same ticks and header:

```text
tick	A	B	C
```

Each phase current sign is one of:

- `+`
- `-`
- `0`

At tick `0`, each phase starts from that tick's requested command and no synthetic dead-time is created.

At any later tick, if the input command requests the opposite transistor from the command currently in effect for that phase, a commutation begins immediately on that tick and the phase starts a fresh dead-time window of `dead_time_ticks`. If another command change arrives before the current dead-time window finishes, restart the dead-time window on that tick and increment `restarted_deadtime_events` for that phase.

While a dead-time window is active, the realized phase state depends only on the current sign:

- `+` => mode `DL`, node `N`
- `-` => mode `DU`, node `P`
- `0` => mode `OFF`, node `Z`

A new commutation does not always take effect as soon as dead-time expires.
After dead-time has expired, the new command remains blocked as long as the current sustains conduction through the freewheeling diode of the outgoing state.

Use these diode-family sustain rules:

- an outgoing `L` state is sustained by `+`, which keeps the realized state on `DL`, node `N`
- an outgoing `U` state is sustained by `-`, which keeps the realized state on `DU`, node `P`
- `0` sustains neither diode family

The new command takes effect on the first tick where the current no longer sustains the outgoing diode family. From that tick onward, the realized transistor state follows the new command unless a later command change starts another commutation.

If no commutation is underway, the realized transistor state depends only on the command currently in effect:

- `U` => mode `TU`, node `P`
- `L` => mode `TL`, node `N`

After writing each tick, decrement the active dead-time counter by `1` if it is greater than `0`.

Node levels are:

- `P = +1`
- `Z = 0`
- `N = -1`

Line voltages are derived from realized node levels:

- `Vab` is `+` if `A_node > B_node`, `0` if equal, `-` otherwise
- `Vbc` is `+` if `B_node > C_node`, `0` if equal, `-` otherwise
- `Vca` is `+` if `C_node > A_node`, `0` if equal, `-` otherwise

Write `TIMELINE_PATH` as tab-separated text with exactly this header:

```text
tick	A_mode	A_node	B_mode	B_node	C_mode	C_node	Vab	Vbc	Vca
```

Allowed mode values:

- `TU`
- `TL`
- `DU`
- `DL`
- `OFF`

Allowed node values:

- `P`
- `N`
- `Z`

Write `REPORT_PATH` as JSON with exactly these top-level keys:

- `upper_transistor_ticks`
- `lower_transistor_ticks`
- `upper_diode_ticks`
- `lower_diode_ticks`
- `floating_ticks`
- `restarted_deadtime_events`

Each report value must be an object with exactly these keys:

- `A`
- `B`
- `C`

Provided files:

- `environment/inverter.cpp`
- `environment/sample_job/config.json`
- `environment/sample_job/commands.tsv`
- `environment/sample_job/currents.tsv`

Verifier-owned repository fixtures also exist under `tests/fixtures/` for exact evaluation. They are verifier-side files and are not copied into `/environment`.

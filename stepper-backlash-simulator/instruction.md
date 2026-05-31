# Stepper Motor Backlash Reconstruction

Repair or replace `environment/stepper.cpp`.

The repaired program must compile with:

```text
g++ -std=c++17 -O2 -Wall -Wextra -o /tmp/stepper /environment/stepper.cpp
```

The compiled binary will be executed as:

```text
/tmp/stepper INPUT_DIR TIMELINE_PATH REPORT_PATH
```

`INPUT_DIR` contains:

- `config.json`
- `commands.tsv`

`config.json` contains exactly two keys:

- `slew_ticks`: positive integer
- `backlash_ticks`: positive integer

`commands.tsv` is tab-separated with exactly this header:

```text
tick	target
```

At tick `0`, the motor initializes at the requested `target` position. The mechanical gears are considered completely disengaged (direction `0`). The motor is `IDLE`.

At any later tick, if the input `target` differs from the current physical position, the motor must move toward the target. The motor moves exactly one position unit at a time. Each unit step takes `slew_ticks` to complete. Once a single step has begun, it cannot be interrupted or reversed until the position physically increments or decrements.

Before any unit step can begin, the mechanical gears must be engaged in the required direction of travel (`+1` for increasing position, `-1` for decreasing).
If the gears were last engaged in a different direction (including the initial `0` disengaged state), the motor must first spend `backlash_ticks` in a `BACKLASH` state to take up the mechanical slack before the step can begin.

The `BACKLASH` state physically prepares the gears for the *new* required direction. However, if the target changes during the `BACKLASH` state such that the motor needs to move in the *previously* engaged direction instead, the slack is already taken up in that direction. The `BACKLASH` state is instantly aborted, and the motor begins slewing in the original direction immediately.
If the target changes to the current physical position during `BACKLASH`, the motor simply becomes `IDLE` and the gears remain in their previously engaged direction.

When the motor has reached the target position and no backlash is underway, its state is `IDLE`.

Allowed states for the timeline:
- `IDLE`
- `SLEWING`
- `BACKLASH`

Write `TIMELINE_PATH` as tab-separated text with exactly this header:

```text
tick	position	state
```

Write `REPORT_PATH` as JSON with exactly these top-level keys:

- `idle_ticks`
- `slewing_ticks`
- `backlash_ticks`
- `aborted_backlash_events`

`aborted_backlash_events` counts the exact number of times a `BACKLASH` state was instantly aborted because the target changed to require a step in the previously engaged direction. Changes that simply make the motor `IDLE` do not increment this counter.

Provided files:

- `environment/stepper.cpp`
- `environment/sample_job/config.json`
- `environment/sample_job/commands.tsv`

Verifier-owned repository fixtures also exist under `tests/fixtures/` for exact evaluation. They are verifier-side files and are not copied into `/environment`.

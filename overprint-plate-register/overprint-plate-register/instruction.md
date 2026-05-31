# Overprint Plate Register

Repair or replace `environment/register.py`.

The program must keep this command-line interface:

```text
python environment/register.py JOB_DIR PROOF_PATH REPORT_PATH
```

`JOB_DIR` contains:

- `sheet.txt`
- `schedule.tsv`
- `plates/<name>.plate`

This is a hermetic environment. Do not use internet access or install external packages.

Only the contents of `sheet.txt`, `schedule.tsv`, and the plate files referenced by `schedule.tsv` affect the result. Unrelated files must be ignored. Renaming referenced plate files does not change the result if `schedule.tsv` is updated consistently.

## Input files

`sheet.txt`

- Rectangular ASCII grid.
- `.` means blank sheet.
- Any other visible character is a dry preprinted mark.
- Input and output files are plain UTF-8 text.

`schedule.tsv`

- Tab-separated with a required header row.
- Rows run in file order.
- Columns:
  - `pass_id`
  - `plate`
  - `ink`
  - `x`
  - `y`
  - `turn_after`
  - `dry_after`

`plates/<name>.plate`

- Rectangular ASCII grid.
- `.` means no contact.
- `#` means normal print contact.
- `~` means drag contact.

## Sheet and feed model

Each sheet cell stores:

- a visible character
- a wetness counter

Initial state:

- characters come from `sheet.txt`
- all initial marks start dry with wetness `0`

Global state:

- feed direction starts `east`
- after a pass with `turn_after=yes`, future passes use `west`
- another `turn_after=yes` flips future passes back to `east`

## Plate placement and pass execution

- `x` and `y` are integer top-left offsets and may place part of a plate off sheet
- off-sheet contacts are ignored completely
- rows are always processed top-to-bottom
- in `east` feed, the plate is placed and processed exactly as written, with columns left-to-right
- in `west` feed, the plate is horizontally mirrored for placement at the same `x`, `y` anchor, then processed right-to-left
- contacts are resolved immediately in processing order, so later contacts in the same pass see the sheet state after earlier contacts in that pass

For each contacted sheet cell:

- `#` writes the current pass `ink` into that cell and increases that cell's wetness by `2`
- `~` first checks the current target cell
- if that target cell is wet (`wetness > 0`) and non-blank, attempt to drag its current visible mark one cell in the current feed direction
- if the drag destination is inside the sheet and currently blank, move that dragged mark there and increase the destination wetness by `1`
- otherwise that dragged mark is lost
- after drag resolution, write the current pass `ink` into the target cell and increase that cell's wetness by `2`

Wetness is cumulative across contacts. If multiple contacts affect the same cell before drying, each one adds its wetness change immediately.

After each pass:

- apply exactly `dry_after` dry cycles
- each dry cycle decrements every positive wetness by `1`
- wetness never goes below `0`

## Outputs

Write `PROOF_PATH` as the final visible sheet only:

- exact ASCII grid
- newline-terminated

Write `REPORT_PATH` as JSON with exactly these top-level keys, in exactly this order:

- `turned_passes`
- `drag_events`
- `lost_drags`
- `ink_counts`

Rules:

- `turned_passes`: `pass_id` values whose row has `turn_after=yes`, in schedule order
- `drag_events`: number of successful drags
- `lost_drags`: number of failed drags
- `ink_counts`: counts of visible final `A`-`Z` characters in the proof, sorted by key, including any surviving preprinted uppercase marks

Write the JSON with indentation `2` and a trailing newline.

Provided files:

- `environment/register.py`
- `environment/sample_job/sheet.txt`
- `environment/sample_job/schedule.tsv`
- `environment/sample_job/plates/*.plate`

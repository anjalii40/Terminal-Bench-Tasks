#!/bin/sh
set -eu

target=/environment/register.py
if [ ! -d /environment ]; then
  target=environment/register.py
fi

cat > "$target" <<'PY'
import csv
import json
import sys
from pathlib import Path


def read_grid(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    width = len(lines[0])
    if any(len(line) != width for line in lines):
        raise ValueError(f"non-rectangular grid: {path}")
    return [list(line) for line in lines]


def load_schedule(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = ["pass_id", "plate", "ink", "x", "y", "turn_after", "dry_after"]
        if reader.fieldnames != required:
            raise ValueError("schedule.tsv header mismatch")
        return list(reader)


def dry_cells(wetness, cycles):
    for _ in range(cycles):
        for row in range(len(wetness)):
            for col in range(len(wetness[row])):
                if wetness[row][col] > 0:
                    wetness[row][col] -= 1


def mirrored_plate(plate):
    return [list(reversed(row)) for row in plate]


def count_visible_inks(sheet):
    counts = {}
    for row in sheet:
        for cell in row:
            if len(cell) == 1 and "A" <= cell <= "Z":
                counts[cell] = counts.get(cell, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def run(job_dir):
    sheet = read_grid(job_dir / "sheet.txt")
    wetness = [[0 for _ in row] for row in sheet]
    schedule = load_schedule(job_dir / "schedule.tsv")
    plates_dir = job_dir / "plates"

    height = len(sheet)
    width = len(sheet[0]) if height else 0

    feed = "east"
    turned_passes = []
    drag_events = 0
    lost_drags = 0

    for entry in schedule:
        plate = read_grid(plates_dir / f"{entry['plate']}.plate")
        if not plate:
            continue

        ink = entry["ink"]
        if len(ink) != 1:
            raise ValueError("ink values must be single characters")
        x = int(entry["x"])
        y = int(entry["y"])
        turn = entry["turn_after"].strip().lower() == "yes"
        dry_after = int(entry["dry_after"])

        active_plate = plate if feed == "east" else mirrored_plate(plate)
        col_indices = range(len(active_plate[0])) if feed == "east" else range(len(active_plate[0]) - 1, -1, -1)
        step = 1 if feed == "east" else -1

        for row_index, row in enumerate(active_plate):
            for col_index in col_indices:
                token = row[col_index]
                if token == ".":
                    continue

                target_x = x + col_index
                target_y = y + row_index
                if not (0 <= target_x < width and 0 <= target_y < height):
                    continue

                if token == "~":
                    current = sheet[target_y][target_x]
                    if current != "." and wetness[target_y][target_x] > 0:
                        dest_x = target_x + step
                        if 0 <= dest_x < width and sheet[target_y][dest_x] == ".":
                            sheet[target_y][dest_x] = current
                            wetness[target_y][dest_x] += 1
                            drag_events += 1
                        else:
                            lost_drags += 1

                sheet[target_y][target_x] = ink
                wetness[target_y][target_x] += 2

        if turn:
            turned_passes.append(entry["pass_id"])
            feed = "west" if feed == "east" else "east"

        dry_cells(wetness, dry_after)

    proof = "\n".join("".join(row) for row in sheet) + "\n"
    report = {
        "turned_passes": turned_passes,
        "drag_events": drag_events,
        "lost_drags": lost_drags,
        "ink_counts": count_visible_inks(sheet),
    }
    return proof, report


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: python environment/register.py JOB_DIR PROOF_PATH REPORT_PATH")

    proof, report = run(Path(argv[1]))
    Path(argv[2]).write_text(proof, encoding="utf-8")
    with Path(argv[3]).open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main(sys.argv)
PY

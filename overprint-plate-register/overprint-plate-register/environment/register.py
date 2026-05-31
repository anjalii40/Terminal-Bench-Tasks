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


def dry_cells(wetness, steps):
    for _ in range(steps):
        for row in range(len(wetness)):
            for col in range(len(wetness[row])):
                if wetness[row][col] > 0:
                    wetness[row][col] -= 1


def load_schedule(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader)


def load_plate(plates_dir, name):
    return read_grid(plates_dir / f"{name}.plate")


def run(job_dir):
    sheet = read_grid(job_dir / "sheet.txt")
    wetness = [[0 for _ in row] for row in sheet]
    schedule = load_schedule(job_dir / "schedule.tsv")
    plates_dir = job_dir / "plates"

    feed = "east"
    turned_passes = []
    drag_events = 0
    lost_drags = 0

    height = len(sheet)
    width = len(sheet[0]) if height else 0

    for entry in schedule:
        plate = load_plate(plates_dir, entry["plate"])
        turn = entry["turn_after"].strip().lower() == "yes"
        x = int(entry["x"])
        y = int(entry["y"])
        ink = entry["ink"]
        dry_after = int(entry["dry_after"])

        if turn:
            turned_passes.append(entry["pass_id"])
            feed = "west" if feed == "east" else "east"

        dry_cells(wetness, dry_after)

        for row_index, row in enumerate(plate):
            for col_index, token in enumerate(row):
                if token == ".":
                    continue
                target_x = x + col_index
                target_y = y + row_index
                if not (0 <= target_x < width and 0 <= target_y < height):
                    continue

                if token == "~" and sheet[target_y][target_x] != "." and wetness[target_y][target_x] > 0:
                    step = 1 if feed == "east" else -1
                    dest_x = target_x + step
                    if 0 <= dest_x < width and sheet[target_y][dest_x] == ".":
                        sheet[target_y][dest_x] = sheet[target_y][target_x]
                        wetness[target_y][dest_x] = 1
                        drag_events += 1
                    else:
                        lost_drags += 1

                sheet[target_y][target_x] = ink
                wetness[target_y][target_x] = 2

    ink_counts = {}
    for row in sheet:
        for cell in row:
            if len(cell) == 1 and "A" <= cell <= "Z":
                ink_counts[cell] = ink_counts.get(cell, 0) + 1

    return {
        "proof": "\n".join("".join(row) for row in sheet) + "\n",
        "report": {
            "turned_passes": turned_passes,
            "drag_events": drag_events,
            "lost_drags": lost_drags,
            "ink_counts": ink_counts,
        },
    }


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: python environment/register.py JOB_DIR PROOF_PATH REPORT_PATH")

    result = run(Path(argv[1]))
    Path(argv[2]).write_text(result["proof"], encoding="utf-8")
    with Path(argv[3]).open("w", encoding="utf-8") as handle:
        json.dump(result["report"], handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main(sys.argv)

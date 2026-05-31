import csv
import json
import os
import shutil
import sys
from pathlib import Path


def read_anchors(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["body_id", "anchor_path"]:
            raise ValueError("anchors.tsv header mismatch")
        return list(reader)


def read_plan(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["path", "kind", "body_id", "face_id", "target"]:
            raise ValueError("plan.tsv header mismatch")
        return list(reader)


def replace_path(path):
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python environment/archive.py JOB_DIR REPORT_PATH")

    job_dir = Path(argv[1])
    gallery = job_dir / "gallery"
    faces = job_dir / "faces"
    anchors = read_anchors(job_dir / "anchors.tsv")
    plan = read_plan(job_dir / "plan.tsv")

    body_to_anchor = {row["body_id"]: gallery / row["anchor_path"] for row in anchors}
    body_to_rows = {}
    symlink_rows = []
    for row in plan:
        if row["kind"] == "file":
            body_to_rows.setdefault(row["body_id"], []).append(row)
        else:
            symlink_rows.append(row)

    for rows in body_to_rows.values():
        face_path = faces / f"{rows[0]['face_id']}.txt"
        payload = face_path.read_bytes()
        for row in rows:
            destination = gallery / row["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            replace_path(destination)
            destination.write_bytes(payload)

    for row in symlink_rows:
        destination = gallery / row["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        replace_path(destination)
        os.symlink(row["target"], destination)

    report = {
        "anchors_preserved": sorted(body_to_anchor),
        "hardlink_groups": {
            body_id: sorted(item["path"] for item in body_to_rows[body_id])
            for body_id in sorted(body_to_rows)
        },
        "symlinks": len(symlink_rows),
        "regular_files": sum(len(rows) for rows in body_to_rows.values()),
    }
    with Path(argv[2]).open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main(sys.argv)

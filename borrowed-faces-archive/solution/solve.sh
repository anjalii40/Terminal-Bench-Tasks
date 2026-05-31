#!/bin/sh
set -eu

cat > /environment/archive.py <<'PY'
import csv
import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path


def read_tsv(path, expected_header):
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != expected_header:
            raise ValueError(f"{path.name} header mismatch")
        return list(reader)


def remove_path(path):
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def ensure_parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)


def required_dirs_for(paths):
    required = {Path(".")}
    for rel_path in paths:
        current = Path(rel_path).parent
        while current != Path("."):
            required.add(current)
            current = current.parent
    return required


def write_bytes_in_place(path, payload):
    with path.open("r+b") as handle:
        handle.seek(0)
        handle.truncate()
        handle.write(payload)


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python environment/archive.py JOB_DIR REPORT_PATH")

    job_dir = Path(argv[1])
    report_path = Path(argv[2])
    gallery = job_dir / "gallery"
    faces_dir = job_dir / "faces"

    anchors = read_tsv(job_dir / "anchors.tsv", ["body_id", "anchor_path"])
    plan = read_tsv(job_dir / "plan.tsv", ["path", "kind", "body_id", "face_id", "target"])

    body_to_anchor_rel = {}
    body_to_anchor_abs = {}
    original_anchor_inodes = {}
    for row in anchors:
        body_id = row["body_id"]
        anchor_rel = Path(row["anchor_path"])
        anchor_abs = gallery / anchor_rel
        if not anchor_abs.is_file() or anchor_abs.is_symlink():
            raise ValueError(f"anchor is not a regular file: {anchor_rel}")
        body_to_anchor_rel[body_id] = anchor_rel
        body_to_anchor_abs[body_id] = anchor_abs
        original_anchor_inodes[body_id] = anchor_abs.stat().st_ino

    file_rows = []
    symlink_rows = []
    body_to_face = {}
    body_to_group = defaultdict(list)
    for row in plan:
        rel_path = Path(row["path"])
        kind = row["kind"]
        if kind == "file":
            body_id = row["body_id"]
            face_id = row["face_id"]
            if body_id not in body_to_anchor_abs:
                raise ValueError(f"unknown body_id: {body_id}")
            if body_id in body_to_face and body_to_face[body_id] != face_id:
                raise ValueError(f"inconsistent face_id for {body_id}")
            body_to_face[body_id] = face_id
            file_rows.append(row)
            body_to_group[body_id].append(row["path"])
        elif kind == "symlink":
            symlink_rows.append(row)
        else:
            raise ValueError(f"unknown kind: {kind}")

    planned_paths = {Path(row["path"]) for row in plan}
    required_dirs = required_dirs_for(planned_paths)

    for directory in sorted(required_dirs, key=lambda item: len(item.parts)):
        (gallery / directory).mkdir(parents=True, exist_ok=True)

    anchor_paths = set(body_to_anchor_rel.values())

    for row in file_rows:
        rel_path = Path(row["path"])
        if rel_path not in anchor_paths:
            remove_path(gallery / rel_path)

    for row in symlink_rows:
        remove_path(gallery / row["path"])

    for body_id, face_id in body_to_face.items():
        payload = (faces_dir / f"{face_id}.txt").read_bytes()
        write_bytes_in_place(body_to_anchor_abs[body_id], payload)

    for row in file_rows:
        body_id = row["body_id"]
        rel_path = Path(row["path"])
        target_path = gallery / rel_path
        anchor_abs = body_to_anchor_abs[body_id]
        if rel_path == body_to_anchor_rel[body_id]:
            continue
        ensure_parent(target_path)
        remove_path(target_path)
        os.link(anchor_abs, target_path)

    for row in symlink_rows:
        target_path = gallery / row["path"]
        ensure_parent(target_path)
        remove_path(target_path)
        os.symlink(row["target"], target_path)

    for root, dirs, files in os.walk(gallery, topdown=False):
        root_path = Path(root)
        rel_root = root_path.relative_to(gallery)
        for name in files:
            rel_path = rel_root / name if rel_root != Path(".") else Path(name)
            if rel_path not in planned_paths:
                remove_path(root_path / name)
        for name in dirs:
            child = root_path / name
            rel_child = child.relative_to(gallery)
            if rel_child not in required_dirs:
                remove_path(child)

    anchors_preserved = [
        body_id
        for body_id in sorted(body_to_anchor_abs)
        if body_to_anchor_abs[body_id].stat().st_ino == original_anchor_inodes[body_id]
    ]
    hardlink_groups = {
        body_id: sorted(body_to_group[body_id])
        for body_id in sorted(body_to_group)
    }
    report = {
        "anchors_preserved": anchors_preserved,
        "hardlink_groups": hardlink_groups,
        "symlinks": len(symlink_rows),
        "regular_files": len(file_rows),
    }

    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main(sys.argv)
PY

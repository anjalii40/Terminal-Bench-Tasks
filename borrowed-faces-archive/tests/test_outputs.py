import json
import os
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "environment" / "archive.py"


BLUEPRINTS = {
    "sample_job": {
        "faces": {
            "amber": "AMBER FACE\nline two\n",
            "onyx": "ONYX FACE\n",
            "verdigris": "VERDIGRIS FACE\n",
        },
        "anchors": {
            "amber": "hall/north/anchor.txt",
            "onyx": "hall/south/ledger.txt",
            "verdigris": "vault/body.txt",
        },
        "plan": [
            {"path": "hall/north/anchor.txt", "kind": "file", "body_id": "amber", "face_id": "amber", "target": "-"},
            {"path": "hall/north/mask.txt", "kind": "file", "body_id": "amber", "face_id": "amber", "target": "-"},
            {"path": "hall/south/ledger.txt", "kind": "file", "body_id": "onyx", "face_id": "onyx", "target": "-"},
            {"path": "annex/borrowed.txt", "kind": "file", "body_id": "onyx", "face_id": "onyx", "target": "-"},
            {"path": "vault/body.txt", "kind": "file", "body_id": "verdigris", "face_id": "verdigris", "target": "-"},
            {"path": "signs/north-arrow", "kind": "symlink", "body_id": "-", "face_id": "-", "target": "../hall/north/anchor.txt"},
            {"path": "signs/missing-arrow", "kind": "symlink", "body_id": "-", "face_id": "-", "target": "../missing/door.txt"},
        ],
        "initial": [
            {"kind": "file", "path": "hall/north/anchor.txt", "content": "wrong amber\n"},
            {"kind": "hardlink", "path": "hall/north/old-mask.txt", "to": "hall/north/anchor.txt"},
            {"kind": "file", "path": "hall/south/ledger.txt", "content": "wrong onyx\n"},
            {"kind": "file", "path": "vault/body.txt", "content": "wrong verdigris\n"},
            {"kind": "file", "path": "hall/south/spare.txt", "content": "extra\n"},
            {"kind": "dir", "path": "notes"},
            {"kind": "file", "path": "notes/ghost.txt", "content": "ghost\n"},
            {"kind": "symlink", "path": "sign-post", "target": "../hall/north/anchor.txt"},
        ],
    },
    "literal_targets_and_type_replacement": {
        "faces": {
            "copper": "COPPER\n",
            "paper": "PAPER FACE\nmore\n",
        },
        "anchors": {
            "copper-body": "rooms/east/anchor.dat",
            "paper-body": "rooms/west/sheet.dat",
        },
        "plan": [
            {"path": "rooms/west/sheet.dat", "kind": "file", "body_id": "paper-body", "face_id": "paper", "target": "-"},
            {"path": "rooms/east/anchor.dat", "kind": "file", "body_id": "copper-body", "face_id": "copper", "target": "-"},
            {"path": "rooms/east/copper-copy.dat", "kind": "file", "body_id": "copper-body", "face_id": "copper", "target": "-"},
            {"path": "rooms/west/copper-via-west.dat", "kind": "file", "body_id": "copper-body", "face_id": "copper", "target": "-"},
            {"path": "labels/raw-pointer", "kind": "symlink", "body_id": "-", "face_id": "-", "target": "../../rooms/./east/../east/anchor.dat"},
            {"path": "labels/missing-hop", "kind": "symlink", "body_id": "-", "face_id": "-", "target": "../void/../void/fall.txt"},
        ],
        "initial": [
            {"kind": "file", "path": "rooms/east/anchor.dat", "content": "old copper\n"},
            {"kind": "file", "path": "rooms/west/sheet.dat", "content": "old paper\n"},
            {"kind": "symlink", "path": "rooms/east/copper-copy.dat", "target": "../west/sheet.dat"},
            {"kind": "dir", "path": "rooms/west/copper-via-west.dat"},
            {"kind": "file", "path": "rooms/west/copper-via-west.dat/nested.txt", "content": "bad nest\n"},
            {"kind": "file", "path": "labels/raw-pointer", "content": "not a symlink\n"},
            {"kind": "symlink", "path": "labels/missing-hop", "target": "../wrong/place.txt"},
            {"kind": "file", "path": "scratch.txt", "content": "delete me\n"},
        ],
    },
    "prunes_extra_dirs_and_breaks_wrong_aliases": {
        "faces": {
            "jade": "JADE MASK\n",
            "silt": "SILT MASK\n",
            "pearl": "PEARL MASK\n",
        },
        "anchors": {
            "jade-body": "cabinet/a/anchor.bin",
            "silt-body": "cabinet/b/ledger.bin",
            "pearl-body": "cabinet/c/core.bin",
        },
        "plan": [
            {"path": "cabinet/a/anchor.bin", "kind": "file", "body_id": "jade-body", "face_id": "jade", "target": "-"},
            {"path": "cabinet/a/twin.bin", "kind": "file", "body_id": "jade-body", "face_id": "jade", "target": "-"},
            {"path": "cabinet/b/ledger.bin", "kind": "file", "body_id": "silt-body", "face_id": "silt", "target": "-"},
            {"path": "cabinet/c/core.bin", "kind": "file", "body_id": "pearl-body", "face_id": "pearl", "target": "-"},
            {"path": "cabinet/c/echo.bin", "kind": "file", "body_id": "pearl-body", "face_id": "pearl", "target": "-"},
            {"path": "threads/jade-link", "kind": "symlink", "body_id": "-", "face_id": "-", "target": "../cabinet/a/twin.bin"},
        ],
        "initial": [
            {"kind": "file", "path": "cabinet/a/anchor.bin", "content": "old jade\n"},
            {"kind": "file", "path": "cabinet/b/ledger.bin", "content": "old silt\n"},
            {"kind": "file", "path": "cabinet/c/core.bin", "content": "old pearl\n"},
            {"kind": "hardlink", "path": "cabinet/c/stale-pearl.bin", "to": "cabinet/c/core.bin"},
            {"kind": "hardlink", "path": "trash/shared-with-jade.bin", "to": "cabinet/a/anchor.bin"},
            {"kind": "dir", "path": "cabinet/c/echo.bin"},
            {"kind": "file", "path": "cabinet/c/echo.bin/old.txt", "content": "remove tree\n"},
            {"kind": "dir", "path": "unused/deep/room"},
            {"kind": "file", "path": "unused/deep/room/note.txt", "content": "remove me\n"},
            {"kind": "symlink", "path": "threads/jade-link", "target": "../wrong/path.bin"},
        ],
    },
    "idempotent_on_second_run": {
        "faces": {
            "salt": "SALT FACE\n",
            "ash": "ASH FACE\n",
        },
        "anchors": {
            "salt-body": "tier1/anchor.txt",
            "ash-body": "tier2/core.txt",
        },
        "plan": [
            {"path": "tier2/core.txt", "kind": "file", "body_id": "ash-body", "face_id": "ash", "target": "-"},
            {"path": "tier2/echo.txt", "kind": "file", "body_id": "ash-body", "face_id": "ash", "target": "-"},
            {"path": "tier1/anchor.txt", "kind": "file", "body_id": "salt-body", "face_id": "salt", "target": "-"},
            {"path": "markers/up", "kind": "symlink", "body_id": "-", "face_id": "-", "target": "../tier1/anchor.txt"},
        ],
        "initial": [
            {"kind": "file", "path": "tier1/anchor.txt", "content": "old salt\n"},
            {"kind": "file", "path": "tier2/core.txt", "content": "old ash\n"},
            {"kind": "file", "path": "markers/up", "content": "wrong type\n"},
            {"kind": "file", "path": "tier2/old.txt", "content": "extra\n"},
        ],
    },
}


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def materialize_job(base_dir, blueprint):
    job_dir = base_dir / "job"
    faces_dir = job_dir / "faces"
    gallery_dir = job_dir / "gallery"
    faces_dir.mkdir(parents=True)
    gallery_dir.mkdir()

    for face_id, content in blueprint["faces"].items():
        write_text(faces_dir / f"{face_id}.txt", content)

    for entry in blueprint["initial"]:
        kind = entry["kind"]
        path = gallery_dir / entry["path"]
        if kind == "dir":
            path.mkdir(parents=True, exist_ok=True)
        elif kind == "file":
            write_text(path, entry["content"])
        elif kind == "hardlink":
            path.parent.mkdir(parents=True, exist_ok=True)
            os.link(gallery_dir / entry["to"], path)
        elif kind == "symlink":
            path.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(entry["target"], path)
        else:
            raise ValueError(f"unknown fixture kind: {kind}")

    anchors_lines = ["body_id\tanchor_path"]
    for body_id, anchor_path in blueprint["anchors"].items():
        anchors_lines.append(f"{body_id}\t{anchor_path}")
    (job_dir / "anchors.tsv").write_text("\n".join(anchors_lines) + "\n", encoding="utf-8")

    plan_lines = ["path\tkind\tbody_id\tface_id\ttarget"]
    for row in blueprint["plan"]:
        plan_lines.append("\t".join([row["path"], row["kind"], row["body_id"], row["face_id"], row["target"]]))
    (job_dir / "plan.tsv").write_text("\n".join(plan_lines) + "\n", encoding="utf-8")
    return job_dir


def required_dirs(blueprint):
    dirs = set()
    for row in blueprint["plan"]:
        parent = Path(row["path"]).parent
        while parent != Path("."):
            dirs.add(str(parent))
            parent = parent.parent
    return dirs


def expected_report_text(blueprint):
    groups = {}
    for body_id in sorted(blueprint["anchors"]):
        members = sorted(row["path"] for row in blueprint["plan"] if row["kind"] == "file" and row["body_id"] == body_id)
        if members:
            groups[body_id] = members
    report = {
        "anchors_preserved": sorted(blueprint["anchors"]),
        "hardlink_groups": groups,
        "symlinks": sum(1 for row in blueprint["plan"] if row["kind"] == "symlink"),
        "regular_files": sum(1 for row in blueprint["plan"] if row["kind"] == "file"),
    }
    return json.dumps(report, indent=2) + "\n"


def run_program(job_dir, report_path):
    subprocess.run(
        [sys.executable, str(PROGRAM), str(job_dir), str(report_path)],
        cwd=ROOT,
        check=True,
    )


def list_gallery_paths(gallery_dir):
    file_paths = set()
    dir_paths = set()
    for root, dirs, files in os.walk(gallery_dir):
        root_path = Path(root)
        rel_root = root_path.relative_to(gallery_dir)
        if rel_root != Path("."):
            dir_paths.add(str(rel_root))
        for name in dirs:
            rel_dir = root_path.joinpath(name).relative_to(gallery_dir)
            dir_paths.add(str(rel_dir))
        for name in files:
            rel_file = root_path.joinpath(name).relative_to(gallery_dir)
            file_paths.add(str(rel_file))
    return file_paths, dir_paths


def verify_blueprint(job_dir, blueprint, report_path, original_anchor_inodes):
    gallery_dir = job_dir / "gallery"
    expected_report = expected_report_text(blueprint)
    assert report_path.read_text(encoding="utf-8") == expected_report

    expected_paths = {row["path"] for row in blueprint["plan"]}
    actual_paths, actual_dirs = list_gallery_paths(gallery_dir)
    assert actual_paths == expected_paths
    assert actual_dirs == required_dirs(blueprint)

    body_inodes = {}
    for body_id, anchor_path in blueprint["anchors"].items():
        anchor_abs = gallery_dir / anchor_path
        st = anchor_abs.stat()
        assert stat.S_ISREG(st.st_mode)
        assert st.st_ino == original_anchor_inodes[body_id]
        body_inodes[body_id] = st.st_ino

    for row in blueprint["plan"]:
        abs_path = gallery_dir / row["path"]
        if row["kind"] == "file":
            st = abs_path.stat()
            assert stat.S_ISREG(st.st_mode)
            assert st.st_ino == body_inodes[row["body_id"]]
            assert abs_path.read_text(encoding="utf-8") == blueprint["faces"][row["face_id"]]
        else:
            st = os.lstat(abs_path)
            assert stat.S_ISLNK(st.st_mode)
            assert os.readlink(abs_path) == row["target"]

    distinct_body_inodes = {body_inodes[body_id] for body_id in blueprint["anchors"]}
    assert len(distinct_body_inodes) == len(blueprint["anchors"])

    for body_id in blueprint["anchors"]:
        members = [row["path"] for row in blueprint["plan"] if row["kind"] == "file" and row["body_id"] == body_id]
        if members:
            link_count = (gallery_dir / members[0]).stat().st_nlink
            assert link_count == len(members)


def prepare_and_run(case_name, tmp_path):
    blueprint = BLUEPRINTS[case_name]
    job_dir = materialize_job(tmp_path / case_name, blueprint)
    original_anchor_inodes = {
        body_id: (job_dir / "gallery" / anchor_path).stat().st_ino
        for body_id, anchor_path in blueprint["anchors"].items()
    }
    report_path = tmp_path / f"{case_name}-report.json"
    run_program(job_dir, report_path)
    verify_blueprint(job_dir, blueprint, report_path, original_anchor_inodes)
    return job_dir, blueprint, report_path, original_anchor_inodes


def test_sample_job_contract(tmp_path):
    prepare_and_run("sample_job", tmp_path)


def test_literal_symlink_targets_and_type_replacement(tmp_path):
    prepare_and_run("literal_targets_and_type_replacement", tmp_path)


def test_prunes_extra_dirs_and_breaks_wrong_aliases(tmp_path):
    prepare_and_run("prunes_extra_dirs_and_breaks_wrong_aliases", tmp_path)


def test_second_run_is_stable(tmp_path):
    job_dir, blueprint, report_path, original_anchor_inodes = prepare_and_run("idempotent_on_second_run", tmp_path)
    second_report = tmp_path / "second-report.json"
    run_program(job_dir, second_report)
    verify_blueprint(job_dir, blueprint, second_report, original_anchor_inodes)
    assert report_path.read_text(encoding="utf-8") == second_report.read_text(encoding="utf-8")

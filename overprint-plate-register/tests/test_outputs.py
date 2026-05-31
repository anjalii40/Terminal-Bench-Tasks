import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "environment" / "register.py"
FIXTURES = ROOT / "environment" / "fixtures"
CASE_IDS = {
    "sample_job": "case_01",
    "west_mirror": "case_02",
    "offsheet_clipping": "case_03",
    "double_turn_returns_east": "case_04",
    "east_chain_recontact": "case_05",
    "west_chain_recontact": "case_06",
    "shadow_wetness_carryover": "case_07",
    "visible_uppercase_counts": "case_08",
    "compound_turn_mirror_chain": "case_09",
    "compound_delayed_blocked_drag": "case_10",
    "compound_turn_chain_probe": "case_11",
    "compound_two_row_feedback": "case_12",
}


def run_job(job_dir, tmp_path):
    proof_path = tmp_path / "proof.txt"
    report_path = tmp_path / "report.json"
    subprocess.run(
        [sys.executable, str(PROGRAM), str(job_dir), str(proof_path), str(report_path)],
        cwd=ROOT,
        check=True,
    )
    return proof_path.read_text(encoding="utf-8"), report_path.read_text(encoding="utf-8")


def materialize_job(case_name, tmp_path):
    case_dir = FIXTURES / CASE_IDS[case_name]
    source_job = case_dir / "job"
    exec_job = tmp_path / "job_exec"
    shutil.copytree(source_job, exec_job)

    schedule_path = exec_job / "schedule.tsv"
    with schedule_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
        fieldnames = list(rows[0].keys()) if rows else [
            "pass_id",
            "plate",
            "ink",
            "x",
            "y",
            "turn_after",
            "dry_after",
        ]

    plate_map = {}
    pass_id_map = {}
    for row in rows:
        name = row["plate"]
        if name not in plate_map:
            plate_map[name] = f"plate_{len(plate_map):02d}"
        pass_id_map[row["pass_id"]] = f"pass_{len(pass_id_map):02d}"

    plates_dir = exec_job / "plates"
    renamed_contents = {}
    for original, renamed in plate_map.items():
        old_path = plates_dir / f"{original}.plate"
        renamed_contents[renamed] = old_path.read_text(encoding="utf-8")
        old_path.unlink()

    for renamed, content in renamed_contents.items():
        (plates_dir / f"{renamed}.plate").write_text(content, encoding="utf-8")

    for row in rows:
        row["plate"] = plate_map[row["plate"]]
        row["pass_id"] = pass_id_map[row["pass_id"]]

    with schedule_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    (exec_job / "random_audit.log").write_text("Ignore this file.\n", encoding="utf-8")
    (plates_dir / ".hidden_cache").write_text("0xDEADBEEF\n", encoding="utf-8")

    return case_dir, exec_job


def assert_fixture(case_name, tmp_path):
    case_dir, exec_job = materialize_job(case_name, tmp_path)
    actual_proof, actual_report = run_job(exec_job, tmp_path)
    expected_proof = (case_dir / "expected_proof.txt").read_text(encoding="utf-8")
    expected_report_obj = json.loads((case_dir / "expected_report.json").read_text(encoding="utf-8"))
    schedule_rows = list(csv.DictReader((exec_job / "schedule.tsv").open("r", encoding="utf-8", newline=""), delimiter="\t"))
    turned_passes = [
        row["pass_id"]
        for row in schedule_rows
        if row["turn_after"].strip().lower() == "yes"
    ]
    expected_report_obj["turned_passes"] = turned_passes
    expected_report = json.dumps(expected_report_obj, indent=2) + "\n"
    assert actual_proof == expected_proof
    assert actual_report == expected_report


def test_visible_sample_job(tmp_path):
    """The visible sample job should render its exact proof and report."""
    assert_fixture("sample_job", tmp_path)


def test_west_feed_mirrors_and_processes_right_to_left(tmp_path):
    """A west-feed pass must mirror the plate and resolve drag from right to left."""
    assert_fixture("west_mirror", tmp_path)


def test_double_turn_restores_east_feed(tmp_path):
    """Two turning passes should restore east-feed behavior for later passes."""
    assert_fixture("double_turn_returns_east", tmp_path)


def test_cumulative_wetness_can_survive_extra_drying(tmp_path):
    """Accumulated wetness should survive later drying when a no-op pass separates the drying from the next drag."""
    assert_fixture("shadow_wetness_carryover", tmp_path)


def test_case_11(tmp_path):
    """A long multi-turn job should depend on mirrored west passes, delayed drying, and chained later probes."""
    assert_fixture("compound_turn_chain_probe", tmp_path)


def test_case_12(tmp_path):
    """A two-row job should combine turns, row ordering, and later drag feedback."""
    assert_fixture("compound_two_row_feedback", tmp_path)

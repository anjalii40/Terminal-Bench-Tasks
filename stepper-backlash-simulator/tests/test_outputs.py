import json
import subprocess
from pathlib import Path

ENV_ROOT = Path("/environment")
TEST_ROOT = Path(__file__).resolve().parent
FIXTURE_ROOT = TEST_ROOT / "fixtures"
SOURCE = ENV_ROOT / "stepper.cpp"

FIXTURE_CASES = [
    "case_visible",
    "case_second_order_reversion",
    "case_interrupt_slew",
    "case_backlash_completion",
]

def compile_candidate(binary_path: Path) -> None:
    subprocess.run(
        ["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-o", str(binary_path), str(SOURCE)],
        check=True,
    )

def run_case(binary_path: Path, input_dir: Path, timeline_path: Path, report_path: Path) -> None:
    subprocess.run(
        [str(binary_path), str(input_dir), str(timeline_path), str(report_path)],
        check=True,
    )

def assert_case_matches(tmp_path: Path, input_dir: Path, expected_timeline: Path, expected_report: Path) -> None:
    binary_path = tmp_path / "stepper"
    timeline_path = tmp_path / "timeline.tsv"
    report_path = tmp_path / "report.json"
    
    compile_candidate(binary_path)
    run_case(binary_path, input_dir, timeline_path, report_path)
    
    assert timeline_path.read_text(encoding="utf-8") == expected_timeline.read_text(encoding="utf-8")
    assert json.loads(report_path.read_text(encoding="utf-8")) == json.loads(
        expected_report.read_text(encoding="utf-8")
    )

def test_fixture_inventory_is_present():
    """Checks that every verifier-owned fixture directory and expected output file is present under tests/fixtures."""
    for case_name in FIXTURE_CASES:
        case_dir = FIXTURE_ROOT / case_name
        assert case_dir.is_dir(), f"Missing fixture directory: {case_dir}"
        assert (case_dir / "expected_timeline.tsv").is_file(), f"Missing expected timeline: {case_dir}"
        assert (case_dir / "expected_report.json").is_file(), f"Missing expected report: {case_dir}"
        if case_name != "case_visible":
            assert (case_dir / "input" / "config.json").is_file(), f"Missing input config: {case_dir}"
            assert (case_dir / "input" / "commands.tsv").is_file(), f"Missing input commands: {case_dir}"

def test_visible_sample_outputs_match_exactly(tmp_path):
    """Checks the published sample job."""
    fixture = FIXTURE_ROOT / "case_visible"
    assert_case_matches(
        tmp_path,
        ENV_ROOT / "sample_job",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )

def test_second_order_reversion(tmp_path):
    """Checks that mid-backlash target flips correctly abort backlash if reverting to the historically engaged direction."""
    fixture = FIXTURE_ROOT / "case_second_order_reversion"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )

def test_interrupt_slew(tmp_path):
    """Checks that slews are strictly uninterruptible mid-step."""
    fixture = FIXTURE_ROOT / "case_interrupt_slew"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )

def test_backlash_completion(tmp_path):
    """Checks standard direction change mechanical backlash."""
    fixture = FIXTURE_ROOT / "case_backlash_completion"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )

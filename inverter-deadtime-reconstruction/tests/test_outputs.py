"""Strict verifier for inverter-deadtime-reconstruction.

All hidden expected files and hidden inputs used below are repository-backed files
under /tests/fixtures. They are verifier-side assets mounted with this test suite,
and are intentionally not copied into /environment.
"""

import json
import subprocess
from pathlib import Path


ENV_ROOT = Path("/environment")
TEST_ROOT = Path(__file__).resolve().parent
FIXTURE_ROOT = TEST_ROOT / "fixtures"
SOURCE = ENV_ROOT / "inverter.cpp"
FIXTURE_CASES = [
    "case_visible",
    "case_sign_flip",
    "case_restart_deadtime",
    "case_restart_reversion_block",
    "case_z_restart_history",
    "case_z_reversion_block",
    "case_z_committed_family",
    "case_zero_current_float",
    "case_three_phase_interaction",
    "case_same_commands_different_currents",
    "case_report_consistency",
    "case_long_trace",
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
    binary_path = tmp_path / "inverter"
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
            assert (case_dir / "input" / "currents.tsv").is_file(), f"Missing input currents: {case_dir}"


def test_visible_sample_outputs_match_exactly(tmp_path):
    """Checks the published sample job where dead-time expiry happens to coincide with immediate commitment."""
    fixture = FIXTURE_ROOT / "case_visible"
    assert_case_matches(
        tmp_path,
        ENV_ROOT / "sample_job",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_deadtime_diode_response_tracks_current_sign_and_delays_commit(tmp_path):
    """Checks that changing current signs inside one window can still leave the request armed after dead-time expires."""
    fixture = FIXTURE_ROOT / "case_sign_flip"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_overwritten_deadtime_restarts_keep_the_original_holding_rail(tmp_path):
    """Checks that a restart during active dead-time preserves the unresolved commutation context until commitment is allowed."""
    fixture = FIXTURE_ROOT / "case_restart_deadtime"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_mid_deadtime_reversion_keeps_blocking_against_the_original_outgoing_state(tmp_path):
    """Checks that a reversal during dead-time does not replace the original outgoing state used for post-dead-time blocking."""
    fixture = FIXTURE_ROOT / "case_restart_reversion_block"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_z_state_restart_still_uses_the_previously_established_command_family(tmp_path):
    """Checks that a restart after floating dead-time ticks still blocks commitment based on the earlier established command family."""
    fixture = FIXTURE_ROOT / "case_z_restart_history"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_post_deadtime_blocking_uses_the_established_command_family_not_the_latest_realized_node(tmp_path):
    """Checks that post-dead-time blocking follows the previously established command family rather than the most recent diode-clamped node."""
    fixture = FIXTURE_ROOT / "case_z_committed_family"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_z_heavy_reversion_still_blocks_on_the_original_outgoing_family(tmp_path):
    """Checks that long floating intervals before and after a restart do not erase which outgoing diode family still governs the block."""
    fixture = FIXTURE_ROOT / "case_z_reversion_block"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_zero_current_after_deadtime_allows_commit(tmp_path):
    """Checks that a zero-current tick does not sustain either rail and therefore allows an armed command to commit."""
    fixture = FIXTURE_ROOT / "case_zero_current_float"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_three_phase_line_voltage_matrix_uses_the_realized_nodes(tmp_path):
    """Checks that phase voltages reflect persistence-gated realized nodes rather than merely the newest requests."""
    fixture = FIXTURE_ROOT / "case_three_phase_interaction"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_same_commands_with_different_currents_change_commit_times(tmp_path):
    """Checks that identical commands can commit on different ticks when current history sustains different rails."""
    fixture = FIXTURE_ROOT / "case_same_commands_different_currents"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_report_counts_match_the_persistence_gated_timeline(tmp_path):
    """Checks the exact aggregate counters on a mixed trace containing delayed commits and direct transistor conduction."""
    fixture = FIXTURE_ROOT / "case_report_consistency"
    assert_case_matches(
        tmp_path,
        fixture / "input",
        fixture / "expected_timeline.tsv",
        fixture / "expected_report.json",
    )


def test_long_trace_and_rerun_are_deterministic(tmp_path):
    """Checks a longer mixed trace exactly and verifies that rerunning it produces identical files."""
    fixture = FIXTURE_ROOT / "case_long_trace"
    binary_path = tmp_path / "inverter"
    timeline_a = tmp_path / "timeline_a.tsv"
    timeline_b = tmp_path / "timeline_b.tsv"
    report_a = tmp_path / "report_a.json"
    report_b = tmp_path / "report_b.json"
    compile_candidate(binary_path)
    run_case(binary_path, fixture / "input", timeline_a, report_a)
    run_case(binary_path, fixture / "input", timeline_b, report_b)
    assert timeline_a.read_text(encoding="utf-8") == (fixture / "expected_timeline.tsv").read_text(encoding="utf-8")
    assert json.loads(report_a.read_text(encoding="utf-8")) == json.loads(
        (fixture / "expected_report.json").read_text(encoding="utf-8")
    )
    assert timeline_a.read_text(encoding="utf-8") == timeline_b.read_text(encoding="utf-8")
    assert report_a.read_text(encoding="utf-8") == report_b.read_text(encoding="utf-8")

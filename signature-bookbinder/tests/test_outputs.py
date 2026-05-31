import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "environment" / "bookbinder.py"
VISIBLE_PLAN = ROOT / "environment" / "visible_plan.json"


VISIBLE_EXPECTED = {
    "leaves": [
        {"signature": "cover", "leaf": 1, "panel": "cover-3", "recto": "C7", "verso": "C3", "tab": None},
        {"signature": "cover", "leaf": 2, "panel": "cover-4", "recto": "C4", "verso": "C8", "tab": "Moss"},
        {"signature": "cover", "leaf": 3, "panel": "cover-2", "recto": "C6", "verso": "C2", "tab": None},
        {"signature": "cover", "leaf": 4, "panel": "cover-1", "recto": "C1", "verso": "C5", "tab": "Bird"},
        {"signature": "index", "leaf": 1, "panel": "index-3", "recto": "I7", "verso": "I3", "tab": None},
        {"signature": "index", "leaf": 2, "panel": "index-1", "recto": "I1", "verso": "I5", "tab": None},
        {"signature": "index", "leaf": 3, "panel": "index-2", "recto": "I6", "verso": "I2", "tab": None},
        {"signature": "index", "leaf": 4, "panel": "index-4", "recto": "I4", "verso": "I8", "tab": None},
    ]
}

ADVERSARIAL_PLAN = {
    "fore_trim": 2,
    "binding_order": ["outer", "inner"],
    "signatures": [
        {
            "id": "outer",
            "folds": ["left-over-right", "top-over-bottom"],
            "grid": [
                [
                    {"panel": "outer-1", "front": "OF1", "back": "OB1", "tab": {"label": "Atlas", "edge": "east", "depth": 2}},
                    {"panel": "outer-2", "front": "OF2", "back": "OB2", "tab": {"label": "Birch", "edge": "west", "depth": 3}},
                ],
                [
                    {"panel": "outer-3", "front": "OF3", "back": "OB3", "tab": {"label": "Cairn", "edge": "north", "depth": 3}},
                    {"panel": "outer-4", "front": "OF4", "back": "OB4", "tab": None},
                ],
            ],
        },
        {
            "id": "inner",
            "folds": ["bottom-over-top", "right-over-left"],
            "grid": [
                [
                    {"panel": "inner-1", "front": "IF1", "back": "IB1", "tab": {"label": "Drift", "edge": "south", "depth": 1}},
                    {"panel": "inner-2", "front": "IF2", "back": "IB2", "tab": None},
                ],
                [
                    {"panel": "inner-3", "front": "IF3", "back": "IB3", "tab": {"label": "Ember", "edge": "east", "depth": 3}},
                    {"panel": "inner-4", "front": "IF4", "back": "IB4", "tab": {"label": "Fjord", "edge": "west", "depth": 0}},
                ],
            ],
        },
    ],
}

ADVERSARIAL_EXPECTED = {
    "leaves": [
        {"signature": "outer", "leaf": 1, "panel": "outer-2", "recto": "OB2", "verso": "OF2", "tab": None},
        {"signature": "outer", "leaf": 2, "panel": "outer-1", "recto": "OF1", "verso": "OB1", "tab": None},
        {"signature": "outer", "leaf": 3, "panel": "outer-3", "recto": "OB3", "verso": "OF3", "tab": None},
        {"signature": "outer", "leaf": 4, "panel": "outer-4", "recto": "OF4", "verso": "OB4", "tab": None},
        {"signature": "inner", "leaf": 1, "panel": "inner-2", "recto": "IB2", "verso": "IF2", "tab": None},
        {"signature": "inner", "leaf": 2, "panel": "inner-4", "recto": "IF4", "verso": "IB4", "tab": None},
        {"signature": "inner", "leaf": 3, "panel": "inner-3", "recto": "IB3", "verso": "IF3", "tab": "Ember"},
        {"signature": "inner", "leaf": 4, "panel": "inner-1", "recto": "IF1", "verso": "IB1", "tab": None},
    ]
}

CASE_C_PLAN = {
    "fore_trim": 0,
    "binding_order": ["solo"],
    "signatures": [
        {
            "id": "solo",
            "folds": ["left-over-right", "top-over-bottom"],
            "grid": [
                [
                    {"panel": "a", "front": "A1", "back": "A5", "tab": {"label": "Alpha", "edge": "east", "depth": 2}},
                    {"panel": "b", "front": "A2", "back": "A6", "tab": None},
                ],
                [
                    {"panel": "c", "front": "A3", "back": "A7", "tab": {"label": "Gamma", "edge": "north", "depth": 1}},
                    {"panel": "d", "front": "A4", "back": "A8", "tab": None},
                ],
            ],
        }
    ],
}

CASE_C_EXPECTED = {
    "leaves": [
        {"signature": "solo", "leaf": 1, "panel": "b", "recto": "A6", "verso": "A2", "tab": None},
        {"signature": "solo", "leaf": 2, "panel": "a", "recto": "A1", "verso": "A5", "tab": None},
        {"signature": "solo", "leaf": 3, "panel": "c", "recto": "A7", "verso": "A3", "tab": None},
        {"signature": "solo", "leaf": 4, "panel": "d", "recto": "A4", "verso": "A8", "tab": None},
    ]
}

CASE_D_PLAN = {
    "fore_trim": 1,
    "binding_order": ["solo"],
    "signatures": [
        {
            "id": "solo",
            "folds": ["bottom-over-top", "right-over-left"],
            "grid": [
                [
                    {"panel": "p", "front": "P1", "back": "P5", "tab": {"label": "Pine", "edge": "south", "depth": 2}},
                    {"panel": "q", "front": "P2", "back": "P6", "tab": None},
                ],
                [
                    {"panel": "r", "front": "P3", "back": "P7", "tab": None},
                    {"panel": "s", "front": "P4", "back": "P8", "tab": {"label": "Spruce", "edge": "west", "depth": 3}},
                ],
            ],
        }
    ],
}

CASE_D_EXPECTED = {
    "leaves": [
        {"signature": "solo", "leaf": 1, "panel": "q", "recto": "P6", "verso": "P2", "tab": None},
        {"signature": "solo", "leaf": 2, "panel": "s", "recto": "P4", "verso": "P8", "tab": "Spruce"},
        {"signature": "solo", "leaf": 3, "panel": "r", "recto": "P7", "verso": "P3", "tab": None},
        {"signature": "solo", "leaf": 4, "panel": "p", "recto": "P1", "verso": "P5", "tab": None},
    ]
}

CASE_E_PLAN = {
    "fore_trim": 0,
    "binding_order": ["second", "first"],
    "signatures": [
        {
            "id": "first",
            "folds": ["top-over-bottom", "left-over-right"],
            "grid": [
                [
                    {"panel": "f1", "front": "F1", "back": "F5", "tab": None},
                    {"panel": "f2", "front": "F2", "back": "F6", "tab": None},
                ],
                [
                    {"panel": "f3", "front": "F3", "back": "F7", "tab": {"label": "FirstTab", "edge": "east", "depth": 1}},
                    {"panel": "f4", "front": "F4", "back": "F8", "tab": None},
                ],
            ],
        },
        {
            "id": "second",
            "folds": ["right-over-left", "bottom-over-top"],
            "grid": [
                [
                    {"panel": "s1", "front": "S1", "back": "S5", "tab": None},
                    {"panel": "s2", "front": "S2", "back": "S6", "tab": {"label": "SecondTab", "edge": "east", "depth": 2}},
                ],
                [
                    {"panel": "s3", "front": "S3", "back": "S7", "tab": None},
                    {"panel": "s4", "front": "S4", "back": "S8", "tab": None},
                ],
            ],
        },
    ],
}

CASE_E_EXPECTED = {
    "leaves": [
        {"signature": "second", "leaf": 1, "panel": "s3", "recto": "S7", "verso": "S3", "tab": None},
        {"signature": "second", "leaf": 2, "panel": "s4", "recto": "S4", "verso": "S8", "tab": None},
        {"signature": "second", "leaf": 3, "panel": "s2", "recto": "S6", "verso": "S2", "tab": None},
        {"signature": "second", "leaf": 4, "panel": "s1", "recto": "S1", "verso": "S5", "tab": None},
        {"signature": "first", "leaf": 1, "panel": "f3", "recto": "F7", "verso": "F3", "tab": None},
        {"signature": "first", "leaf": 2, "panel": "f1", "recto": "F1", "verso": "F5", "tab": None},
        {"signature": "first", "leaf": 3, "panel": "f2", "recto": "F6", "verso": "F2", "tab": None},
        {"signature": "first", "leaf": 4, "panel": "f4", "recto": "F4", "verso": "F8", "tab": None},
    ]
}

CASE_F_PLAN = {
    "fore_trim": 2,
    "binding_order": ["trim"],
    "signatures": [
        {
            "id": "trim",
            "folds": ["left-over-right", "bottom-over-top"],
            "grid": [
                [
                    {"panel": "t1", "front": "T1", "back": "T5", "tab": {"label": "HideMe", "edge": "east", "depth": 2}},
                    {"panel": "t2", "front": "T2", "back": "T6", "tab": None},
                ],
                [
                    {"panel": "t3", "front": "T3", "back": "T7", "tab": {"label": "ShowMe", "edge": "west", "depth": 3}},
                    {"panel": "t4", "front": "T4", "back": "T8", "tab": None},
                ],
            ],
        }
    ],
}

CASE_F_EXPECTED = {
    "leaves": [
        {"signature": "trim", "leaf": 1, "panel": "t4", "recto": "T8", "verso": "T4", "tab": None},
        {"signature": "trim", "leaf": 2, "panel": "t3", "recto": "T3", "verso": "T7", "tab": "ShowMe"},
        {"signature": "trim", "leaf": 3, "panel": "t1", "recto": "T5", "verso": "T1", "tab": None},
        {"signature": "trim", "leaf": 4, "panel": "t2", "recto": "T2", "verso": "T6", "tab": None},
    ]
}


def run_candidate(plan, tmp_path):
    plan_path = tmp_path / "plan.json"
    output_path = tmp_path / "output.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    subprocess.run(
        [sys.executable, str(PROGRAM), str(plan_path), str(output_path)],
        cwd=ROOT,
        check=True,
    )
    return json.loads(output_path.read_text(encoding="utf-8"))


def test_visible_sample_output(tmp_path):
    """Checks the published sample plan and the exact leaf ordering it must produce."""
    plan = json.loads(VISIBLE_PLAN.read_text(encoding="utf-8"))
    assert run_candidate(plan, tmp_path) == VISIBLE_EXPECTED


def test_adversarial_fold_order_output(tmp_path):
    """Checks mixed fold directions and a surviving visible tab after two flips."""
    assert run_candidate(ADVERSARIAL_PLAN, tmp_path) == ADVERSARIAL_EXPECTED


def test_vertical_then_horizontal_signature(tmp_path):
    """Checks a single signature folded left-over-right then top-over-bottom."""
    assert run_candidate(CASE_C_PLAN, tmp_path) == CASE_C_EXPECTED


def test_horizontal_then_vertical_signature(tmp_path):
    """Checks a single signature folded bottom-over-top then right-over-left."""
    assert run_candidate(CASE_D_PLAN, tmp_path) == CASE_D_EXPECTED


def test_binding_order_across_signatures(tmp_path):
    """Checks that output signatures follow binding_order rather than source order."""
    assert run_candidate(CASE_E_PLAN, tmp_path) == CASE_E_EXPECTED


def test_trim_threshold_and_tab_labels(tmp_path):
    """Checks that tabs with depth equal to fore_trim disappear while deeper tabs emit their label strings."""
    assert run_candidate(CASE_F_PLAN, tmp_path) == CASE_F_EXPECTED

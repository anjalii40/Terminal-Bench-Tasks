#!/bin/sh
set -eu
cat > /environment/bookbinder.py <<'PY'
import json
import sys


VERTICAL_FOLDS = {"left-over-right", "right-over-left"}
HORIZONTAL_FOLDS = {"top-over-bottom", "bottom-over-top"}
VERTICAL_MIRROR = {
    "north": "north",
    "east": "west",
    "south": "south",
    "west": "east",
}
HORIZONTAL_MIRROR = {
    "north": "south",
    "east": "east",
    "south": "north",
    "west": "west",
}


def clone_panel(cell):
    tab = cell.get("tab")
    return {
        "panel": cell["panel"],
        "front": cell["front"],
        "back": cell["back"],
        "tab": None if tab is None else dict(tab),
        "flipped": False,
    }


def mirror_panel(panel, axis):
    copied = {
        "panel": panel["panel"],
        "front": panel["front"],
        "back": panel["back"],
        "tab": None if panel["tab"] is None else dict(panel["tab"]),
        "flipped": not panel["flipped"],
    }
    if copied["tab"] is not None:
        if axis == "vertical":
            copied["tab"]["edge"] = VERTICAL_MIRROR[copied["tab"]["edge"]]
        else:
            copied["tab"]["edge"] = HORIZONTAL_MIRROR[copied["tab"]["edge"]]
    return copied


def fold_vertical(grid, direction):
    if not grid or any(len(row) != 2 for row in grid):
        raise ValueError("vertical fold requires a two-column grid")
    result = []
    for row in range(len(grid)):
        if direction == "left-over-right":
            moved = grid[row][0]
            stay = grid[row][1]
        elif direction == "right-over-left":
            moved = grid[row][1]
            stay = grid[row][0]
        else:
            raise ValueError(f"unknown fold: {direction}")
        moved_stack = [mirror_panel(panel, "vertical") for panel in reversed(moved)]
        result.append([moved_stack + stay])
    return result


def fold_horizontal(grid, direction):
    if len(grid) != 2 or not grid[0] or len(grid[0]) != len(grid[1]):
        raise ValueError("horizontal fold requires a two-row grid")
    row = []
    for column in range(len(grid[0])):
        if direction == "top-over-bottom":
            moved = grid[0][column]
            stay = grid[1][column]
        elif direction == "bottom-over-top":
            moved = grid[1][column]
            stay = grid[0][column]
        else:
            raise ValueError(f"unknown fold: {direction}")
        moved_stack = [mirror_panel(panel, "horizontal") for panel in reversed(moved)]
        row.append(moved_stack + stay)
    return [row]


def fold_signature(signature):
    grid = [[[clone_panel(cell)] for cell in row] for row in signature["grid"]]
    folds = signature["folds"]
    if len(folds) != 2:
        raise ValueError("each signature must have exactly two folds")
    seen_vertical = False
    seen_horizontal = False
    for fold in folds:
        if fold in VERTICAL_FOLDS:
            seen_vertical = True
            grid = fold_vertical(grid, fold)
        elif fold in HORIZONTAL_FOLDS:
            seen_horizontal = True
            grid = fold_horizontal(grid, fold)
        else:
            raise ValueError(f"unsupported fold: {fold}")
    if not seen_vertical or not seen_horizontal:
        raise ValueError("each signature must contain one vertical and one horizontal fold")
    if len(grid) != 1 or len(grid[0]) != 1:
        raise ValueError("signature did not collapse to a stack")
    return grid[0][0]


def visible_tab(panel, fore_trim):
    tab = panel["tab"]
    if tab is None:
        return None
    if tab["edge"] != "east":
        return None
    if tab["depth"] <= fore_trim:
        return None
    return tab["label"]


def render_leaf(signature_id, index, panel, fore_trim):
    if panel["flipped"]:
        recto = panel["back"]
        verso = panel["front"]
    else:
        recto = panel["front"]
        verso = panel["back"]
    return {
        "signature": signature_id,
        "leaf": index,
        "panel": panel["panel"],
        "recto": recto,
        "verso": verso,
        "tab": visible_tab(panel, fore_trim),
    }


def simulate(plan):
    signature_map = {signature["id"]: signature for signature in plan["signatures"]}
    leaves = []
    for signature_id in plan["binding_order"]:
        stack = fold_signature(signature_map[signature_id])
        for index, panel in enumerate(stack, start=1):
            leaves.append(render_leaf(signature_id, index, panel, plan["fore_trim"]))
    return {"leaves": leaves}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python environment/bookbinder.py INPUT_JSON OUTPUT_JSON")
    with open(argv[1], "r", encoding="utf-8") as handle:
        plan = json.load(handle)
    result = simulate(plan)
    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main(sys.argv)
PY

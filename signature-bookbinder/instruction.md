# Signature Bookbinder

Repair or replace `environment/bookbinder.py`.

The program must keep its current command-line interface:

```text
python environment/bookbinder.py INPUT_JSON OUTPUT_JSON
```

`INPUT_JSON` contains a bookbinding plan with this structure:

- `fore_trim`: integer trim depth applied to the finished book.
- `binding_order`: signature ids from outermost to innermost.
- `signatures`: list of signature objects.

Each signature has:

- `id`: unique string.
- `folds`: exactly two folds, containing one vertical fold and one horizontal fold.
- `grid`: a 2x2 grid of panel objects.

Each panel object has:

- `panel`: unique id for that panel.
- `front`: label on the front face.
- `back`: label on the back face.
- `tab`: either `null` or an object with `label`, `edge`, and `depth`.

Allowed folds:

- Vertical: `left-over-right`, `right-over-left`
- Horizontal: `top-over-bottom`, `bottom-over-top`

Binding semantics:

1. A fold moves the named half onto the other half.
2. The moved half lands on top.
3. Every moved panel flips front/back.
4. The moved stack reverses as it lands.
5. Vertical folds mirror tab edges `east <-> west`.
6. Horizontal folds mirror tab edges `north <-> south`.

After both folds, each signature becomes a single stack. Read that stack from top to bottom.

For each leaf:

- `recto` is the face on top of that folded leaf.
- `verso` is the opposite face.
- `tab` is `null` when no tab is visible, otherwise it must be the visible tab's `label` string.
- a tab is visible only if its current edge is `east` and its `depth` is strictly greater than `fore_trim`.

Write `OUTPUT_JSON` in exactly this format:

```json
{
  "leaves": [
    {
      "signature": "cover",
      "leaf": 1,
      "panel": "cover-1",
      "recto": "C1",
      "verso": "C5",
      "tab": null
    }
  ]
}
```

`leaf` numbering restarts at `1` inside each signature. The final `leaves` list must follow `binding_order`.

Provided files:

- `environment/bookbinder.py`
- `environment/visible_plan.json`

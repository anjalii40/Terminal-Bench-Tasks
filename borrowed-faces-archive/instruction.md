# Borrowed-Faces Archive

Repair or replace `environment/archive.py`.

The program must keep this command-line interface:

```text
python environment/archive.py JOB_DIR REPORT_PATH
```

`JOB_DIR` contains:

- `faces/`
- `gallery/`
- `anchors.tsv`
- `plan.tsv`

The program must rewrite `gallery/` in place and then write `REPORT_PATH`.

## Input files

`faces/<face_id>.txt`

- Regular text files.
- The exact bytes of each file are the required final bytes for every gallery file that uses that `face_id`.

`anchors.tsv`

- Tab-separated with required header:

```text
body_id	anchor_path
```

- `anchor_path` is relative to `gallery/`.
- Every listed anchor path exists as a regular file before the program runs.
- Record the original inode of each listed anchor path before making changes.

`plan.tsv`

- Tab-separated with required header:

```text
path	kind	body_id	face_id	target
```

- `path` is relative to `gallery/`.
- `kind` is `file` or `symlink`.
- For `file` rows:
  - `body_id` and `face_id` are non-empty.
  - `target` is `-`.
- For `symlink` rows:
  - `body_id` and `face_id` are `-`.
  - `target` is the exact symlink text to store.

You may assume:

- all paths are safe relative paths with no `..`
- every `body_id` in `plan.tsv` appears exactly once in `anchors.tsv`
- all `file` rows for the same `body_id` use the same `face_id`

## Final gallery rules

After the program finishes:

- `gallery/` must contain exactly the planned file and symlink paths, plus only the parent directories required to hold them
- every path from a `file` row must be a regular file
- every path from a `symlink` row must be a symlink with exactly the stored `target` text from `plan.tsv`
- all file rows with the same `body_id` must be hardlinks to one another
- that shared inode must be the original inode of the corresponding anchor path from `anchors.tsv`
- the anchor path itself must still exist at the same path and still carry that original inode
- the bytes of every file row must exactly equal `faces/<face_id>.txt`
- extra files, symlinks, and directories not required by the plan must be removed

Important:

- Preserving an anchor inode means you must not replace that anchor with a new file.
- Writing new bytes through an anchor path is allowed if the inode stays the same.
- Symlink targets are checked literally. Do not normalize them.

## Output report

Write `REPORT_PATH` as JSON with exactly these top-level keys, in exactly this order:

- `anchors_preserved`
- `hardlink_groups`
- `symlinks`
- `regular_files`

Rules:

- `anchors_preserved`: sorted `body_id` values whose anchor path still has its original inode
- `hardlink_groups`: object whose keys are sorted `body_id` values and whose values are lexicographically sorted planned file paths for that body
- `symlinks`: number of `symlink` rows in `plan.tsv`
- `regular_files`: number of `file` rows in `plan.tsv`

Write the JSON with indentation `2` and a trailing newline.

Provided in the container:

- `environment/archive.py`
- `environment/sample_job/`

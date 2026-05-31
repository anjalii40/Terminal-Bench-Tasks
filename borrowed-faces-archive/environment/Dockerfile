FROM python:3.10.14-slim

WORKDIR /

RUN pip install --no-cache-dir pytest==8.3.2

COPY archive.py /environment/

RUN python - <<'PY'
import os
from pathlib import Path

root = Path("/environment/sample_job")
faces = root / "faces"
gallery = root / "gallery"
faces.mkdir(parents=True, exist_ok=True)
gallery.mkdir(parents=True, exist_ok=True)

(faces / "amber.txt").write_text("AMBER FACE\nline two\n", encoding="utf-8")
(faces / "onyx.txt").write_text("ONYX FACE\n", encoding="utf-8")
(faces / "verdigris.txt").write_text("VERDIGRIS FACE\n", encoding="utf-8")

for rel, text in {
    "hall/north/anchor.txt": "wrong amber\n",
    "hall/south/ledger.txt": "wrong onyx\n",
    "vault/body.txt": "wrong verdigris\n",
}.items():
    path = gallery / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

os.link(gallery / "hall/north/anchor.txt", gallery / "hall/north/old-mask.txt")
(gallery / "hall/south/spare.txt").write_text("extra\n", encoding="utf-8")
(gallery / "notes").mkdir()
(gallery / "notes/ghost.txt").write_text("ghost\n", encoding="utf-8")
os.symlink("../hall/north/anchor.txt", gallery / "sign-post")

(root / "anchors.tsv").write_text(
    "body_id\tanchor_path\n"
    "amber\thall/north/anchor.txt\n"
    "onyx\thall/south/ledger.txt\n"
    "verdigris\tvault/body.txt\n",
    encoding="utf-8",
)

(root / "plan.tsv").write_text(
    "path\tkind\tbody_id\tface_id\ttarget\n"
    "hall/north/anchor.txt\tfile\tamber\tamber\t-\n"
    "hall/north/mask.txt\tfile\tamber\tamber\t-\n"
    "hall/south/ledger.txt\tfile\tonyx\tonyx\t-\n"
    "annex/borrowed.txt\tfile\tonyx\tonyx\t-\n"
    "vault/body.txt\tfile\tverdigris\tverdigris\t-\n"
    "signs/north-arrow\tsymlink\t-\t-\t../hall/north/anchor.txt\n"
    "signs/missing-arrow\tsymlink\t-\t-\t../missing/door.txt\n",
    encoding="utf-8",
)
PY

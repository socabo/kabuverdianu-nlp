"""Bring raw text into the corpus with provenance.

Raw files are never edited: ingestion reads them and appends records to
data/clean/pending.jsonl (monolingual) for the clean step to process.
"""

from __future__ import annotations

import csv
import datetime as _dt
import json
from pathlib import Path

from . import CLEAN_DIR, PARALLEL_DIR


def _today() -> str:
    return _dt.date.today().isoformat()


def _append_jsonl(path: Path, records: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return len(records)


def ingest_text(
    file: str | Path,
    *,
    source: str,
    lang: str = "kea",
    orth: str = "unknown",
    variant: str = "unknown",
    license_: str = "unknown",
    root: str | Path = ".",
) -> int:
    """Ingest a plain-text file: one record per non-empty line (clean step re-splits)."""
    lines = Path(file).read_text(encoding="utf-8", errors="replace").splitlines()
    records = [
        {
            "text": line.strip(),
            "lang": lang,
            "orth": orth,
            "variant": variant,
            "source": source,
            "license": license_,
            "date_collected": _today(),
        }
        for line in lines
        if line.strip()
    ]
    return _append_jsonl(Path(root) / CLEAN_DIR / "pending.jsonl", records)


def ingest_pairs(
    file: str | Path,
    *,
    source: str,
    src_lang: str = "kea",
    tgt_lang: str = "por",
    delimiter: str = "\t",
    license_: str = "unknown",
    root: str | Path = ".",
) -> int:
    """Ingest a delimited file of parallel pairs: src<delim>tgt per line."""
    records = []
    with Path(file).open(encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.reader(fh, delimiter=delimiter):
            if len(row) < 2 or not row[0].strip() or not row[1].strip():
                continue
            records.append(
                {
                    "src": row[0].strip(),
                    "src_lang": src_lang,
                    "tgt": row[1].strip(),
                    "tgt_lang": tgt_lang,
                    "source": source,
                    "license": license_,
                    "date_collected": _today(),
                }
            )
    return _append_jsonl(Path(root) / PARALLEL_DIR / "pending.jsonl", records)

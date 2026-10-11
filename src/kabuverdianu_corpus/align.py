"""Parallel-pair validation: cleaning both sides, length-ratio filter, dedup."""

from __future__ import annotations

import json
from pathlib import Path

from . import PARALLEL_DIR
from .clean import clean_text, dedup_key, keep
from .normalize import tag_record

# Sentence pairs whose length ratio is extreme are usually misaligned.
MAX_LEN_RATIO = 3.0


def pair_ok(src: str, tgt: str) -> bool:
    if not (keep(src) and keep(tgt)):
        return False
    ratio = max(len(src), len(tgt)) / max(1, min(len(src), len(tgt)))
    return ratio <= MAX_LEN_RATIO


def process_pending(root: str | Path = ".") -> tuple[int, int]:
    """Process data/parallel/pending.jsonl into data/parallel/pairs.jsonl."""
    par_dir = Path(root) / PARALLEL_DIR
    pending = par_dir / "pending.jsonl"
    out = par_dir / "pairs.jsonl"
    if not pending.exists():
        return (0, 0)

    seen: set[tuple[str, str]] = set()
    if out.exists():
        with out.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                    seen.add((dedup_key(rec["src"]), dedup_key(rec["tgt"])))
                except (json.JSONDecodeError, KeyError):
                    continue

    kept = dropped = 0
    with pending.open(encoding="utf-8") as fin, out.open("a", encoding="utf-8") as fout:
        for line in fin:
            try:
                rec = json.loads(line)
                src, tgt = clean_text(rec["src"]), clean_text(rec["tgt"])
            except (json.JSONDecodeError, KeyError):
                dropped += 1
                continue
            key = (dedup_key(src), dedup_key(tgt))
            if not pair_ok(src, tgt) or key in seen:
                dropped += 1
                continue
            seen.add(key)
            rec.update(src=src, tgt=tgt)
            fout.write(json.dumps(tag_record(rec), ensure_ascii=False) + "\n")
            kept += 1

    pending.unlink()
    return (kept, dropped)

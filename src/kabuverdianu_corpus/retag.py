"""Source-level retagging: apply human knowledge of a source to all its records.

Variant (and orthography) are usually properties of a whole source — a song, a
publication — rather than of individual lines, and a native speaker's judgment
beats the per-line heuristics in normalize.py. `retag` stamps every record from
a given source in the corpus files, overriding whatever was guessed.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import CLEAN_DIR, ORTHOGRAPHIES, PARALLEL_DIR, VARIANTS


def retag_source(
    source: str,
    *,
    variant: str | None = None,
    orth: str | None = None,
    root: str | Path = ".",
) -> dict[str, int]:
    """Set variant and/or orth on every record whose source matches.

    Returns {file: records retagged}. Raises ValueError on unknown tag values.
    Run `export` afterwards to refresh the split files.
    """
    if variant is None and orth is None:
        raise ValueError("nothing to retag: pass variant and/or orth")
    if variant is not None and variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}; choose from {VARIANTS}")
    if orth is not None and orth not in ORTHOGRAPHIES:
        raise ValueError(f"unknown orth {orth!r}; choose from {ORTHOGRAPHIES}")

    counts: dict[str, int] = {}
    root = Path(root)
    for rel in (f"{CLEAN_DIR}/sentences.jsonl", f"{PARALLEL_DIR}/pairs.jsonl"):
        path = root / rel
        if not path.exists():
            continue
        records, n = [], 0
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("source") == source:
                    if variant is not None:
                        rec["variant"] = variant
                    if orth is not None:
                        rec["orth"] = orth
                    n += 1
                records.append(rec)
        tmp = path.with_suffix(".jsonl.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        tmp.replace(path)
        counts[rel] = n
    return counts

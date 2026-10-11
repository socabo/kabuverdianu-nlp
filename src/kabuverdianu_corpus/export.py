"""Export train/dev/test splits ready for NLLB fine-tuning.

Splits are deterministic (hash of the source text), so re-running export after
adding data never moves an old sentence between splits — important to avoid
test-set leakage across versions. Evaluate the final model on FLORES-200
(kea_Latn) as the external benchmark; the dev/test here are for iteration only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import CLEAN_DIR, EXPORTS_DIR, PARALLEL_DIR

DEV_PCT = 2
TEST_PCT = 2


def _split_of(text: str) -> str:
    h = int(hashlib.sha1(text.encode("utf-8")).hexdigest(), 16) % 100
    if h < TEST_PCT:
        return "test"
    if h < TEST_PCT + DEV_PCT:
        return "dev"
    return "train"


def export(root: str | Path = ".") -> dict[str, int]:
    root = Path(root)
    out_dir = root / EXPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    jobs = [
        (root / PARALLEL_DIR / "pairs.jsonl", "parallel", "src"),
        (root / CLEAN_DIR / "sentences.jsonl", "mono", "text"),
    ]
    for src_file, prefix, key_field in jobs:
        if not src_file.exists():
            continue
        handles = {
            s: (out_dir / f"{prefix}.{s}.jsonl").open("w", encoding="utf-8")
            for s in ("train", "dev", "test")
        }
        try:
            with src_file.open(encoding="utf-8") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                        split = _split_of(rec[key_field])
                    except (json.JSONDecodeError, KeyError):
                        continue
                    handles[split].write(json.dumps(rec, ensure_ascii=False) + "\n")
                    counts[f"{prefix}.{split}"] = counts.get(f"{prefix}.{split}", 0) + 1
        finally:
            for fh in handles.values():
                fh.close()
    return counts

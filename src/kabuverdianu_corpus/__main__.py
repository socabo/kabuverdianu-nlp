"""CLI: python -m kabuverdianu_corpus <command> [...]"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import CLEAN_DIR, PARALLEL_DIR
from .align import process_pending
from .clean import clean_pending
from .export import export
from .ingest import ingest_pairs, ingest_text
from .retag import retag_source


def _count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="kabuverdianu-nlp")
    p.add_argument("--root", default=".", help="pipeline root (contains data/)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("ingest", help="ingest a monolingual text file")
    s.add_argument("file")
    s.add_argument("--source", required=True, help="provenance label, e.g. lyrics/sodade")
    s.add_argument("--lang", default="kea")
    s.add_argument("--orth", default="unknown")
    s.add_argument("--variant", default="unknown")
    s.add_argument("--license", default="unknown")

    s = sub.add_parser("pairs", help="ingest a TSV/CSV of parallel pairs")
    s.add_argument("file")
    s.add_argument("--source", required=True)
    s.add_argument("--src-lang", default="kea")
    s.add_argument("--tgt-lang", default="por")
    s.add_argument("--delimiter", default="\t")
    s.add_argument("--license", default="unknown")

    s = sub.add_parser("retag", help="set variant/orth on all records from one source")
    s.add_argument("--source", required=True, help="exact source label to retag")
    s.add_argument("--variant", help="santiago | saovicente | other | unknown")
    s.add_argument("--orth", help="alupec | pt-based | mixed | unknown")

    sub.add_parser("clean", help="process pending monolingual + parallel data")
    sub.add_parser("export", help="write train/dev/test JSONL splits")
    sub.add_parser("stats", help="show corpus sizes")

    a = p.parse_args(argv)
    root = a.root

    if a.cmd == "ingest":
        n = ingest_text(a.file, source=a.source, lang=a.lang, orth=a.orth,
                        variant=a.variant, license_=a.license, root=root)
        print(f"ingested {n} lines from {a.file}")
    elif a.cmd == "pairs":
        n = ingest_pairs(a.file, source=a.source, src_lang=a.src_lang,
                         tgt_lang=a.tgt_lang, delimiter=a.delimiter,
                         license_=a.license, root=root)
        print(f"ingested {n} pairs from {a.file}")
    elif a.cmd == "retag":
        counts = retag_source(a.source, variant=a.variant, orth=a.orth, root=root)
        total = sum(counts.values())
        for rel, n in counts.items():
            print(f"{rel}: retagged {n}")
        if total:
            print("run `export` to refresh the split files")
        else:
            print(f"no records found with source {a.source!r}")
    elif a.cmd == "clean":
        k1, d1 = clean_pending(root)
        k2, d2 = process_pending(root)
        print(f"monolingual: kept {k1}, dropped {d1}; parallel: kept {k2}, dropped {d2}")
    elif a.cmd == "export":
        print(json.dumps(export(root), indent=2))
    elif a.cmd == "stats":
        print(f"monolingual sentences: {_count(Path(root) / CLEAN_DIR / 'sentences.jsonl')}")
        print(f"parallel pairs:        {_count(Path(root) / PARALLEL_DIR / 'pairs.jsonl')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Cleaning: unicode repair, boilerplate stripping, sentence splitting, dedup.

Uses only the standard library; `ftfy` (mojibake repair) is used when installed.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

try:
    import ftfy
except ImportError:  # keep the pipeline usable without ftfy installed
    ftfy = None

from . import CLEAN_DIR

# Sentence boundary: ., !, ?, … followed by space + capital/quote. Deliberately
# simple — Kriolu has no off-the-shelf sentence splitter; refine against real data.
_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÖØ-Þ\"'«])")
_WS = re.compile(r"\s+")
_URL = re.compile(r"https?://\S+|www\.\S+")
_NOISE = re.compile(r"[​‎‏﻿]")  # zero-width chars

MIN_CHARS = 3
MAX_CHARS = 1000
MIN_ALPHA_RATIO = 0.5  # drop lines that are mostly numbers/punctuation


def clean_text(text: str) -> str:
    """Normalize one string (NFC, mojibake repair, whitespace, zero-width chars)."""
    if ftfy is not None:
        text = ftfy.fix_text(text)
    text = unicodedata.normalize("NFC", text)
    text = _NOISE.sub("", text)
    text = _URL.sub(" ", text)
    return _WS.sub(" ", text).strip()


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def keep(sentence: str) -> bool:
    if not (MIN_CHARS <= len(sentence) <= MAX_CHARS):
        return False
    alpha = sum(ch.isalpha() for ch in sentence)
    return alpha / len(sentence) >= MIN_ALPHA_RATIO


def dedup_key(sentence: str) -> str:
    """Case/punctuation-insensitive key so near-duplicates collapse."""
    return "".join(ch for ch in sentence if ch.isalnum()).casefold()


def clean_pending(root: str | Path = ".") -> tuple[int, int]:
    """Process data/clean/pending.jsonl into data/clean/sentences.jsonl.

    Returns (kept, dropped). Dedup is global across the existing sentence file.
    """
    clean_dir = Path(root) / CLEAN_DIR
    pending = clean_dir / "pending.jsonl"
    out = clean_dir / "sentences.jsonl"
    if not pending.exists():
        return (0, 0)

    seen: set[str] = set()
    if out.exists():
        with out.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    seen.add(dedup_key(json.loads(line)["text"]))
                except (json.JSONDecodeError, KeyError):
                    continue

    kept = dropped = 0
    with pending.open(encoding="utf-8") as fin, out.open("a", encoding="utf-8") as fout:
        for line in fin:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                dropped += 1
                continue
            for sentence in split_sentences(clean_text(rec.get("text", ""))):
                key = dedup_key(sentence)
                if not keep(sentence) or key in seen:
                    dropped += 1
                    continue
                seen.add(key)
                fout.write(json.dumps({**rec, "text": sentence}, ensure_ascii=False) + "\n")
                kept += 1

    pending.unlink()
    return (kept, dropped)

"""Orthography handling for Kriolu.

Policy (see roadmap): keep text as found, TAG it, and keep normalization rules in
one reviewable place. The heuristics below only *guess* tags for untagged text;
the ALUPEC mapping table is a scaffold to fill in with a native-speaker reviewer
before enabling normalize().
"""

from __future__ import annotations

import re

# Portuguese-based spelling signals: letters/digraphs ALUPEC does not use.
_PT_SIGNALS = re.compile(r"ç|lh|nh(?!a\b)|qu|ã|õ|ou\b|ss", re.IGNORECASE)
# ALUPEC signals: k, y, w are regular letters; tx for the affricate.
_ALUPEC_SIGNALS = re.compile(r"\bk|k[aeiou]|tx|y[aeiou]|dj", re.IGNORECASE)

# São Vicente variant hints vs Santiago (badiu). Rough lexical markers — extend.
_SAOVICENTE_HINTS = re.compile(r"\b(bosê|ês\b|q'|d'|m'|t[eê]ve)\b", re.IGNORECASE)
_SANTIAGO_HINTS = re.compile(r"\b(nhos|dja\b|ki\b|kel\b|sta\b)\b", re.IGNORECASE)


def guess_orthography(text: str) -> str:
    pt = len(_PT_SIGNALS.findall(text))
    al = len(_ALUPEC_SIGNALS.findall(text))
    if pt and al:
        return "mixed"
    if al:
        return "alupec"
    if pt:
        return "pt-based"
    return "unknown"


def guess_variant(text: str) -> str:
    sv = len(_SAOVICENTE_HINTS.findall(text))
    st = len(_SANTIAGO_HINTS.findall(text))
    if st > sv:
        return "santiago"
    if sv > st:
        return "saovicente"
    return "unknown"


# --- ALUPEC normalization (SCAFFOLD — review with a native speaker) -----------
# Ordered (pattern, replacement) pairs applied to pt-based text. These are the
# standard correspondences; validate and extend before trusting the output.
ALUPEC_RULES: list[tuple[str, str]] = [
    (r"ç", "s"),
    (r"qu(?=[ei])", "k"),
    (r"\bc(?=[aou])", "k"),
    (r"ch", "tx"),
    (r"lh", "lh"),   # kept: ALUPEC uses lh too
    (r"nh", "nh"),   # kept: ALUPEC uses nh too
    (r"j(?=[aou])", "j"),
]


def normalize_to_alupec(text: str) -> str:
    """Apply ALUPEC_RULES. Only meaningful once the table has been reviewed."""
    for pattern, repl in ALUPEC_RULES:
        text = re.sub(pattern, repl, text)
        text = re.sub(pattern.upper(), repl.upper(), text)
    return text


def tag_record(rec: dict) -> dict:
    """Fill in orth/variant tags when they are 'unknown'."""
    text = rec.get("text") or rec.get("src") or ""
    if rec.get("orth", "unknown") == "unknown":
        rec["orth"] = guess_orthography(text)
    if rec.get("variant", "unknown") == "unknown":
        rec["variant"] = guess_variant(text)
    return rec

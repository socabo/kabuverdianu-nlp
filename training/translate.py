#!/usr/bin/env python
"""Translate with a (fine-tuned) NLLB model.

    python training/translate.py "N ta papia kriolu" --model models/nllb-kea-v1
    python training/translate.py --src por --tgt kea "Eu falo crioulo"
    echo "Bon dia" | python training/translate.py --model models/nllb-kea-v1

Defaults to kea -> por. Works with the stock facebook/nllb-200-distilled-600M
too, which gives you the pre-fine-tuning baseline to compare against.
"""

from __future__ import annotations

import argparse
import sys

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from finetune_nllb import NLLB_CODES


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="*", help="text to translate (or pipe via stdin)")
    ap.add_argument("--model", default="facebook/nllb-200-distilled-600M")
    ap.add_argument("--src", default="kea", choices=sorted(NLLB_CODES))
    ap.add_argument("--tgt", default="por", choices=sorted(NLLB_CODES))
    ap.add_argument("--max-length", type=int, default=256)
    args = ap.parse_args()

    lines = [" ".join(args.text)] if args.text else [l.strip() for l in sys.stdin if l.strip()]
    if not lines:
        raise SystemExit("nothing to translate")

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model)
    tokenizer.src_lang = NLLB_CODES[args.src]
    tgt_token_id = tokenizer.convert_tokens_to_ids(NLLB_CODES[args.tgt])

    for line in lines:
        inputs = tokenizer(line, return_tensors="pt", truncation=True,
                           max_length=args.max_length)
        out = model.generate(**inputs, forced_bos_token_id=tgt_token_id,
                             max_length=args.max_length, num_beams=5)
        print(tokenizer.batch_decode(out, skip_special_tokens=True)[0])


if __name__ == "__main__":
    main()

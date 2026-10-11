#!/usr/bin/env python
"""Fine-tune NLLB-200 on the exported Kriolu parallel corpus.

Input:  data/exports/parallel.train.jsonl / parallel.dev.jsonl
        (produced by `python -m kabuverdianu_corpus export`; records look like
        {"src": "...", "src_lang": "kea", "tgt": "...", "tgt_lang": "por", ...})
Output: a fine-tuned model directory usable with translate.py or transformers.

Requirements (GPU with ~16GB VRAM is enough for the 600M model):
    pip install "transformers>=4.40" datasets sacrebleu sentencepiece accelerate torch

Typical run (Kriolu -> Portuguese and reverse direction in the same model):
    python training/finetune_nllb.py \
        --train data/exports/parallel.train.jsonl \
        --dev   data/exports/parallel.dev.jsonl \
        --output models/nllb-kea-v1 --bidirectional

NLLB already knows Kabuverdianu as `kea_Latn`, so no new language token is
needed — fine-tuning sharpens it with your data. Evaluate the final model on
FLORES-200 `kea_Latn` for an externally comparable chrF/BLEU score.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from datasets import Dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

import sacrebleu

# ISO 639-3 -> NLLB (FLORES-200) language codes
NLLB_CODES = {
    "kea": "kea_Latn",  # Kabuverdianu
    "por": "por_Latn",
    "eng": "eng_Latn",
    "fra": "fra_Latn",
}

MAX_LEN = 256


def load_pairs(path: Path, bidirectional: bool) -> list[dict]:
    """Load pipeline JSONL into direction-explicit examples."""
    examples = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
                src, tgt = rec["src"], rec["tgt"]
                sl, tl = NLLB_CODES[rec["src_lang"]], NLLB_CODES[rec["tgt_lang"]]
            except (json.JSONDecodeError, KeyError):
                continue
            examples.append({"src": src, "tgt": tgt, "src_lang": sl, "tgt_lang": tl})
            if bidirectional:
                examples.append({"src": tgt, "tgt": src, "src_lang": tl, "tgt_lang": sl})
    return examples


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", type=Path, default=Path("data/exports/parallel.train.jsonl"))
    ap.add_argument("--dev", type=Path, default=Path("data/exports/parallel.dev.jsonl"))
    ap.add_argument("--output", type=Path, default=Path("models/nllb-kea-v1"))
    ap.add_argument("--base-model", default="facebook/nllb-200-distilled-600M")
    ap.add_argument("--bidirectional", action="store_true",
                    help="also train the reverse direction of every pair")
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--grad-accum", type=int, default=2)
    args = ap.parse_args()

    train_ex = load_pairs(args.train, args.bidirectional)
    dev_ex = load_pairs(args.dev, bidirectional=False) if args.dev.exists() else []
    if not train_ex:
        raise SystemExit(f"no training pairs found in {args.train} — run the corpus "
                         "pipeline (ingest/clean/export) first")
    print(f"train examples: {len(train_ex)}  dev examples: {len(dev_ex)}")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.base_model)

    def preprocess(batch):
        # NLLB conditions on source/target language via tokenizer attributes.
        input_ids, labels = [], []
        for src, tgt, sl, tl in zip(batch["src"], batch["tgt"],
                                    batch["src_lang"], batch["tgt_lang"]):
            tokenizer.src_lang = sl
            tokenizer.tgt_lang = tl
            enc = tokenizer(src, text_target=tgt, max_length=MAX_LEN, truncation=True)
            input_ids.append(enc["input_ids"])
            labels.append(enc["labels"])
        return {"input_ids": input_ids, "labels": labels}

    cols = ["src", "tgt", "src_lang", "tgt_lang"]
    train_ds = Dataset.from_list(train_ex).map(preprocess, batched=True, remove_columns=cols)
    dev_ds = (Dataset.from_list(dev_ex).map(preprocess, batched=True, remove_columns=cols)
              if dev_ex else None)

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        preds = np.where(preds != -100, preds, tokenizer.pad_token_id)
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        hyp = tokenizer.batch_decode(preds, skip_special_tokens=True)
        ref = tokenizer.batch_decode(labels, skip_special_tokens=True)
        return {
            "chrf": sacrebleu.corpus_chrf(hyp, [ref]).score,
            "bleu": sacrebleu.corpus_bleu(hyp, [ref]).score,
        }

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        warmup_ratio=0.03,
        weight_decay=0.01,
        fp16=True,
        logging_steps=50,
        eval_strategy="epoch" if dev_ds else "no",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=bool(dev_ds),
        metric_for_best_model="chrf",
        predict_with_generate=True,
        generation_max_length=MAX_LEN,
        report_to="none",
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=dev_ds,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
        compute_metrics=compute_metrics if dev_ds else None,
    )
    trainer.train()
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    print(f"saved fine-tuned model to {args.output}")


if __name__ == "__main__":
    main()

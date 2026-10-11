# Kabuverdianu NLP — Corpus Pipeline for Cape Verdean Creole

Corpus-collection pipeline and NLLB fine-tuning for **Kabuverdianu** (Cape Verdean
Creole — Kriolu/Krioulo, ISO 639-3 `kea`).

The pipeline takes raw text from anywhere (pasted files, scraped pages, lyric sheets,
Bible verses) through four stages:

```
ingest  →  clean  →  normalize  →  export
 raw/       clean/     (tags)       exports/   (JSONL ready for NLLB fine-tuning)
```

Parallel data (Kriolu ↔ Portuguese/English/French) flows through the same stages and
is paired in `data/parallel/`.

## Layout

```
kabuverdianu-nlp/
├── src/kabuverdianu_corpus/
│   ├── ingest.py      # bring raw text in (txt, csv/tsv pairs), record provenance
│   ├── clean.py       # unicode fixes, boilerplate strip, sentence split, dedup
│   ├── normalize.py   # orthography handling (ALUPEC policy) + variant tagging
│   ├── align.py       # build/validate parallel pairs, length-ratio filter
│   └── export.py      # train/dev/test JSONL for Hugging Face / NLLB fine-tuning
├── data/
│   ├── raw/           # as collected, never edited (one subfolder per source)
│   ├── clean/         # cleaned monolingual sentences (JSONL, one per line)
│   ├── parallel/      # aligned pairs (JSONL)
│   └── exports/       # final splits
└── tests/
```

## Record schema

Every sentence is a JSON object; provenance travels with the text:

```json
{"text": "N ta papia kriolu", "lang": "kea", "orth": "alupec", "variant": "santiago",
 "source": "lyrics/cesaria-evora", "license": "research-only", "date_collected": "2026-10-11"}
```

Parallel pairs add the other side:

```json
{"src": "N ta papia kriolu", "src_lang": "kea", "tgt": "Eu falo crioulo", "tgt_lang": "por",
 "source": "bible/almeida-vs-kriolu", "align_score": 0.91}
```

Fields `orth` (`alupec` | `pt-based` | `mixed` | `unknown`) and `variant`
(`santiago` | `saovicente` | `other` | `unknown`) implement the roadmap's
orthography policy: we keep text as found and **tag** it, so later you can train
on one convention or normalize in one place.

## Quick start

```bash
cd kabuverdianu-nlp
pip install -e .

# 1. Ingest a raw text file (monolingual Kriolu)
python -m kabuverdianu_corpus ingest data/raw/lyrics/sodade.txt --source lyrics/sodade --lang kea

# 2. Clean + sentence-split everything ingested
python -m kabuverdianu_corpus clean

# 3. Ingest a TSV of parallel pairs (kriolu<TAB>portuguese)
python -m kabuverdianu_corpus pairs data/raw/bible/gen1.tsv --source bible/gen1 --tgt-lang por

# 4. Export train/dev/test splits
python -m kabuverdianu_corpus export
```

## Fine-tuning (after collecting data)

`training/finetune_nllb.py` fine-tunes **NLLB-200-distilled-600M** on the exported
pairs (NLLB already knows Kabuverdianu as `kea_Latn`, so no new language token is
needed). Needs a GPU (~16GB VRAM) and `pip install -e ".[ml]" sacrebleu accelerate torch`.

```bash
python training/finetune_nllb.py --bidirectional --output models/nllb-kea-v1
python training/translate.py "N ta papia kriolu" --model models/nllb-kea-v1
python training/translate.py "N ta papia kriolu"   # stock NLLB = baseline to beat
```

Evaluate the result on FLORES-200 `kea_Latn` for an externally comparable score.

## Collection checklist (from the roadmap)

- [ ] Inventory existing `kea` data: FLORES-200 (`kea_Latn`), OPUS, Hugging Face
- [ ] Bible / JW.org parallel text
- [ ] Song lyrics (morna, funaná, coladeira) + their Portuguese translations
- [ ] News in Kriolu (A Nação, Expresso das Ilhas)
- [ ] Social-media / informal monolingual text
- [ ] Decide ALUPEC normalization rules in `normalize.py` with a native-speaker reviewer

**Licensing**: record the `license` field honestly at ingest time. Lyrics and news
are copyrighted — fine for research corpora in many jurisdictions, but check before
publishing a dataset publicly; prefer sources you can redistribute (Bible translations
with permissive terms, government text, crowdsourced contributions).

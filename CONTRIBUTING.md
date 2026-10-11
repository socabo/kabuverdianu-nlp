# Contributing to Kabuverdianu NLP

Obrigadu / thank you for your interest! This project builds open language
technology for **Kabuverdianu** (Cape Verdean Creole, ISO 639-3 `kea`). All
skill levels and all islands' variants are welcome — native speakers, diaspora,
linguists, and engineers alike.

## Ways to contribute

**No coding required:**
- **Text**: point us to (or contribute) Kriolu text we may legally use — lyrics
  with permission, your own writing, public documents. Open an issue describing
  the source and its license before any large contribution.
- **Translation pairs**: Kriolu ↔ Portuguese/English/French sentence pairs you
  wrote or verified yourself.
- **Review**: the ALUPEC normalization rules in
  `src/kabuverdianu_corpus/normalize.py` and the variant-detection hints need
  native-speaker review — this is one of the highest-value contributions.
- **Orthography/variant tagging**: checking that samples are tagged with the
  right convention (ALUPEC vs Portuguese-based) and variant (Santiago,
  São Vicente, …).

**Code:**
- Pipeline improvements (better sentence splitting for Kriolu, smarter
  alignment, new ingestors), training/evaluation work, tests.

## Ground rules for data

1. **Language purity**: only Kabuverdianu (`kea`). Guinea-Bissau Creole (`pov`)
   and other creoles are different languages — do not mix them in (see
   `docs/ROADMAP.md` for the *Nobu Testamentu* trap).
2. **Provenance always**: every record carries `source`, `license`, and
   `date_collected`. Contributions without a clear source/license cannot be
   merged.
3. **Respect copyright**: do not commit text you don't have the right to
   redistribute (this includes JW.org content and most news/lyrics). Raw corpus
   data stays out of git by design (`data/**/*.jsonl` is gitignored); only
   redistributable datasets will ever be published, separately and with their
   own license.
4. **Tag, don't rewrite**: keep text as found and tag its orthography/variant;
   normalization decisions happen in one reviewable place (`normalize.py`).

## Workflow

1. Fork, create a branch, make your change.
2. Run the test: `pip install -e ".[test]" && pytest tests/`.
3. For changes to cleaning/normalization rules, include before/after examples
   of real Kriolu sentences in the PR description.
4. Open a pull request. Small, focused PRs merge fastest.

## Licensing of contributions

Code contributions are licensed under the repository's [MIT License](LICENSE).
Text/data contributions must state their own license in the record's `license`
field; by contributing your own original text you agree to license it under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) unless you state
otherwise in the PR.

## Questions

Open a GitHub issue — questions about the language itself (ALUPEC, variants)
are as welcome as technical ones.

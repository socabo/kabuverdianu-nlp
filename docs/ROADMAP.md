# Building language technology for Cape Verdean Creole (Kriolu / Kabuverdianu)

> Reference note for the `africa-expert` agent. Context: after adding the transcript on Fongbé entering Google Traduction (`transcripts/tv-fongbe-google-traduction-benin.md`), the question was how to build something similar for Cape Verdean Creole. Status as of late 2026.

## Where Kriolu already stands

Unlike Fongbé in 2018, Cape Verdean Creole does not start from zero:

- **Google Translate** added Cape Verdean Creole in its June 2024 expansion (~110 new languages, PaLM 2-based). Quality is limited but it exists.
- **Meta NLLB-200** (open-source translation model) and the **FLORES-200** benchmark include Kabuverdianu, language code `kea_Latn`.
- ISO 639-3 code: `kea`.

So the goal is to *improve on weak baselines* — better translation, speech recognition, and digital presence — not to bootstrap from nothing.

## 1. Data is 90% of the work

The Fongbé team spent years on collection and annotation before any model. For Kriolu:

**Parallel text** (Kriolu ↔ Portuguese / English / French), in order of expected yield:
- **JW.org set to Kabuverdianu** — likely the single largest aligned source. Jehovah's Witnesses publish substantial Kriolu content whose Portuguese counterparts match paragraph-for-paragraph, which makes alignment nearly mechanical.
- **Bible portions** — smaller than usual: per Joshua Project, Kabuverdianu has only Bible *portions* (translated 1936–2021), **no complete New Testament or Bible**. What exists is aggregated at Scripture Earth (scriptureearth.org, code `kea`) as text PDFs and audio; align verse-by-verse against a public-domain Portuguese Bible (Almeida).
- Song lyrics — a major Kriolu asset (morna, funaná, coladeira; Cesária Évora's repertoire and beyond) with published Portuguese translations.
- News outlets when they publish in Kriolu (A Nação, Expresso das Ilhas), government and civic materials.
- Subtitled videos and film dialogue.

> **⚠️ Language trap**: the *Nobu Testamentu* sold as a "Crioulo" New Testament is
> **Guinea-Bissau Creole** (ISO `pov`) — a related but different language. Do not mix
> it into a `kea` corpus; if used at all, tag it as `pov`. Check the language of any
> "Crioulo" source (e.g. GospelGo's combined Cape Verde/Guinea-Bissau listing) before ingesting.

**Monolingual Kriolu text**: social media and WhatsApp-style informal writing, literature (e.g. Kaoberdiano Dambará), blogs, forums.

**Orthography policy — decide early.** This is Kriolu's special challenge:
- Text in the wild mixes **ALUPEC**, Portuguese-based spellings, and personal improvisations.
- There's a variant split: Santiago (badiu) vs São Vicente (kriol d'Soncent) and the other islands.
- Either normalize toward ALUPEC or tag each sample with its variant/orthography. Inconsistent spelling silently wrecks model quality.

## 2. Start from existing models, don't train from scratch

- **Translation**: fine-tune **NLLB-200** (the distilled 600M-parameter version runs on a single GPU) on collected Kriolu pairs, using Hugging Face `transformers` (~100 lines of code). A few thousand good sentence pairs already moves the needle; tens of thousands gets genuinely useful.
- **Speech** (crucial for a heavily oral language): fine-tune **Whisper** for Kriolu transcription using transcribed audio — radio archives, interviews. Propose Kriolu on **Mozilla Common Voice** and crowdsource voice recordings (the same playbook as Benin's « J'aime ma langue »).
- Check **OPUS** and **Hugging Face** for existing `kea` datasets before collecting anything — avoid duplicating work.

## 3. Plug into the community

- **Masakhane** — the grassroots African-NLP research network (the Fongbé work of Bonaventure Dossou grew in that orbit). Open participation, mentorship, shared tooling.
- Publish datasets and models on **Hugging Face** so others can build on them.
- The **Cape Verdean diaspora** (Boston/Brockton, Lisbon, Rotterdam, Paris, Dakar) is a real asset for crowdsourcing annotation, translation pairs, and voice data.
- Institutional allies: Universidade de Cabo Verde (Uni-CV), the IILP (Instituto Internacional da Língua Portuguesa, headquartered in Praia), and Cape Verde's ongoing efforts around officializing Kriolu.

### Masakhane integration path

1. **Intro post** in the Masakhane community channels (Slack/mailing list, join via masakhane.io): what the project is, what exists, where Kriolu speakers and researchers can help.
2. **Study existing benchmarks** in [masakhane-io/masakhane-mt](https://github.com/masakhane-io/masakhane-mt): how languages with similar problems (small corpora, orthography variation) prepared data, and the documentation conventions for dataset provenance and splits — mirror those conventions in our exports so a benchmark submission is trivial later.
3. **Contribute a `kea` benchmark PR** to masakhane-mt once a v1 corpus + fine-tuned model exists (Kabuverdianu appears to have no benchmark there yet): data-prep notebook, model results (chrF/BLEU on FLORES-200 `kea_Latn`), provenance documentation. This registers Kabuverdianu in the community's own language registry — the single highest-visibility step for attracting collaborators.
4. Note on tooling: masakhane-mt's starter notebooks are JoeyNMT-based (training from scratch); our NLLB fine-tuning approach supersedes that for a corpus this small, so we take their *process and conventions*, not their training stack.

## 4. Suggested sequence

1. Define scope: which variant(s), which orthography, translation first or speech first.
2. Inventory existing resources (OPUS, Hugging Face, FLORES-200 `kea_Latn`, academic corpora).
3. Build the corpus pipeline: scraping + cleaning + orthography normalization + parallel alignment.
4. Fine-tune NLLB-200 distilled; evaluate on FLORES-200 `kea_Latn` (gives a comparable BLEU/chrF score).
5. Release dataset + model openly; iterate with community feedback.
   Then submit the `kea` benchmark to masakhane-mt (see "Masakhane integration path" above).
6. Speech track: Common Voice campaign → Whisper fine-tune.
7. Longer term: push improved data to Google (they accept community contributions for low-resource languages) and seek institutional backing — the Benin lesson is that a government program ("J'aime ma langue") can take a grassroots effort to national scale.

## Key references

- Scripture Earth Kabuverdianu page: scriptureearth.org (`kea`) — existing Bible portions.
- Joshua Project `kea` page — Bible translation status (portions only, no complete NT).
- NLLB-200 / FLORES-200: Meta AI, "No Language Left Behind" (2022) — includes Kabuverdianu (`kea_Latn`).
- Google Translate 110-language expansion announcement (June 2024) — includes Cape Verdean Creole.
- FFR Translate (Bonaventure Dossou & Chris Emezue) — the Fon↔French precedent that fed Google's Fongbé support.
- Masakhane: masakhane.io
- Mozilla Common Voice: commonvoice.mozilla.org

# Historical lexical source slices

`ancient_lexical_sources.json` pins each resource, its lexical redistribution
terms and the authored review. `scripts/stage_ancient_lexica.py --dataset NAME
--fetch` verifies original bytes and stages outside intake. New namespaces append
once; `compile_ancient_lexical_ledgers.py` checks the accepted guards against the
staged slice. Reuse of a source family does not establish independence.

* Coptic: form-specific Sahidic (S) labels in the frozen CopticScriptorium Alpha
  file. Only English lexical glosses are mapped, not every translation/citation.
* Egyptian: TLA Earlier Egyptian v18 premium single-word sentence rows. Preserve
  supplied lemma, morphology, date bounds and hieroglyphs; do not invent object IDs
  or vowel readings. Broad accepted Egyptian identity is not a single period.
* Etruscan: `ancient_etruscan_2026-10-28.jsonl.gz` is the exact Kaikki rolling
  resource retrieved 2026-10-28, compressed deterministically. Its uncompressed
  SHA256 is pinned. It contains Wiktionary-derived text under CC BY-SA 4.0;
  original headword/page-history URLs and full lexical entries retain attribution.
  This is a reproducibility copy, not a new independent dictionary. Citation:
  Tatu Ylonen 2022, *Wiktextract: Wiktionary as Machine-Readable Structured Data*,
  LREC pp.1317–1325; Wiktionary contributors. Original resource:
  https://kaikki.org/dictionary/Etruscan/kaikki.org-dictionary-Etruscan.jsonl .
  Wiktionary terms: https://en.wiktionary.org/wiki/Wiktionary:Copyrights .
* Classic Mayan: a manually reviewed lexical transcription from Christian M.
  Prager's TWKM Research Note 13 (2020), DOI10.20376/IDIOM-23665556.20.rn013.en,
  p.2. The PDF bytes are pinned; the authored review records page, signs and
  attestation discussion. Text is CC BY4.0; no third-party image is redistributed.
  Rechecking the short page quotation is an editorial audit, not automatic OCR.

These slices deliberately supply **no Segments**. Their guarded admissions use
`transcription_policy=orthographic_only`; the emitter must retain blank segments
and an unsupported status even when the Latin spelling could tokenize. Future
pronunciation recovery needs a separate source-specific review. The license of
this repository's software does not replace these lexical data licenses.

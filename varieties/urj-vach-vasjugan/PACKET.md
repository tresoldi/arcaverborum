# Vach–Vasjugan — repair review, 2026-10-27

The accepted UraLex sample remains `uralex_khanty_vakh_vasyugan`, Glottocode fare1244. All 377 forms and source expert cognate annotations are preserved. The source is the tresoldi IPA-conversion fork, not an unmodified UraLex release.

82 overrides attach detached U+0306 breves to their preceding reviewed vowel (ɑ, o, ø). These are 83 diacritics, not extra vowels. UraLex `IPA_NOTES.md` specifies preserving vowel brevity. Normalized source characters remain identical after removing token spaces; no phoneme is added or removed. The review ledger retains each source snapshot, corrected sequence and reason.

Clean forms increase from 292 to **374/377**, and clean core support from 121 to **150/161**. All 377 forms map to concepts (307 distinct). Three source rows remain unclean: dull, flow and think contain comma-separated alternatives without source segmentation. Selecting or joining alternatives would require further evidence.

Run `python scripts/repair_vakh_segments.py` to verify source snapshots and generated repairs; `--write` reproduces the reviewed overrides. No upstream raw source is edited. Transcription validity and preserved character sequences do not replace specialist phonological review.

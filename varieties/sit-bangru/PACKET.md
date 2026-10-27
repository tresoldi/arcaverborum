# Bangru — original fieldwork source admission, 2026-10-27

First accepted Bangru construction: 99 supplied-IPA forms covering 95 core
concepts, from the consistently identified speaker A sample in Sarli circle,
Arunachal Pradesh, India. The canonical language is bang1369; Sarli dialect
leva1238 belongs to it. This is one newly represented language, not separate
varieties for each speaker or an overlap with an accepted sample.

Authority: Timotheus Adrianus Bodt. 2017. Bangru Language Data - various
descriptions and analyses. Zenodo, doi:10.5281/zenodo.1116263. CC BY 4.0.
Original fieldwork: December 2013. Speaker A corresponds to Pisa Chachung in
the overview deposit doi:10.5281/zenodo.1116298. Collector/team attribution is
retained there. Recordings and other speakers were not merged into this sample.
Regional Glottolog coordinates are reference points, not speaker GPS.

Of 119 reviewed core-sense entries, 95 are admitted and 24 held. Original page,
gloss, full entry, speaker label, raw alternatives and evidence hashes survive.
All alternatives in an admitted A span are retained (99 forms), rather than
choosing a convenient reading. Comparative Dammai/Namrei/Aka/Koro/China values,
Puroik comparisons and tentative Root reconstructions are never admitted as
Bangru forms or cognate judgments. No expert or computed cognacy is inferred.

Source transcriptions are supplied IPA, not converted spelling. The author's
licensed NEILS 2014 phonology presentation, slide 9, explicitly lists ʧ/ʤ;
their tʃ/dʒ equivalents are tied before segmentation. Original raw IPA remains
unchanged, including length, phonation, nasalization and tone. Multiword forms
retain boundaries. Unreviewed affricate sequences, ASCII stress conventions,
parenthetical optionality, unclear spacing and insufficiently specific senses
remain held. Every alternative must validate; partial admission is forbidden.

The frozen PDF SHA256 is 61760ad451c9594d7d82bb04fa24b392c592cb88f0d153cd8a90e813c816a9fa.
The authored ledger and original-source manifest are in src/arcaverborum/data/
bangru_original_forms.csv and bangru_original_source.json. The supplied-segment
label means source-provided transcription validated by the pipeline, not a new
native-speaker verification. The bronze score is a conservative construction
assessment; source attribution and review remain independently inspectable.

Reproduce with scripts/stage_bangru_original.py --fetch --audit-pdf (optional
PyMuPDF for PDF-span audit), validate/append its staged new namespace, rebuild
the intake database, then update sit-bangru. Generic source fetching recognizes
this document deposit and never attempts to clone Zenodo as Git. Full intake
must still be assembled in staging; never run subset ingest over active tables.

Tangam and the Nepal survey candidates remain separate held cases. The original
Bangru deposit's license does not retroactively license the Wust repository.
Review status: draft; independent specialist review remains welcome.

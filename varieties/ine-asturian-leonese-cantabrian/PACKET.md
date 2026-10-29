# Asturian sample — reviewed replacement, 2026-10-27

Accepted source is Wiktionary **wikt_ast**, under frozen Glottocode astu1245 / av_id ine-asturian-leonese-cantabrian. The frozen catalog name is broader than this construction: no Leonese or Cantabrian members are pooled. The old source member was gled_ASTURIAN. Source identity is retained explicitly, rather than claiming coverage of the whole continuum.

9715 lexical forms are retained: 166 source-provided IPA, 3,548 profile-supported, 6,001 unresolved. Supported core grows **37 → 92/161**. The source still maps 142 core concepts after 203 English-sense reviews and 42 corrections (including the shared sense rules); the larger lexical count is not pronunciation certification. GLED cognacy is not transferred; Wiktionary etymology annotations retain their own method labels.

The profile follows the primary [Academia de la Llingua Asturiana grammar (2001)](https://alladixital.org/wp-content/uploads/2022/08/Gramatica-de-la-Llingua-Asturiana.pdf), pp.15–16,23–24,36–48. It is an intentionally incomplete broad phonemic standard-spelling subset: five vowels, documented consonant/digraph correspondences, contextual c, silent u in gue/gui/que/qui, and intervocalic tap/trill distinctions. It excludes x/y ambiguity, foreign letters, dialect signs, vowel sequences, and noninitial nonintervocalic r. Stress and surface allophones are unspecified. Source IPA always takes precedence. Exact-word keys prevent automatic coverage of new spellings.

Native IPA evidence comes from the frozen Wiktextract index and is retained in form comments and intake/pronunciation evidence. Profile review records source-form identities separately. English-sense reviews do not certify target lexical accuracy. Unsupported forms remain visible, without spelling-as-IPA fallback.

Core gained with clean support: act-burn, act-rope, agr-flower, agr-root, agr-seed, ani-bird, ani-mosquito, ani-spider, bod-back, bod-belly, bod-bite, bod-breathe, bod-feather, bod-foot, bod-hair, bod-head, bod-heart, bod-kill, bod-liver, bod-mouth, bod-navel, bod-tail, bod-vomit, bod-wing, cog-what, emo-cry, emo-good, emo-laugh, foo-salt, fun-this, hou-house, kin-child, kin-father, kin-husband, kin-man, kin-mother, kin-wife, kin-woman, law-steal, lng-say, lng-sing, mot-fall, mot-run, mot-swim, mot-throw, mot-walk, phy-ash, phy-cloud, phy-dust, phy-firewood, phy-fog, phy-lake, phy-moon, phy-sand, phy-thunder, pss-give, qua-count, qua-five, qua-many, sns-dirty, sns-dry, sns-heavy, sns-sharp, sns-white, spa-near, spa-right, spa-round, spa-sit, spa-small, tim-tomorrow, tim-year, war-hunt.

Prior clean core not supported by this construction: agr-leaf, agr-tree, ani-fish, bod-blood, bod-bone, bod-ear, bod-eye, bod-horn, bod-knee, bod-tongue, kin-i, phy-star, phy-stone, phy-water, sns-hear, tim-new, tim-night.

Run `python scripts/asturian_profile.py --write`, then `python scripts/audit_core_pilots.py --write-maps`, rebuild, and run the audit without write flags. Specialist phonological and lexical review remains pending.

## Follow-up profile audit, 2026-10-27

The current construction has **166 source-provided, 3,946 profile-supported and
5,603 unresolved forms**, with **82 supported core concepts**. These supersede
the preliminary 92-core profile count above. The revised rules add documented
onset-cluster taps, post-l/n/s trills, open-vowel hiatus and written stressed-weak-
vowel hiatus (ALLA grammar pp.42–43,51). They retain source IPA precedence.

A regression test exposed that Python's empty-string membership test had allowed
word-final r into the old intervocalic branch. The grammar explicitly allows
both tap and trill in final position; these readings are now withheld. The new
contexts add 856 profile forms, and the correction removes 458 unsupported
ones: net +398 profile forms, with a conservative core change of 92 → 82.
Remaining glide/hiatus, x/y and variable-rhotic cases are not guessed.

## Worldwide GW review — 2026-10-29

[Execution, source pins, linguistic limits and exact decision ledgers](../../docs/WORLDWIDE_EXPANSION_2026-10-29.md).
Current accepted state: 9715 records; 82/161 supported core; statuses {'unclean': 5603, 'profile': 3946, 'source': 166}.
This section supersedes older current-state counts. Earlier readings/cognacy and
native evidence are retained; exact reviewed semantic corrections may unmap a
record without deleting it. Source profiles and original IPA routes remain scoped
to their guarded members/forms, with uncertainty and written-only status explicit.
See HELD before reopening source notation, sample identity or sense decisions.

## Worldwide follow-up — 2026-10-29

Accepted 9715 records; 82/161 supported core concepts. Primary: `wiktionary`.
[Execution, sources, gains and holds](../../docs/WORLDWIDE_FOLLOWUP_EXECUTION_2026-10-29.md).
Earlier evidence and source-specific cognacy remain; six precise shared English-sense
rules correct older mappings where applicable. Source conversions are not independent
IPA elicitation, profiles are finite and source-specific, and written-only records
add no phonetic support. Config and guarded custom ledgers enforce acceptance.

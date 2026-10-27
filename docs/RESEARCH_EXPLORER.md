# Research explorer implementation and review

The agreed defaults are all accepted varieties, a selection-first comparison workspace, and refinement of the existing scholarly visual style. Source acceptance and underlying lexical judgments are unchanged.

| Agreed improvement | Implementation |
|---|---|
| Separate collection and vocabulary | Independent Core/all collection and all/161-concept controls; explanatory guide |
| Broader collection | Complete accepted catalog and family downloads; previous Core-only explorer retained |
| Transcription evidence | Visible source/profile/resegmented/unresolved status, filters and interpretation notes |
| Provenance and citations | Form record IDs, source keys, dataset citation/version/license, bibliography and copy citation |
| Concept coverage | Distinct mapped and supported-core counts, missing concepts, thresholds and sorting |
| Multiple cognate assignments | Separate membership table and individual set links; source namespace retained |
| Cognate evidence | Method, source, doubt, loan, morpheme and alignment fields exposed without inferred judgments |
| Comparative wordlists | Explicit variety/concept selection, matrix cells containing synonyms and evidence |
| Definitions and mappings | Frozen definitions, original source glosses, local sense-review decisions/notes and packet links |
| Persistent navigation | Link-based details, compact URL state, filters/selections restored on reload and Back/Forward |
| Reproducible exports | CSV/TSV, selection manifests with aggregate/catalog/shard hashes, source versions and licenses |
| Linguistic search | Alias/code catalog search; literal, token and regex lexical search; optional combining-mark/case folding |
| Tier interpretation | Separate transcription/cognate scores and coverage; explicit explanation of limitations |
| Analytical maps | Scope/color controls, clickable external legends, source-scoped cognate sets, colocated popups and missing-coordinate counts |
| Tables and mobile | Sortable paginated tables, column chooser, sticky identifying columns, compact mobile defaults |
| Accessibility | Native links/buttons/labels, focus states, live result/status announcements, reduced motion and keyboard navigation |
| Sampling and missingness | Coverage distributions, source composition, documentation metadata and explicitly qualified historical/name labels |
| Performance | Lightweight catalog, family downloads, content-hash caching, worker-based parsing/querying and query timeouts |

## Verification and limits

The builder tests exercise synonym-safe coverage, individual cognate membership, preservation of uncertain evidence, source glosses, parent relationships, licenses, case-safe SQL field names, file checksums and byte-reproducible compressed outputs. The browser workflow tests collection scopes, persistent URLs, comparison, provenance, CSV/manifest export, search, read-only SQL, maps, mobile overflow and keyboard links.

Full-data exploration has practical bounds: lexical searches operate within a selected family; search exports cover up to 500 displayed matches; matrices support 16 varieties and 200 concepts per selection; arbitrary SQL sees loaded lexical families and all catalog tables. These limits are exposed in the interface. Loading many large families still depends on device memory; reload clears in-memory tables while URL selections persist.

A valid token sequence is not independent pronunciation verification. Profiles may represent broad phonemic readings with documented omissions. English sense reviews are not native lexical certification. Empty source flags and missing entries are not evidence of absence. Historical/reconstructed labels derived from catalog names are marked as such; missing dates and license metadata remain explicit. No guessed dates, sound correspondences, cognate judgments or semantic corrections were introduced by the website build.

The Pages workflow publishes committed data artifacts, not live intake. `scripts/build_research_web.py` regenerates the complete browser dataset from the accepted aggregate; the public manifest and representative workflows must be checked after deployment. See `web/README.md` for reproduction commands and the browser test.

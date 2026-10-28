# RVID data component

The `rvidinfinitives` lexical data derivative, its source transcription review
(`romance_r04_review_2026-10-28.csv`) and corresponding data specification retain
GPLv3 terms from RVID2.0. They are not relicensed under this repository's MIT
software licence. See the public [notice](../web/data/RVID_NOTICE.txt) and
[GPL text](../web/data/RVID_GPL-3.0.txt). Other source components retain their own
terms recorded in aggregate metadata and exports.

The notice identifies the original authors, immutable source, modifications and
corresponding source. `scripts/stage_rvid.py --fetch` reconstructs the derivative
outside active intake using pinned original files and the tracked review. Never
replace active intake with that partial stage; append only the new namespace once.
For an already appended namespace, validate reproduction without appending again.

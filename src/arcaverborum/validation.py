from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from arcaverborum.schema import ColumnTracking, DatasetMetadata, ReferenceVersions


@dataclass
class ValidationAccumulator:
    total_forms: int = 0
    total_languages: int = 0
    total_parameters: int = 0
    datasets_processed: int = 0
    datasets_with_cognates: int = 0

    forms_with_glottocode: int = 0
    forms_with_concepticon: int = 0
    forms_with_cognacy: int = 0
    forms_with_segments: int = 0
    forms_with_alignment: int = 0
    forms_with_morpheme_index: int = 0
    forms_with_segment_slice: int = 0

    all_metadata: list[dict] = field(default_factory=list)
    all_references: list[dict] = field(default_factory=list)
    all_bibtex: list[str] = field(default_factory=list)
    all_column_tracking: list[dict] = field(default_factory=list)

    datasets_with_morpheme_index_names: list[str] = field(default_factory=list)
    datasets_with_segment_slice_names: list[str] = field(default_factory=list)

    completeness: dict[str, dict] = field(default_factory=dict)

    def update(
        self,
        dataset: str,
        forms: pd.DataFrame,
        languages: pd.DataFrame,
        parameters: pd.DataFrame,
        metadata: DatasetMetadata | dict,
        references: ReferenceVersions | dict,
        bibtex: str,
        column_tracking: ColumnTracking | dict,
    ) -> None:
        self.total_forms += len(forms)
        self.total_languages += len(languages)
        self.total_parameters += len(parameters)
        self.datasets_processed += 1

        meta_dict = metadata.to_dict() if isinstance(metadata, DatasetMetadata) else metadata
        ref_dict = references.to_dict() if isinstance(references, ReferenceVersions) else references
        ct_dict = column_tracking.to_dict() if isinstance(column_tracking, ColumnTracking) else column_tracking

        has_cognates = meta_dict.get("Has_Cognates", False)
        if has_cognates:
            self.datasets_with_cognates += 1

        self.forms_with_glottocode += int(forms["Glottocode"].notna().sum())
        self.forms_with_concepticon += int(forms["Concepticon_ID"].notna().sum())
        self.forms_with_cognacy += int(forms["Cognacy"].notna().sum())
        self.forms_with_segments += int(forms["Segments"].notna().sum())
        self.forms_with_alignment += int(forms["Alignment"].notna().sum())

        if forms["Morpheme_Index"].notna().any():
            self.datasets_with_morpheme_index_names.append(dataset)
            self.forms_with_morpheme_index += int(forms["Morpheme_Index"].notna().sum())

        if forms["Segment_Slice"].notna().any():
            self.datasets_with_segment_slice_names.append(dataset)
            self.forms_with_segment_slice += int(forms["Segment_Slice"].notna().sum())

        null_pct: dict[str, float] = {}
        for col in ("Segments", "Comment", "Loan", "Cognacy", "Alignment"):
            if col in forms.columns:
                total = len(forms)
                null_count = int(forms[col].isna().sum())
                null_pct[col] = round(100 * null_count / total, 1) if total > 0 else 0.0

        self.completeness[dataset] = {
            "forms": len(forms),
            "languages": len(languages),
            "parameters": len(parameters),
            "has_cognates": has_cognates,
            "columns_present": ct_dict.get("forms_columns_present", []),
            "null_percentage": null_pct,
        }

        self.all_metadata.append(meta_dict)
        self.all_references.append(ref_dict)
        self.all_bibtex.append(bibtex)
        self.all_column_tracking.append(ct_dict)

    def generate_report(self) -> dict:
        version_dist: dict[str, dict[str, int]] = {
            "glottolog": {},
            "concepticon": {},
            "clts": {},
        }
        for ref in self.all_references:
            for key in ("Glottolog_Version", "Concepticon_Version", "CLTS_Version"):
                version = ref.get(key)
                if version:
                    dist_key = key.replace("_Version", "").lower()
                    version_dist[dist_key][version] = version_dist[dist_key].get(version, 0) + 1

        quality: dict[str, float] = {}
        if self.total_forms > 0:
            quality = {
                "glottocode_coverage_percent": round(100 * self.forms_with_glottocode / self.total_forms, 2),
                "concepticon_coverage_percent": round(100 * self.forms_with_concepticon / self.total_forms, 2),
                "forms_with_cognate_data_percent": round(100 * self.forms_with_cognacy / self.total_forms, 2),
                "forms_with_segments_percent": round(100 * self.forms_with_segments / self.total_forms, 2),
                "forms_with_alignment_percent": round(100 * self.forms_with_alignment / self.total_forms, 2),
            }

        return {
            "summary": {
                "total_datasets": self.datasets_processed,
                "total_forms": self.total_forms,
                "total_languages": self.total_languages,
                "total_parameters": self.total_parameters,
                "datasets_with_cognates": self.datasets_with_cognates,
                "datasets_with_partial_cognacy": (
                    len(self.datasets_with_morpheme_index_names)
                    + len(self.datasets_with_segment_slice_names)
                ),
            },
            "completeness": self.completeness,
            "referential_integrity": {
                "note": "Referential integrity not validated in streaming mode",
            },
            "data_quality": quality,
            "version_distribution": version_dist,
            "partial_cognacy": {
                "datasets_with_morpheme_index": self.datasets_with_morpheme_index_names,
                "datasets_with_segment_slice": self.datasets_with_segment_slice_names,
                "forms_with_morpheme_index": self.forms_with_morpheme_index,
                "forms_with_segment_slice": self.forms_with_segment_slice,
            },
        }

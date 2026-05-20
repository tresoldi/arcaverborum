from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class ColumnSchema:
    forms_processing: tuple[str, ...]
    forms_output: tuple[str, ...]
    languages: tuple[str, ...]
    parameters: tuple[str, ...]


OUTPUT_SCHEMA = ColumnSchema(
    forms_processing=(
        "ID", "Dataset", "Local_ID", "Language_ID", "Parameter_ID",
        "Value", "Form", "Segments", "Comment", "Source", "Loan",
        "Graphemes", "Profile", "Cognacy", "Doubt", "Cognate_Detection_Method",
        "Cognate_Source", "Alignment", "Glottocode", "Glottolog_Name",
        "Concepticon_ID", "Concepticon_Gloss", "Morpheme_Index", "Segment_Slice",
    ),
    forms_output=(
        "ID", "Dataset", "Language_ID", "Glottocode", "Glottolog_Name",
        "Parameter_ID", "Concepticon_Gloss", "Value", "Form", "Segments",
        "Cognacy", "Alignment", "Loan", "Morpheme_Index", "Segment_Slice",
        "Doubt", "Comment", "Source", "Cognate_Detection_Method", "Cognate_Source",
    ),
    languages=(
        "ID", "Dataset", "Name", "Glottocode", "Glottolog_Name",
        "ISO639P3code", "Macroarea", "Latitude", "Longitude",
        "Family", "Location", "Remark",
    ),
    parameters=(
        "ID", "Dataset", "Name", "Concepticon_ID", "Concepticon_Gloss",
        "Gloss", "Description",
    ),
)


@dataclass(frozen=True, slots=True)
class DatasetMetadata:
    dataset: str
    title: str
    citation: str
    url: str
    license: str
    cldf_module: str
    repository_version: str | None
    python_version: str | None
    form_count: int
    language_count: int
    parameter_count: int
    has_cognates: bool

    def to_dict(self) -> dict:
        return {
            "Dataset": self.dataset,
            "Title": self.title,
            "Citation": self.citation,
            "URL": self.url,
            "License": self.license,
            "CLDF_Module": self.cldf_module,
            "Repository_Version": self.repository_version,
            "Python_Version": self.python_version,
            "Form_Count": self.form_count,
            "Language_Count": self.language_count,
            "Parameter_Count": self.parameter_count,
            "Has_Cognates": self.has_cognates,
        }


@dataclass(frozen=True, slots=True)
class ReferenceVersions:
    dataset: str
    glottolog_version: str | None
    concepticon_version: str | None
    clts_version: str | None

    def to_dict(self) -> dict:
        return {
            "Dataset": self.dataset,
            "Glottolog_Version": self.glottolog_version,
            "Concepticon_Version": self.concepticon_version,
            "CLTS_Version": self.clts_version,
        }


@dataclass(frozen=True, slots=True)
class ColumnTracking:
    dataset: str
    forms_columns_present: tuple[str, ...]
    has_cognates: bool

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "forms_columns_present": list(self.forms_columns_present),
            "has_cognates": self.has_cognates,
        }


@dataclass
class DatasetResult:
    forms: pd.DataFrame
    languages: pd.DataFrame
    parameters: pd.DataFrame
    metadata: DatasetMetadata
    references: ReferenceVersions
    bibtex: str
    column_tracking: ColumnTracking

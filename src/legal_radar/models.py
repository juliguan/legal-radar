"""Pydantic-modellen: YAML-kennisbank en modeloutput."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class Evidence(str, Enum):
    text_checked = "text_checked"
    primary_page = "primary_page"
    search_snippet = "search_snippet"
    secondary = "secondary"


class SourceRef(BaseModel):
    url: str
    title: str
    type: str
    accessed: str


class Law(BaseModel):
    id: str
    reference: str
    article: str
    what_nl: str
    source_url: str
    evidence: Evidence
    verified: bool

    @field_validator("source_url")
    @classmethod
    def _url(cls, v: str) -> str:
        if not v.startswith("http"):
            raise ValueError("source_url moet een URL zijn")
        return v


class TriggerQuestion(BaseModel):
    id: str
    text: str
    based_on: list[str] = Field(min_length=1)


class Mistake(BaseModel):
    text: str
    source_url: str
    evidence: Evidence
    verified: bool


class Change(BaseModel):
    date: str
    text: str
    source_url: str
    evidence: Evidence
    verified: bool


class AppliesTo(BaseModel):
    text: str
    source_url: str


class LegalArea(BaseModel):
    id: str
    name: str
    summary_nl: str
    applies_to: list[AppliesTo]
    laws: list[Law]
    trigger_questions: list[TriggerQuestion] = Field(min_length=3, max_length=5)
    common_mistakes: list[Mistake]
    recent_changes: list[Change]
    sources: list[SourceRef] = Field(min_length=1)
    source_conflicts: list[str] = []

    @model_validator(mode="after")
    def _unique_trigger_ids(self) -> "LegalArea":
        ids = [t.id for t in self.trigger_questions]
        if len(ids) != len(set(ids)):
            raise ValueError(f"dubbele trigger-id's in {self.id}")
        return self


class Meta(BaseModel):
    version: int
    accessed: str
    disclaimer_nl: str
    known_gaps: list[str] = []


class KnowledgeBase(BaseModel):
    meta: Meta
    areas: list[LegalArea] = Field(min_length=1)

    def area(self, area_id: str) -> LegalArea:
        for a in self.areas:
            if a.id == area_id:
                return a
        raise KeyError(area_id)


# --- Modeloutput -------------------------------------------------------------

class AreaStatus(str, Enum):
    relevant = "relevant"
    niet_relevant = "niet_relevant"
    onzeker = "onzeker"


class AreaAssessment(BaseModel):
    """Wat het model per gebied mag bepalen: status, triggervraag, citaat. Verder niets."""
    area_id: str
    status: AreaStatus
    trigger_id: str | None = None
    quote: str | None = None


class Assessment(BaseModel):
    areas: list[AreaAssessment]


class CheckedAssessment(AreaAssessment):
    """Resultaat na de code-controles."""
    quote_ok: bool = True
    note: str | None = None

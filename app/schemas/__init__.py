"""Schemas Pydantic para request/response."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


# ── Curriculo ────────────────────────────────────────────────────────────────
class CVRequest(BaseModel):
    """Input do candidato para matching."""
    name: str = Field(..., min_length=1, max_length=100, examples=["Caio"])
    level: Optional[str] = Field(
        None, examples=["estagio"], description="estagio | junior | pleno | senior"
    )
    skills: List[str] = Field(
        ...,
        min_length=1,
        examples=[["python", "fastapi", "postgresql", "docker"]],
        description="Skills tecnicas do candidato",
    )
    areas: List[str] = Field(
        default_factory=list,
        examples=[["backend", "devops", "automacao"]],
        description="Areas de interesse",
    )


class MatchDetailOut(BaseModel):
    """Detalhe de cada tipo de match no ranking."""
    kind: str
    terms: List[str]
    weight: int


class RankedJobOut(BaseModel):
    """Vaga ja rankeada para output."""
    id: Optional[int]
    title: str
    company: Optional[str]
    location: Optional[str]
    url: Optional[HttpUrl] = None
    score: int
    band: str
    emoji: str
    action: str
    match_details: List[MatchDetailOut]


class MatchResponse(BaseModel):
    """Resposta do POST /match."""
    candidate: str
    total_vagas: int
    matched: List[RankedJobOut]


# ── Vaga ─────────────────────────────────────────────────────────────────────
class JobOut(BaseModel):
    """Vaga para listagem/detalhe."""
    id: int
    title: str
    company: Optional[str]
    location: Optional[str]
    url: Optional[HttpUrl] = None
    level: Optional[str]
    source: str
    scraped_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    items: List[JobOut]
    total: int
    limit: int
    offset: int


# ── Stats ────────────────────────────────────────────────────────────────────
class StatsResponse(BaseModel):
    total_vagas: int
    vagas_por_source: dict[str, int]
    vagas_por_level: dict[str, int]
    ultima_coleta: Optional[datetime] = None

"""
Motor de ranking de vagas por compatibilidade com currículo.

Score = soma ponderada de matches entre skills do candidato e título da vaga.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional

from app.config import get_settings

settings = get_settings()


# ── Faixas de compatibilidade ───────────────────────────────────────────────
@dataclass(frozen=True)
class Band:
    """Faixa de score e label humano-legível."""
    min_score: int
    label: str
    emoji: str
    action: str


HIGH = Band(15, "ALTA", "🟢", "Candidatar imediatamente")
MEDIUM = Band(8, "MEDIA", "🟡", "Boa opcao")
LOW = Band(3, "BAIXA", "🟠", "Candidatura possivel")
MINIMAL = Band(-999, "MINIMA", "🔴", "Pouca relacao — pular")

BANDS = (HIGH, MEDIUM, LOW, MINIMAL)


def band_for(score: int) -> Band:
    """Retorna a faixa de compatibilidade para um score."""
    for band in BANDS:
        if score >= band.min_score:
            return band
    return MINIMAL


# ── Match types ──────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class MatchDetail:
    """Detalhe de um match: lista de termos e peso."""
    kind: str  # "exato" | "parcial" | "nivel" | "area"
    terms: tuple[str, ...]
    weight: int


@dataclass
class RankedItem:
    """Item rankeado: input + score + banda + detalhes."""
    id: Optional[int]
    title: str
    score: int
    band: Band
    details: list[MatchDetail]
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None


# ── Engine ──────────────────────────────────────────────────────────────────
class JobRanker:
    """
    Calcula score de compatibilidade entre um currículo e uma vaga.
    Stateless — pode ser instanciado uma vez e reutilizado.
    """

    # Padroes para tokenizacao de texto
    _TOKEN_RE = re.compile(r"[a-z0-9+#.]+", re.IGNORECASE)
    _LEVEL_KEYWORDS = {
        "estagio": ("estagio", "estagiario", "intern", "trainee"),
        "junior": ("junior", "jr", "entry", "entry-level", "assistente"),
        "pleno": ("pleno", "mid", "intermediate"),
        "senior": ("senior", "sr", "lead", "principal"),
    }

    def __init__(
        self,
        exact_weight: int | None = None,
        partial_weight: int | None = None,
        level_weight: int | None = None,
        area_weight: int | None = None,
    ) -> None:
        self.exact_weight = exact_weight or settings.ranker_exact_weight
        self.partial_weight = partial_weight or settings.ranker_partial_weight
        self.level_weight = level_weight or settings.ranker_level_weight
        self.area_weight = area_weight or settings.ranker_area_weight

    def _normalize(self, text: str) -> str:
        """Lowercase + strip acentos basicos para matching."""
        text = text.lower()
        replacements = str.maketrans({
            "á": "a", "à": "a", "ã": "a", "â": "a",
            "é": "e", "ê": "e",
            "í": "i",
            "ó": "o", "ô": "o", "õ": "o",
            "ú": "u", "ü": "u",
            "ç": "c",
        })
        return text.translate(replacements)

    def _tokens(self, text: str) -> set[str]:
        """Extrai tokens normalizados."""
        return set(self._TOKEN_RE.findall(self._normalize(text)))

    def rank(
        self,
        *,
        title: str,
        skills: Iterable[str],
        areas: Iterable[str],
        level: Optional[str] = None,
        job_id: Optional[int] = None,
        company: Optional[str] = None,
        location: Optional[str] = None,
        url: Optional[str] = None,
    ) -> RankedItem:
        """
        Calcula o score de uma vaga contra o currículo fornecido.
        """
        title_norm = self._normalize(title)
        title_tokens = self._tokens(title)

        details: list[MatchDetail] = []
        score = 0

        # ── Match exato e parcial por skill ──
        exact_matches: list[str] = []
        partial_matches: list[str] = []

        for skill in skills:
            skill_norm = self._normalize(skill.strip())
            if not skill_norm:
                continue

            if skill_norm in title_tokens:
                exact_matches.append(skill)
                score += self.exact_weight
            elif skill_norm in title_norm:
                partial_matches.append(skill)
                score += self.partial_weight

        if exact_matches:
            details.append(MatchDetail("exato", tuple(exact_matches), self.exact_weight * len(exact_matches)))
        if partial_matches:
            details.append(MatchDetail("parcial", tuple(partial_matches), self.partial_weight * len(partial_matches)))

        # ── Match por area ──
        area_matches: list[str] = []
        for area in areas:
            area_norm = self._normalize(area.strip())
            if area_norm and area_norm in title_norm:
                area_matches.append(area)
                score += self.area_weight

        if area_matches:
            details.append(MatchDetail("area", tuple(area_matches), self.area_weight * len(area_matches)))

        # ── Match por nivel ──
        if level:
            level_norm = self._normalize(level.strip())
            keywords = self._LEVEL_KEYWORDS.get(level_norm, (level_norm,))
            level_matches = [kw for kw in keywords if kw in title_norm]
            if level_matches:
                details.append(MatchDetail("nivel", tuple(level_matches), self.level_weight))
                score += self.level_weight

        return RankedItem(
            id=job_id,
            title=title,
            score=score,
            band=band_for(score),
            details=details,
            company=company,
            location=location,
            url=url,
        )

    def rank_batch(
        self,
        jobs: Iterable[dict],
        *,
        skills: Iterable[str],
        areas: Iterable[str],
        level: Optional[str] = None,
    ) -> list[RankedItem]:
        """Ranqueia uma lista de vagas e retorna ordenada por score (desc)."""
        ranked = [
            self.rank(
                title=j.get("title", ""),
                skills=skills,
                areas=areas,
                level=level,
                job_id=j.get("id"),
                company=j.get("company"),
                location=j.get("location"),
                url=j.get("url"),
            )
            for j in jobs
        ]
        ranked.sort(key=lambda r: r.score, reverse=True)
        return ranked

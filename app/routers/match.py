"""Rotas de match."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Job
from app.schemas import (
    CVRequest,
    MatchDetailOut,
    MatchResponse,
    RankedJobOut,
)
from app.services.ranker import JobRanker

router = APIRouter(prefix="/match", tags=["match"])

# Singleton stateless
_ranker = JobRanker()


@router.post("", response_model=MatchResponse)
async def match_candidate(
    cv: CVRequest,
    session: AsyncSession = Depends(get_session),
    min_score: int = 0,
    limit: int = 50,
) -> MatchResponse:
    """
    Recebe um curriculo e retorna as vagas mais compativeis.
    Ordenado por score (desc).
    """
    # Busca todas as vagas — em prod usar paginacao + FTS
    result = await session.execute(select(Job))
    jobs = result.scalars().all()

    # Converte para dict para o ranker
    job_dicts = [
        {"id": j.id, "title": j.title, "company": j.company, "location": j.location, "url": j.url}
        for j in jobs
    ]

    ranked = _ranker.rank_batch(
        job_dicts,
        skills=cv.skills,
        areas=cv.areas,
        level=cv.level,
    )

    # Filtra por score minimo
    if min_score > 0:
        ranked = [r for r in ranked if r.score >= min_score]

    # Limita
    ranked = ranked[:limit]

    return MatchResponse(
        candidate=cv.name,
        total_vagas=len(ranked),
        matched=[
            RankedJobOut(
                id=r.id,
                title=r.title,
                company=r.company,
                location=r.location,
                url=r.url,
                score=r.score,
                band=r.band.label,
                emoji=r.band.emoji,
                action=r.band.action,
                match_details=[
                    MatchDetailOut(kind=d.kind, terms=list(d.terms), weight=d.weight)
                    for d in r.details
                ],
            )
            for r in ranked
        ],
    )

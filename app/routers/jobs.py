"""Rotas de vagas."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Job
from app.schemas import JobListResponse, JobOut, StatsResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    session: AsyncSession = Depends(get_session),
    limit: int = 20,
    offset: int = 0,
    source: Optional[str] = None,
    level: Optional[str] = None,
) -> JobListResponse:
    """Lista vagas com filtros opcionais."""
    stmt = select(Job)
    count_stmt = select(func.count(Job.id))

    if source:
        stmt = stmt.where(Job.source == source)
        count_stmt = count_stmt.where(Job.source == source)
    if level:
        stmt = stmt.where(Job.level == level)
        count_stmt = count_stmt.where(Job.level == level)

    stmt = stmt.order_by(Job.scraped_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    jobs = result.scalars().all()

    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    return JobListResponse(
        items=[JobOut.model_validate(j) for j in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: int,
    session: AsyncSession = Depends(get_session),
) -> JobOut:
    """Detalhe de uma vaga especifica."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Vaga {job_id} nao encontrada")
    return JobOut.model_validate(job)


@router.get("/stats/overview", response_model=StatsResponse)
async def stats(session: AsyncSession = Depends(get_session)) -> StatsResponse:
    """Estatisticas gerais do banco de vagas."""
    total = await session.scalar(select(func.count(Job.id))) or 0

    by_source_rows = await session.execute(
        select(Job.source, func.count(Job.id)).group_by(Job.source)
    )
    by_source = {row[0]: row[1] for row in by_source_rows.all()}

    by_level_rows = await session.execute(
        select(Job.level, func.count(Job.id))
        .where(Job.level.isnot(None))
        .group_by(Job.level)
    )
    by_level = {row[0]: row[1] for row in by_level_rows.all()}

    last = await session.scalar(select(Job.scraped_at).order_by(Job.scraped_at.desc()))

    return StatsResponse(
        total_vagas=total,
        vagas_por_source=by_source,
        vagas_por_level=by_level,
        ultima_coleta=last,
    )

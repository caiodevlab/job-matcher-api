"""Testes do motor de ranking."""
import pytest

from app.services.ranker import JobRanker, band_for


@pytest.fixture
def ranker() -> JobRanker:
    return JobRanker()


def test_band_thresholds():
    assert band_for(0).label == "MINIMA"
    assert band_for(2).label == "MINIMA"
    assert band_for(3).label == "BAIXA"
    assert band_for(7).label == "BAIXA"
    assert band_for(8).label == "MEDIA"
    assert band_for(14).label == "MEDIA"
    assert band_for(15).label == "ALTA"
    assert band_for(50).label == "ALTA"


def test_exact_skill_match(ranker):
    """Skill exata no titulo deve somar peso exato."""
    result = ranker.rank(
        title="Vaga Python Backend",
        skills=["python"],
        areas=[],
    )
    assert result.score == ranker.exact_weight
    assert any(d.kind == "exato" and "python" in d.terms for d in result.details)


def test_partial_skill_match(ranker):
    """Skill parcial no titulo deve somar peso parcial."""
    result = ranker.rank(
        title="Vaga FastAPI Senior",
        skills=["fastapi"],
        areas=[],
    )
    # "fastapi" aparece como substring mesmo sem token boundary
    assert result.score >= ranker.partial_weight
    assert any(d.kind == "parcial" for d in result.details)


def test_area_match(ranker):
    result = ranker.rank(
        title="Vaga Backend Developer",
        skills=["java"],  # sem match
        areas=["backend"],
    )
    assert result.score == ranker.area_weight
    assert any(d.kind == "area" for d in result.details)


def test_level_match(ranker):
    result = ranker.rank(
        title="Estagio em Desenvolvimento",
        skills=[],
        areas=[],
        level="estagio",
    )
    assert result.score == ranker.level_weight
    assert any(d.kind == "nivel" for d in result.details)


def test_combined_score(ranker):
    """Multiplos matches devem acumular score."""
    result = ranker.rank(
        title="Estagio Backend Python",
        skills=["python", "fastapi"],
        areas=["backend"],
        level="estagio",
    )
    # exato(python) + parcial(fastapi) + area(backend) + nivel(estagio)
    expected = (
        ranker.exact_weight
        + ranker.partial_weight
        + ranker.area_weight
        + ranker.level_weight
    )
    assert result.score == expected
    assert result.band.label == "ALTA"


def test_normalization_accent_insensitive(ranker):
    """Deve ignorar acentos no matching."""
    result = ranker.rank(
        title="Vaga Programação Júnior",
        skills=["programacao", "junior"],
        areas=[],
    )
    # "programacao" deve casar com "programacao" no titulo (sem acento)
    # "junior" deve casar exatamente
    assert result.score > 0


def test_rank_batch_sorting(ranker):
    """rank_batch deve ordenar por score decrescente."""
    jobs = [
        {"id": 1, "title": "Vaga Java Senior"},
        {"id": 2, "title": "Estagio Python Backend"},
        {"id": 3, "title": "Designer Grafico"},
    ]
    ranked = ranker.rank_batch(
        jobs, skills=["python", "fastapi"], areas=["backend"], level="estagio"
    )
    # O segundo deve ser o melhor match
    assert ranked[0].id == 2
    # O terceiro nao tem nada a ver
    assert ranked[-1].id == 3
    assert ranked[-1].score == 0

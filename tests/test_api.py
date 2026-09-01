"""Testes de integracao da API."""
import pytest


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "name" in body


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"


@pytest.mark.asyncio
async def test_match_empty_db(client):
    """Match com DB vazio deve retornar lista vazia mas 200."""
    resp = await client.post(
        "/match",
        json={
            "name": "Caio",
            "level": "estagio",
            "skills": ["python", "fastapi"],
            "areas": ["backend"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["candidate"] == "Caio"
    assert body["total_vagas"] == 0
    assert body["matched"] == []


@pytest.mark.asyncio
async def test_match_invalid_payload(client):
    """Payload sem skills deve dar 422."""
    resp = await client.post(
        "/match",
        json={"name": "Caio", "level": "estagio", "skills": []},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_jobs_list_empty(client):
    resp = await client.get("/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []


@pytest.mark.asyncio
async def test_stats_empty(client):
    resp = await client.get("/jobs/stats/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_vagas"] == 0

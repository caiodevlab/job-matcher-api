"""
Scraper de vagas com anti-duplicacao e anti-ban.

Usa httpx async + selectolax (HTML parser rapido).
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import AsyncIterator, Iterable, Optional

import httpx
from selectolax.parser import HTMLParser

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ScrapedJob:
    """Vaga coletada (antes de ir pro banco)."""
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None
    source: str = "unknown"

    @property
    def source_hash(self) -> str:
        """Hash deterministico para evitar duplicatas."""
        key = f"{self.title.strip().lower()}|{(self.company or '').strip().lower()}|{(self.url or '').strip()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()


# Heuristica simples de deteccao de nivel
LEVEL_RE = re.compile(
    r"\b(estagi[oá]rio|estagi[oá]|intern|trainee|junior|jr\.?|jovem\s+aprendiz|auxiliar|assistente)\b",
    re.IGNORECASE,
)


def _detect_level(title: str) -> Optional[str]:
    """Detecta nivel a partir do titulo da vaga."""
    m = LEVEL_RE.search(title)
    if not m:
        return None
    word = m.group(0).lower()
    if "estagi" in word or "intern" in word or "trainee" in word or "aprendiz" in word or "auxiliar" in word or "assistente" in word:
        return "estagio"
    if "junior" in word or "jr" in word:
        return "junior"
    return None


class JobScraper:
    """
    Scraper generico. Subclasses implementam `parse_html()` para cada fonte.
    """

    def __init__(self, source_name: str, base_url: str, timeout: int | None = None):
        self.source_name = source_name
        self.base_url = base_url
        self.timeout = timeout or settings.scraper_timeout_seconds
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "JobScraper":
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": settings.scraper_user_agent},
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client:
            await self._client.aclose()

    async def fetch(self, url: str) -> str:
        """Faz GET e retorna HTML."""
        assert self._client is not None, "Use o scraper como async context manager"
        resp = await self._client.get(url)
        resp.raise_for_status()
        return resp.text

    def parse_html(self, html: str) -> Iterable[ScrapedJob]:
        """Override em cada subclasse para parsear o HTML especifico."""
        raise NotImplementedError

    async def scrape(self, urls: list[str]) -> AsyncIterator[ScrapedJob]:
        """Itera sobre as URLs e yield vagas parseadas."""
        for url in urls:
            try:
                html = await self.fetch(url)
            except httpx.HTTPError as exc:
                logger.warning(f"[{self.source_name}] Falha ao buscar {url}: {exc}")
                continue

            for job in self.parse_html(html):
                job.source = self.source_name
                if not job.level:
                    job.level = _detect_level(job.title)
                yield job


# ── Exemplo: scraper generico baseado em data-attributes ────────────────────
class GenericListingScraper(JobScraper):
    """
    Scraper generico que procura elementos com classes comuns.
    Bom como exemplo — cada site real pede customizacao.
    """

    def __init__(self, source_name: str, base_url: str, **kwargs):
        super().__init__(source_name, base_url, **kwargs)

    def parse_html(self, html: str) -> Iterable[ScrapedJob]:
        tree = HTMLParser(html)
        # heuristica simples: procure <article> ou <li> com titulo dentro
        for node in tree.css("article, li.vaga, .job-listing, .job-card"):
            title_node = node.css_first("h2, h3, .job-title, .title")
            if not title_node:
                continue
            title = title_node.text(strip=True)
            if not title or len(title) < 3:
                continue

            company = None
            company_node = node.css_first(".company, .employer, [data-company]")
            if company_node:
                company = company_node.text(strip=True)

            location = None
            loc_node = node.css_first(".location, [data-location]")
            if loc_node:
                location = loc_node.text(strip=True)

            url = None
            link = node.css_first("a")
            if link and link.attributes.get("href"):
                url = link.attributes["href"]

            yield ScrapedJob(
                title=title,
                company=company,
                location=location,
                url=url,
            )

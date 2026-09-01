# 💼 Job Matcher API

> **API REST que recebe um currículo e devolve vagas de TI ranqueadas por compatibilidade. Score, filtering, histórico de buscas — tudo via endpoints documentados.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Problema que resolve

O `Assistente-Vagas` original rodava no terminal e tinha que rodar de novo cada vez. Esta API transforma a lógica de scraping + ranking em um **serviço HTTP production-ready**:

- Empresas podem integrar o ranking de vagas em seus sistemas
- Usuários enviam currículo via `POST` e recebem vagas ranqueadas em JSON
- Documentação Swagger em `/docs`
- Pronto para deploy em Docker

---

## ⚡ Funcionalidades

- 📄 **POST /match** — Envia currículo, recebe vagas ranqueadas
- 🔍 **GET /jobs** — Lista vagas com filtros (score mínimo, área, nível)
- 📊 **GET /jobs/{id}** — Detalhe de uma vaga específica
- 📈 **GET /stats** — Estatísticas: total de vagas, score médio, áreas mais demandadas
- 🔄 **POST /scrape** — Dispara nova coleta de vagas (protegido)
- ✅ **Idempotente** — Scraper só coleta o que ainda não existe

---

## 🛠️ Stack

| Camada | Tecnologia |
|---|---|
| **Framework** | FastAPI (async, validated) |
| **ORM** | SQLAlchemy 2.x (async) |
| **Migrations** | Alembic |
| **Database** | PostgreSQL 15 + pgvector |
| **Validation** | Pydantic v2 |
| **HTTP Client** | `httpx` (async) |
| **HTML Parsing** | `selectolax` (mais rápido que BeautifulSoup) |
| **Container** | Docker + Docker Compose |

---

## 📂 Estrutura do projeto

```
job-matcher-api/
├── app/
│   ├── main.py              # FastAPI app, CORS, lifespan
│   ├── config.py            # Settings via Pydantic
│   ├── database.py          # Session + engine async
│   ├── models/
│   │   └── job.py           # SQLAlchemy models
│   ├── schemas/
│   │   ├── cv.py            # CV input/output
│   │   └── job.py           # Job output
│   ├── services/
│   │   ├── scraper.py       # Coleta de vagas
│   │   └── ranker.py        # Motor de score
│   └── routers/
│       ├── jobs.py          # /jobs endpoints
│       └── match.py         # /match endpoint
├── tests/
│   ├── test_ranker.py       # Unit tests do ranker
│   ├── test_api.py          # API integration tests
│   └── conftest.py          # Fixtures
├── alembic/                 # Migrations
│   ├── env.py
│   └── versions/
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
└── requirements.txt
```

---

## 🚀 Como rodar

### Desenvolvimento local

```bash
# 1. Clone
git clone https://github.com/caiodevlab/job-matcher-api
cd job-matcher-api

# 2. Crie .env
cp .env.example .env
# Edite: DATABASE_URL, SCRAPER_CONFIG

# 3. Suba o banco
docker compose up -d db

# 4. Rode migrations
alembic upgrade head

# 5. Instale deps e execute
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse:
- **API:** http://localhost:8000
- **Swagger:** http://localhost:8000/docs
- **Admin DB:** http://localhost:8081 (Adminer)

### Docker completo

```bash
docker compose up -d
```

---

## 🔌 Endpoints principais

### `POST /match`

Envia currículo e recebe vagas ranqueadas:

```bash
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Caio",
    "level": "estagio",
    "skills": ["python", "fastapi", "postgresql", "docker"],
    "areas": ["backend", "devops", "automacao"]
  }'
```

Resposta:

```json
{
  "candidate_id": "caio-c7f2",
  "total_vagas": 47,
  "matched": [
    {
      "id": 12,
      "title": "Estagio Backend Python",
      "company": "Tech Corp",
      "score": 22,
      "band": "ALTA",
      "match_details": {
        "exato": ["python", "backend"],
        "parcial": ["postgresql"],
        "area": ["backend"]
      },
      "url": "https://..."
    }
  ]
}
```

---

## 🧠 Como o ranking funciona

| Tipo de match | Peso | Descrição |
|---|---|---|
| **Exato** | +3 | Skill inteira no título da vaga |
| **Parcial** | +1 | Skill parcial no título |
| **Nível** | +2 | Vaga de estágio para perfil de estágio |
| **Área** | +2 | Área de interesse no título |

| Score | Banda | Ação |
|---|---|---|
| `>= 15` | 🟢 **ALTA** | Candidatar imediatamente |
| `>= 8` | 🟡 **MÉDIA** | Boa opção |
| `>= 3` | 🟠 **BAIXA** | Possível |
| `< 3` | 🔴 **MÍNIMA** | Pouca relação |

---

## 🔒 Variáveis de ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `DATABASE_URL` | Connection string do Postgres | `postgresql+asyncpg://postgres:postgres@localhost:5432/jobmatcher` |
| `DEBUG` | Modo debug | `false` |
| `CORS_ORIGINS` | Origens CORS (separadas por vírgula) | `http://localhost:3000` |

---

## 📝 Licença

MIT — use, modifique, distribua.

---

<p align="center">
  Feito com ☕ por <a href="https://github.com/caiodevlab">@caiodevlab</a>
</p>

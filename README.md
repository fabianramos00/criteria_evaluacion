# Criteria Evaluacion

API for evaluating repository compliance across 8 criteria areas.

## Criteria Areas

| Criterion | Max Rating |
|-----------|------------|
| Visibility | 9.5 |
| Policy | 9 |
| Legal Aspects | 5 |
| Metadata | 16 |
| Interoperability | 13 |
| Security | 4 |
| Statistics | 4 |
| Services | 7 |

**Total: 67.5 points**

## Tech Stack

- FastAPI + Pydantic v2
- PostgreSQL + SQLAlchemy (async)
- Alembic migrations

## Setup

```bash
cp .env.example .env  # Configure DATABASE_URL and API keys
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:app --reload
```

## API Endpoints

### Registration
```
POST /                     # Register repository → returns token
```

### Evaluation (workflow)
```
POST /visibility/{token}
POST /policy/{token}
POST /legal_aspects/{token}
POST /metadata/{token}
POST /interoperability/{token}
POST /security/{token}
POST /statistics/{token}
POST /services/{token}
```

### Query
```
GET /detail/{item}/{token}  # Get evaluation for specific criterion
GET /list?page=&limit=&search=  # List records
GET /summary/{token}        # Get final summary with ratings
```

## Migrations

```bash
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head
uv run alembic downgrade -1
```

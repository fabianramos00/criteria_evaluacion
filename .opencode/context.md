# Project Context: Criteria Evaluacion

## Project Overview

**Criteria Evaluacion** is a FastAPI application for evaluating repository criteria compliance. It assesses repositories against 8 criteria areas and provides ratings based on various indicators.

## Technology Stack

- **Framework**: FastAPI (Python 3.14+)
- **Database**: PostgreSQL with SQLAlchemy (async) + Alembic migrations
- **Validation**: Pydantic v2
- **HTTP Client**: httpx
- **Web Scraping**: BeautifulSoup4
- **Package Manager**: uv

## Project Structure

```
src/
├── main.py              # FastAPI app factory (create_app)
├── constants.py         # Criteria lists, ratings, metadata fields
├── api/
│   ├── routes.py        # API endpoints (8 criteria + list/summary)
│   ├── schemas.py       # Pydantic schemas with validation
│   └── services.py       # Database operations
├── core/                # Criteria evaluation modules
│   ├── visibility.py
│   ├── policy.py
│   ├── legal_aspects.py
│   ├── metadata.py
│   ├── interoperability.py
│   ├── security.py
│   ├── statistics.py
│   └── services.py
├── config/
│   └── settings.py      # Pydantic Settings (DATABASE_URL, API keys, etc.)
└── database/
    ├── session.py       # Async SQLAlchemy session
    └── models.py        # OAI_PMH, ROAR, Record models

alembic/
├── env.py              # Async migration config
└── versions/           # Database migrations

load_data/              # Data loading Jupyter notebook
.env                    # Environment variables (DATABASE_URL, API keys)
```

## Database Models

### Record (main table)
- `id` (UUID): Primary key
- `data` (JSON): Stores criteria evaluation results
- `rating` (Float): Accumulated score
- `repository_url`, `repository_names`: Repository info
- `links` (JSONB): Collected links during evaluation
- `last_item_evaluated`: Current workflow position
- `is_completed`: Workflow completion flag

### OAI_PMH, ROAR
- Reference tables for repository metadata

## API Endpoints

### Workflow (POST)
1. `POST /` - Register repository → returns token
2. `POST /visibility/{token}` - Visibility evaluation
3. `POST /policy/{token}` - Policy evaluation
4. `POST /legal_aspects/{token}` - Legal aspects evaluation
5. `POST /metadata/{token}` - Metadata evaluation
6. `POST /interoperability/{token}` - Interoperability evaluation
7. `POST /security/{token}` - Security evaluation
8. `POST /statistics/{token}` - Statistics evaluation
9. `POST /services/{token}` - Services evaluation

### Query (GET)
- `GET /detail/{item}/{token}` - Get evaluation result for specific criterion
- `GET /list?page=&limit=&search=` - List records
- `GET /summary/{token}` - Get final summary with ratings

## Criteria Ratings (max points)

| Criterion | Max Rating |
|-----------|------------|
| visibility | 9.5 |
| policy | 9 |
| legal_aspects | 5 |
| metadata | 16 |
| interoperability | 13 |
| security | 4 |
| statistics | 4 |
| services | 7 |

**Total: 67.5 points**

## Schema Validation Patterns

### Conditional Required Fields
When a boolean field is `True`, related URL fields become required:
```python
@field_validator("url_field")
def validate_required_if_condition(cls, v, info):
    if info.data.get('condition_field') and not v:
        raise ValueError('Field is required when condition is true')
    return v
```

### URL Validation
- Use `HttpUrl` type for automatic URL validation
- Use `check_website()` to verify URL accessibility
- Use `url_must_contain()` validator for URL comparison

### Validator Factories
- `conditional_required(condition_field)` - Require field when condition is true
- `url_must_contain(base_url_field)` - Validate URL matches repository URL
- `combined_validator(*validators)` - Chain multiple validators

## Code Quality Rules

1. **No Redundant Comments**: Only comment complex logic; use descriptive names
2. **Efficiency**: Prefer built-ins and standard library; optimize for readability
3. **Consistency**: Follow Python PEP 8; maintain patterns across codebase

## Project Rules

1. **Code changes via the backend agent only**: Application code (`src/`, `tests/`, `alembic/`) must only be modified by the `backend` subagent. All other agents are read-only for code and must delegate any code edits to the backend agent.
2. **Commit only when requested**: Never run `git commit`, `git commit --amend`, or `git push` unless the user explicitly asks to commit. When committing, follow the repo's conventional-commit style (`type: description`, lowercase, e.g. `feat:`, `fix:`, `refactor:`, `test:`, `perf:`).

## Database Migrations (Alembic)

```bash
# Create migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1

# History
uv run alembic history
```

## Key Files Reference

- `src/constants.py:1` - CRITERIA_LIST, CRITERIA_LIST_RATINGS
- `src/api/schemas.py:1` - All Pydantic schemas with validators
- `src/api/routes.py:38` - `get_record_or_404` dependency
- `src/core/tools.py:29` - `check_website()` function

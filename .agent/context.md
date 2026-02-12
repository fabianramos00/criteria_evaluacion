# Project Context

## Code Quality Rules

### 1. No Redundant Comments
- Avoid comments that simply restate what the code does
- Only add comments for complex logic, non-obvious decisions, or important context
- Use descriptive variable/function names instead of comments
- Remove section headers that are obvious from the code structure

### 2. Efficiency and Simplicity
- Write the simplest code that solves the problem
- Avoid over-engineering or unnecessary abstractions
- Prefer built-in functions and standard library over custom implementations
- Optimize for readability first, then performance if needed

### 3. Code Organization
- Keep related code together
- Use clear, descriptive names for variables, functions, and classes
- Follow Python PEP 8 style guidelines
- Maintain consistent patterns across the codebase

### 4. Context File Maintenance
- **Update `.agent/context.md` when there are edge changes** to the project
- Edge changes include:
  - New architectural patterns or design decisions
  - Changes to project structure or directory organization
  - Addition or removal of major dependencies or technology stack components
  - New validation patterns or coding conventions
  - Significant refactoring that changes how components interact
  - Migration milestones (e.g., Flask to FastAPI conversion progress)
- Keep the context file concise and focused on information that helps future development
- Remove outdated information when patterns or structures change

## Project Structure

This is a FastAPI application for evaluating repository criteria.

### Key Directories
- `src/api/` - API routes and schemas
- `src/` - Main application code
- `scripts/` - Utility scripts and legacy Flask code
- `.agent/` - Agent configuration and workflows

### Technology Stack
- **Backend**: FastAPI
- **Validation**: Pydantic v2
- **Database**: (To be determined from codebase)
- **Legacy**: Flask forms (being migrated to FastAPI schemas)

## Current Migration

Converting Flask WTForms to Pydantic schemas:
- Source: `scripts/forms.py` (Flask WTForms)
- Target: `src/api/schemas.py` (Pydantic schemas)
- Maintain all validation logic from original forms
- Use Pydantic's native validation features

## Validation Patterns

### Conditional Required Fields
When a boolean field is `True`, related URL fields become required:
```python
@model_validator(mode='after')
def validate_conditional_fields(self):
    if self.some_flag and not self.some_url:
        raise ValueError('some_url is required when some_flag is true')
    return self
```

### URL Validation
- Use `HttpUrl` type for automatic URL validation
- Use `validate_website()` to check URL accessibility
- Use `validate_url_contains()` for URL comparison validation

### Cross-field Validation
Use `@model_validator(mode='after')` for validations that depend on multiple fields.

## Database Migrations (Alembic)

### Setup
- Alembic is configured for async SQLAlchemy
- Metadata is imported in `alembic/env.py` from `src.database.models`

### Common Commands
- **Create Migration**: `uv run alembic revision --autogenerate -m "Description"`
- **Apply Migrations**: `uv run alembic upgrade head`
- **Rollback**: `uv run alembic downgrade -1`
- **History**: `uv run alembic history`

### Note on Async
- Alembic is configured to run migrations using `asyncpg`
- Ensure `DATABASE_URL` is set in `.env`

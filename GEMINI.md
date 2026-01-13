# Content Mate - Context Guide

This document provides a comprehensive overview of the **Content Mate** project, a multi-agent AI content creation platform based on LangGraph and MCP. Use this as a reference for understanding the architecture, development workflows, and operational procedures.

## 1. Project Overview

**Content Mate** is an autonomous content generation factory that orchestrates a team of specialized AI agents to produce high-quality content.

- **Core Goal:** Automate the entire content lifecycle: Research → Plan → Write → Edit → SEO → Visuals.
- **Key Innovation:** Combines **LangGraph** for complex stateful multi-agent workflows with **MCP (Model Context Protocol)** for standardized tool integration.
- **Architecture Pattern:** Microservices-like modularity within a monolith (FastAPI + Streamlit), containerized via Docker.

## 2. Development Environment & Tech Stack

- **Language:** Python 3.11+
- **Package Manager:** [uv](https://docs.astral.sh/uv/) (**Strictly enforce: No `pip` usage**)
- **Backend Framework:** FastAPI (Async, Pydantic v2)
- **Frontend Framework:** Streamlit
- **Linters & Formatters:** `ruff`
- **Type Checker:** `mypy`
- **Testing:** `pytest` + `pytest-asyncio`
- **Databases:** PostgreSQL, Redis

## 3. Essential Commands

Execute these commands from the project root.

```bash
# Install Dependencies (Syncs with pyproject.toml)
uv sync

# Run Development Server
uv run uvicorn src.api.main:app --reload

# Run All Tests (Stop on first failure, verbose)
uv run pytest -x -v tests/

# Run Specific Test File
uv run pytest -x -v tests/test_api/test_auth.py

# Run Single Test Case
uv run pytest -x -v tests/test_api/test_auth.py::test_login

# Code Formatting
uv run ruff format .

# Linting
uv run ruff check . --fix

# Type Checking
uv run mypy src/
```

## 4. Code Style & Rules

### MUST DO

- **Type Hints:** All functions must have type hints.
- **Pydantic:** Use Pydantic models for all request/response schemas.
- **Async:** Use `async def` for I/O bound operations. Avoid synchronous functions in API routes.
- **Error Handling:** Use `HTTPException` for API errors.
- **Configuration:** Manage environment variables via `pydantic-settings`.

### NEVER DO

- **No Print:** Do not use `print()`. Use `logger` (from `loguru` or standard lib).
- **No Generic Args:** Avoid `*args`, `**kwargs` abuse. Be explicit.
- **No `Any`:** Minimize the use of `Any` type.
- **No Hardcoding:** Never hardcode configuration values (API keys, URLs).

### Naming Conventions

- **Functions/Variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Files:** `snake_case.py`

## 5. Project Structure

```text
content-mate/
├── src/                      # Source Code
│   ├── agents/               # specialized AI Agents (Researcher, Writer, etc.)
│   ├── api/                  # FastAPI application
│   │   ├── routes/           # API Endpoints
│   │   └── main.py           # Entry point
│   ├── db/                   # Database connection & models
│   ├── mcp/                  # MCP Client and Server implementations
│   ├── models/               # Pydantic data models & Domain models
│   ├── services/             # Business logic layer
│   ├── utils/                # Config, logging, common utilities
│   └── workflows/            # LangGraph pipelines
├── ui/                       # Streamlit Frontend application
├── tests/                    # Pytest suite
└── docker/                   # Docker config
```

## 6. Common Mistakes (Avoid These!)

1.  ❌ `from src.models import *`
    ✅ `from src.models.user import User` (Explicit imports)

2.  ❌ Creating DB sessions directly in functions
    ✅ Use `Depends(get_db)` (Dependency Injection)

3.  ❌ Blocking I/O in async functions
    ✅ Use `await` or `run_in_executor` for blocking synchronous calls.

## 7. Git Workflow

- **Branches:** `feature/feature-name`, `fix/bug-name`
- **Commits:** Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat: add login`, `fix: resolve auth error`).
- **Pre-Push:** Ensure `pytest`, `mypy`, and `ruff` pass before pushing or opening a PR.

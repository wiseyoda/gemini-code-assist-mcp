# Repository Guidelines

## Project Structure & Module Organization
- `src/main.py` starts the MCP server; CLI entrypoint lives in `src/cli`.
- Core logic is in `src/core`, feature tools under `src/features/*`, and server adapters in `src/server`.
- Tests sit next to code in `src/*/tests`; root smoke tests include `test_installation.py`, `test_cli.py`, and `test_code.py`.
- Helper scripts: `run_tests.py` (pytest wrapper) and `GEMINI.md`/`CLAUDE.md` for agent behavior notes.

## Build, Test, and Development Commands
- Install deps: `uv sync`
- Run server locally: `uv run python src/main.py`
- Try the CLI: `uv run gemini-mcp-cli --show-prompts review file --file example.py`
- Full test suite: `uv run pytest` (or `python run_tests.py --coverage` for HTML coverage)
- Quality checks: `uv run ruff format .`, `uv run ruff check .`, `uv run mypy .`

## Coding Style & Naming Conventions
- Python 3.11+ with full type hints; keep functions/classes small and purposeful.
- Ruff enforces 88-char lines, double quotes, import sorting, and common pycodestyle/bugbear rules; Black-style formatting via `ruff format`.
- Tests follow `test_*.py` with `Test*` classes and `test_*` functions. Use descriptive, action-oriented names for tools and CLI commands.
- Branch naming: `feature/...`, `fix/...`, `docs/...`, `refactor/...`.

## Testing Guidelines
- Add or update tests beside the code you change in `src/*/tests`; mock external Gemini/Cloud calls.
- Pytest is configured with `asyncio_mode=auto`; prefer async fixtures where applicable.
- Aim for ≥80% coverage; use `uv run pytest --cov=src --cov-report=term-missing` or `--cov-report=html` to review gaps.
- For CLI/server flows, include end-to-end samples when feasible (e.g., `uv run gemini-mcp-cli status check`).

## Commit & Pull Request Guidelines
- Use conventional-style messages (`feat: ...`, `fix: ...`, `docs: ...`); keep commits atomic and scoped.
- PRs should include a clear summary, linked issues, breaking-change notes, and test evidence (pytest/lint/type checks).
- Update documentation when flags, prompts, or tool interfaces change; include screenshots or sample outputs for UX-facing updates.
- Request review after checks pass; respond promptly to feedback and keep branch history clean.

## Security & Configuration Tips
- Do not commit credentials, gcloud tokens, or API outputs; prefer environment variables like `GEMINI_DEBUG` and `GEMINI_SANDBOX`.
- Validate Gemini CLI availability and authentication in new code paths; fail fast with actionable error messages.
- Keep dependencies pinned via `pyproject.toml` + `uv.lock`; avoid manual edits to generated files.

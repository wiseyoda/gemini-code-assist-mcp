# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gemini Code Assist MCP** - A Model Context Protocol server that integrates Google Gemini CLI with Claude Code for AI-powered development assistance. Uses existing Google Cloud authentication (no API key needed).

**Prerequisites**:
- Python 3.11+
- Gemini CLI installed: `npm install -g @google/gemini-cli`
- Google authentication: `gcloud auth login`

## Development Commands

```bash
# Setup
uv venv && uv sync

# Run tests
uv run pytest                           # All tests
uv run pytest src/core/tests/ -v        # Specific module
uv run pytest --cov=src --cov-report=html  # With coverage

# Code quality
uv run ruff format .                    # Format
uv run ruff check .                     # Lint
uv run mypy .                           # Type check

# Run server
uv run python src/main.py               # Start MCP server
uv run mcp dev src/main.py              # Development mode with MCP Inspector

# CLI testing
uv run gemini-mcp-cli status check
uv run gemini-mcp-cli --show-prompts review file --file code.py

# Package management
uv add <package>                        # Add dependency
uv remove <package>                     # Remove dependency
```

## Architecture

Vertical slice architecture with tests co-located with code:

```
src/
├── main.py                    # Entry point, exposes FastMCP server as `mcp`/`server`/`app`
├── server/
│   └── gemini_server.py       # FastMCP server with tools: gemini_review_code,
│                              # gemini_proofread_feature_plan, gemini_analyze_bug,
│                              # gemini_explain_code + MCP resources
├── core/
│   ├── gemini_client.py       # GeminiCLIClient wrapper (subprocess to Gemini CLI)
│   ├── config.py              # ServerConfig, PromptTemplate, ConfigManager
│   └── tests/
├── cli/
│   ├── main.py                # Click CLI entry point
│   ├── commands/              # review, feature, bug, explain, status commands
│   └── utils/                 # OutputFormatter, file utilities
└── features/                  # Feature modules (analysis, proofreading, utilities)
```

### Key Data Flow

1. MCP tools in `gemini_server.py` receive requests
2. Tools use `ConfigManager` to get prompt templates
3. `GeminiCLIClient.call_with_structured_prompt()` builds and executes CLI commands
4. Gemini CLI runs via `asyncio.subprocess`, authenticates via gcloud
5. Response parsed and returned as Pydantic models

## Code Guidelines

- **File limits**: <500 lines per file, <50 lines per function/class
- **Style**: PEP8, type hints required, format with `ruff`
- **Validation**: Use Pydantic v2 models for all data structures
- **Docstrings**: Google style for all functions
- **Tests**: Co-located in `tests/` directories, always test new features
- **Comments**: Add `# Reason:` for non-obvious logic

## Key Types & Patterns

```python
# Gemini client
from src.core.gemini_client import GeminiOptions, GeminiResponse, GeminiCLIClient

# Configuration
from src.core.config import ServerConfig, PromptTemplate, ConfigManager

# MCP responses
from src.server.gemini_server import CodeReviewResponse, GeminiToolResponse
```

### MCP Tool Pattern

```python
@mcp.tool()
async def tool_name(
    required_arg: str,
    ctx: Context,
    optional_arg: str | None = "default",
) -> GeminiToolResponse:
    """Tool description."""
    await ctx.info("Starting operation")
    try:
        template = config_manager.get_template("template_name")
        system_prompt, user_prompt = template.format(**kwargs)
        response = await gemini_client.call_with_structured_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        return GeminiToolResponse(result=response.content, ...)
    except Exception as e:
        await ctx.error(f"Error: {str(e)}")
        return error_response
```

### Adding New Tools

1. Add `PromptTemplate` in `ConfigManager._load_default_templates()` (`src/core/config.py`)
2. Add tool function with `@mcp.tool()` decorator in `create_server()` (`src/server/gemini_server.py`)
3. Add CLI command in `src/cli/commands/`
4. Add tests in corresponding `tests/` directories

## Dependencies

- **mcp >= 1.0.0**: Model Context Protocol SDK (FastMCP)
- **pydantic >= 2.0.0**: Data validation
- **click >= 8.0.0**: CLI framework
- **rich >= 12.0.0**: Terminal formatting

## Behavioral Guidelines

- Always use `uv run` for commands
- Always confirm file paths exist before using them
- Keep README.md and CLAUDE.md updated with changes
- Branch naming: `feature/`, `fix/`, `docs/`, `refactor/`


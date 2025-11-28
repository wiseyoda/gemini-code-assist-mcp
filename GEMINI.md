# Gemini Code Assist MCP

## Project Overview

**Gemini Code Assist MCP** is a Python-based Model Context Protocol (MCP) server that integrates the Google Gemini CLI into development workflows, specifically designed for Claude Code and Claude Desktop. It acts as a bridge, allowing users to leverage Gemini's capabilities (code review, bug analysis, feature planning) directly within their MCP-enabled environments without requiring a direct API key (uses Google Cloud auth).

### Key Technologies
*   **Language:** Python 3.11+
*   **Package Manager:** `uv`
*   **Core Library:** `mcp` (FastMCP)
*   **Integration:** Google Gemini CLI (`@google/gemini-cli`)
*   **Quality Tools:** `ruff` (linting/formatting), `mypy` (type checking), `pytest` (testing)

### Architecture
The project follows a **vertical slice architecture**:
*   `src/main.py`: Application entry point. Exposes the `mcp` server object.
*   `src/server/`: Contains the FastMCP server implementation (`gemini_server.py`) and tool definitions.
*   `src/core/`: Shared utilities, configuration (`config.py`), and the Gemini CLI wrapper (`gemini_client.py`).
*   `src/features/`: Feature-specific logic (e.g., analysis, proofreading).
*   `src/cli/`: A standalone CLI tool (`gemini-mcp-cli`) for testing and interacting with the server features directly.

## Building and Running

### Prerequisites
1.  **Google Gemini CLI:** `npm install -g @google/gemini-cli`
2.  **Google Auth:** `gcloud auth login`
3.  **Python & UV:** Python 3.11+ and `uv` installed.

### Installation
```bash
# Clone and setup dependencies
uv sync
```

### Running the Server
To start the MCP server (stdio mode):
```bash
uv run python src/main.py
```

### Using the CLI
The project includes a CLI for testing features without a full MCP client:
```bash
# Check status
uv run gemini-mcp-cli status check

# Review a file
uv run gemini-mcp-cli review file --file src/main.py
```

### Running Tests
```bash
# Run the comprehensive test suite
uv run pytest

# Run the quick installation verification script
uv run python test_installation.py
```

### Installing in Claude Code
```bash
uv run mcp install src/main.py --name "Gemini Assistant"
```

## Development Conventions

**Refere strictly to `CLAUDE.md` for detailed guidelines.**

*   **Code Style:** Follow PEP 8. Use `ruff` for formatting and linting.
    *   `uv run ruff format .`
    *   `uv run ruff check .`
*   **Type Safety:** All code must be type-hinted. Use `mypy` for verification.
    *   `uv run mypy .`
*   **Structure:**
    *   **Files:** < 500 lines.
    *   **Functions/Classes:** < 50 lines.
    *   **Vertical Slices:** Keep related code and tests together.
*   **Testing:**
    *   Write `pytest` unit tests for all new features.
    *   Place tests in a `tests/` directory next to the code they test.
*   **Documentation:**
    *   Every function and class must have a Google-style docstring.
    *   Update `README.md` and `CLAUDE.md` when architecture or dependencies change.

## Key Files

*   `src/main.py`: The entry point for the MCP server.
*   `src/server/gemini_server.py`: Defines the MCP tools (`gemini_review_code`, `gemini_analyze_bug`, etc.) and resources.
*   `src/core/gemini_client.py`: Handles the interaction with the external Gemini CLI process.
*   `pyproject.toml`: Defines dependencies and build configuration.
*   `CLAUDE.md`: Validated source of truth for coding standards and behavioral guidelines.

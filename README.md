# Gemini Code Assist MCP

[![CI](https://github.com/YOUR-USERNAME/gemini-code-assist-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USERNAME/gemini-code-assist-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io)

A Model Context Protocol (MCP) server that integrates Google Gemini CLI with Claude Code for AI-powered development assistance.

**Key Features:**
- No API key required - uses your existing Google Cloud authentication
- Works with Claude Code and Claude Desktop
- Includes CLI for testing and standalone use

## Quick Start

```bash
# 1. Install prerequisites
npm install -g @google/gemini-cli
gcloud auth login

# 2. Clone and install
git clone https://github.com/YOUR-USERNAME/gemini-code-assist-mcp.git
cd gemini-code-assist-mcp
uv sync

# 3. Verify installation
uv run gemini-mcp-cli status check

# 4. Install in Claude Code
uv run mcp install src/main.py --name "Gemini Assistant"
```

## Available Tools

| Tool | Description |
|------|-------------|
| `gemini_review_code` | Analyze code quality, security, performance, and style |
| `gemini_proofread_feature_plan` | Review and improve feature specifications |
| `gemini_analyze_bug` | Analyze bugs with root cause identification and fix suggestions |
| `gemini_explain_code` | Explain code functionality at varying detail levels |

## Prerequisites

1. **Google Gemini CLI** - [Installation guide](https://github.com/google-gemini/gemini-cli)
   ```bash
   npm install -g @google/gemini-cli
   ```

2. **Google Cloud authentication**
   ```bash
   gcloud auth login
   ```

3. **Python 3.11+ with UV**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Installation

### Claude Code Setup

**Option 1: MCP Install Command (Recommended)**
```bash
uv run mcp install src/main.py --name "Gemini Assistant"
```

**Option 2: Manual Configuration**

Add to `~/.claude/settings.json`:
```json
{
  "mcp": {
    "servers": {
      "gemini-code-assist": {
        "command": "uv",
        "args": ["run", "python", "src/main.py"],
        "cwd": "/absolute/path/to/gemini-code-assist-mcp"
      }
    }
  }
}
```

### Claude Desktop Setup

Edit `claude_desktop_config.json`:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gemini-code-assist": {
      "command": "uv",
      "args": ["run", "python", "/absolute/path/to/gemini-code-assist-mcp/src/main.py"]
    }
  }
}
```

## CLI Usage

Test functionality without MCP:

```bash
# Check status
uv run gemini-mcp-cli status check

# Code review
uv run gemini-mcp-cli review file --file code.py --focus security
uv run gemini-mcp-cli --show-prompts review file --file code.py  # See prompts

# Bug analysis
uv run gemini-mcp-cli bug analyze --description "App crashes" --code-file main.py

# Code explanation
uv run gemini-mcp-cli explain file --file complex.py --level intermediate

# Feature plan review
uv run gemini-mcp-cli feature review --file plan.md
```

**Global options:** `--json`, `--verbose`, `--debug`, `--show-prompts`, `--model <model>`

## Configuration

### Server Options

```python
from src.core.config import ServerConfig, GeminiOptions

config = ServerConfig(
    gemini_options=GeminiOptions(
        model="gemini-3-pro-preview",
        sandbox=False,
        debug=False
    ),
    enable_caching=True,
    max_file_size_mb=10.0
)
```

### MCP Resources

- `gemini://config` - Current configuration
- `gemini://templates` - Available prompt templates
- `gemini://status` - CLI status and authentication

## Development

```bash
# Install with dev dependencies
make install

# Run quality checks
make check      # lint + typecheck + test

# Individual commands
make lint       # ruff check
make fmt        # ruff format
make typecheck  # mypy
make test       # pytest
make test-cov   # pytest with coverage

# Run server
make serve
```

### Project Structure

```
src/
├── main.py                 # Entry point (exposes mcp/server/app)
├── server/
│   └── gemini_server.py    # MCP tools and resources
├── core/
│   ├── gemini_client.py    # Gemini CLI wrapper
│   └── config.py           # Configuration and templates
├── cli/
│   ├── main.py             # CLI entry point
│   └── commands/           # CLI commands
└── features/               # Feature modules
```

## Troubleshooting

### Common Issues

**"Gemini CLI not found"**
```bash
npm install -g @google/gemini-cli
gemini --help  # Verify installation
```

**Authentication errors**
```bash
gcloud auth login
gcloud auth list  # Verify active account
gemini -p "test"  # Test directly
```

**MCP server not appearing**
- Verify JSON syntax in config file
- Use absolute paths, not relative
- Restart Claude after config changes

**Debug mode**
```bash
uv run gemini-mcp-cli --debug status check
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run quality checks (`make check`)
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

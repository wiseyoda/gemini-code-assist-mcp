# Gemini Code Assist MCP

[![Version](https://img.shields.io/badge/version-0.1.3-blue.svg)](https://github.com/VinnyVanGogh/gemini-code-assist-mcp/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io)

A robust Model Context Protocol (MCP) server that integrates Google Gemini CLI with Claude Code for AI-powered development assistance.

🌟 **No API key required** - Uses your existing Google Cloud authentication  
🚀 **Claude Code compatible** - Works seamlessly with both Claude Code and Claude Desktop  
🔍 **Comprehensive analysis** - Code review, bug analysis, feature planning, and code explanation  
🛠️ **CLI interface** - Test and develop with the included CLI tool

## Quick Start

1. **Install and authenticate Gemini CLI**:
   ```bash
   npm install -g @google/gemini-cli
   gcloud auth login
   ```

2. **Clone and install the MCP server**:
   ```bash
   git clone https://github.com/VinnyVanGogh/gemini-code-assist-mcp.git
   cd gemini-code-assist-mcp
   uv sync
   ```

3. **Test the CLI**:
   ```bash
   uv run gemini-mcp-cli --show-prompts review file --file your_code.py
   ```

4. **Set up in Claude Code** (see [Claude Code Setup](#claude-code-setup) below)

## Features

This MCP server provides the following tools for development assistance:

### 🔍 Code Analysis & Review
- **`gemini_review_code`**: Comprehensive code review with quality, security, and performance analysis
- **`gemini_analyze_security`**: Security-focused code analysis

### 📋 Feature Planning & Documentation  
- **`gemini_proofread_feature_plan`**: Review and improve feature specifications
- **`gemini_suggest_implementation`**: Implementation guidance and architecture suggestions

### 🐛 Bug Analysis & Debugging
- **`gemini_analyze_bug`**: Root cause analysis and fix suggestions
- **`gemini_debug_assistance`**: Debugging workflow assistance

### 📖 Code Understanding
- **`gemini_explain_code`**: Clear code explanations with varying detail levels
- **`gemini_generate_tests`**: AI-assisted test generation

## Prerequisites

Before using this MCP server, ensure you have:

1. **Gemini CLI installed and configured**
   ```bash
   # Install Gemini CLI (follow Google's official instructions)
   # https://github.com/google-gemini/gemini-cli
   ```

2. **Google authentication set up**
   ```bash
   # Authenticate with Google (no API key needed)
   gcloud auth login
   ```

3. **Python 3.11+ with UV package manager**
   ```bash
   # Install UV if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Installation

1. **Clone and install the MCP server**:
   ```bash
   git clone <repository-url>
   cd gemini-mcp-server
   uv sync
   ```

2. **Test the installation**:
   ```bash
   # Test Gemini CLI access
   gemini --help
   
   # Test the MCP server
   uv run python src/main.py
   ```

3. **Test the installation**:
   ```bash
   # Run installation tests
   uv run python test_installation.py
   ```

4. **Install in Claude Code**:
   ```bash
   # Install the server for Claude Code (recommended)
   uv run mcp install src/main.py
   
   # Or with a custom name
   uv run mcp install src/main.py --name "Gemini Assistant"
   
   # Alternative: Manual installation with JSON
   claude mcp add '{
     "name": "Gemini Code Assist",
     "command": "uv",
     "args": ["run", "python", "src/main.py"],
     "cwd": "/Users/your-username/path/to/gemini-code-assist-mcp",
     "env": {
       "GEMINI_DEBUG": "false"
     }
   }'
   ```

## Claude Code Setup

### Method 1: Local MCP Server (Recommended)

1. **Install the MCP server**:
   ```bash
   git clone https://github.com/VinnyVanGogh/gemini-code-assist-mcp.git
   cd gemini-code-assist-mcp
   uv sync
   ```

2. **Configure Claude Code**:
   - Open Claude Code
   - Navigate to Settings > MCP Servers
   - Add a new server with these settings:
     - **Name**: `Gemini Code Assist`
     - **Command**: `uv`
     - **Args**: `["run", "python", "src/main.py"]`
     - **Working Directory**: `/path/to/gemini-code-assist-mcp`

3. **Alternative: Edit configuration file**:
   ```bash
   # Edit your Claude Code configuration
   code ~/.claude/settings.json
   ```
   
   Add this configuration:
   ```json
   {
     "mcp": {
       "servers": {
         "gemini-code-assist": {
           "command": "uv",
           "args": ["run", "python", "src/main.py"],
           "cwd": "/path/to/gemini-code-assist-mcp",
           "env": {
             "GEMINI_DEBUG": "false"
           }
         }
       }
     }
   }
   ```

### Method 2: Claude Desktop Configuration

For Claude Desktop users, edit `claude_desktop_config.json`:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gemini-code-assist": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/path/to/gemini-code-assist-mcp/src/main.py"
      ],
      "env": {
        "GEMINI_DEBUG": "false",
        "GEMINI_SANDBOX": "false"
      }
    }
  }
}
```

### Method 3: Remote MCP Server

For remote deployment, you can host the MCP server and connect via URL:

```json
{
  "mcpServers": {
    "gemini-code-assist": {
      "url": "https://your-deployment-url.com/mcp",
      "auth": {
        "type": "bearer",
        "token": "your-auth-token"
      }
    }
  }
}
```

### Verification

After configuration, restart Claude Code/Desktop and verify the server is loaded:

1. Check the MCP servers list in settings
2. Look for "Gemini Code Assist" in available tools
3. Try using a tool to confirm it works

## Usage in Claude Code

Once installed, you can use the Gemini tools directly in Claude Code:

### Code Review Example
```
@gemini_review_code
{
  "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
  "language": "python",
  "focus": "performance"
}
```

### Feature Plan Review Example
```
@gemini_proofread_feature_plan
{
  "feature_plan": "Add user authentication with OAuth2...",
  "context": "Web application with React frontend",
  "focus_areas": "security,usability,implementation"
}
```

### Bug Analysis Example
```
@gemini_analyze_bug
{
  "bug_description": "Application crashes when processing large files",
  "code_context": "def process_file(filepath):\n    with open(filepath) as f:\n        return f.read()",
  "error_logs": "MemoryError: Unable to allocate array",
  "environment": "Python 3.11, 8GB RAM"
}
```

## Configuration

### Server Configuration

The server can be configured by modifying the `ServerConfig` in `src/core/config.py`:

```python
config = ServerConfig(
    name="Custom Gemini Server",
    gemini_options=GeminiOptions(
        model="gemini-3-pro-preview",  # or "gemini-2.5-pro"
        sandbox=False,           # Enable sandbox mode
        debug=False             # Enable debug logging
    ),
    enable_caching=True,
    max_file_size_mb=10.0
)
```

### Gemini CLI Options

The server supports all major Gemini CLI options:

- `model`: Choose the Gemini model (`gemini-2.5-pro`, `gemini-pro`)
- `sandbox`: Run in sandbox mode for code execution
- `debug`: Enable detailed logging
- `all_files`: Include all files in context
- `yolo`: Auto-accept all actions
- `checkpointing`: Enable file edit checkpointing

### Custom Templates

You can add custom prompt templates by extending the `ConfigManager`:

```python
from src.core.config import ConfigManager, PromptTemplate

manager = ConfigManager()
custom_template = PromptTemplate(
    name="custom_review",
    description="Custom code review template",
    system_prompt="You are a specialized reviewer for...",
    user_template="Review this {language} code: {code}",
    variables={"language": "Programming language", "code": "Code to review"}
)
manager.add_template(custom_template)
```

## Available Resources

The server exposes several MCP resources for inspection:

- **`gemini://config`**: Current server configuration
- **`gemini://templates`**: Available prompt templates
- **`gemini://status`**: Gemini CLI status and authentication info

Access these in Claude Code:
```
Can you show me the current Gemini configuration?
# Claude will automatically fetch gemini://config resource
```

## CLI Usage

The included CLI tool allows you to test and use Gemini functionality directly:

### Basic Commands

```bash
# Check version
uv run gemini-mcp-cli version

# Show help
uv run gemini-mcp-cli --help

# Check status and authentication
uv run gemini-mcp-cli status check
```

### Code Review

```bash
# Review a Python file
uv run gemini-mcp-cli review file --file code.py --focus security

# Review with input/output transparency
uv run gemini-mcp-cli --show-prompts review file --file code.py

# Review from stdin
cat code.py | uv run gemini-mcp-cli review stdin --focus performance

# Output as JSON
uv run gemini-mcp-cli --json review file --file code.py
```

### Feature Planning

```bash
# Review a feature plan
uv run gemini-mcp-cli feature review --file feature-plan.md

# Interactive feature planning
uv run gemini-mcp-cli feature interactive
```

### Bug Analysis

```bash
# Analyze a bug with context
uv run gemini-mcp-cli bug analyze --description "App crashes on startup" --code-file main.py

# Interactive bug analysis
uv run gemini-mcp-cli bug interactive
```

### Code Explanation

```bash
# Explain code at different levels
uv run gemini-mcp-cli explain file --file complex.py --level beginner
uv run gemini-mcp-cli explain file --file algorithm.py --level advanced
```

### Global Options

- `--show-prompts`: Show input prompts and raw responses for transparency
- `--json`: Output results in JSON format
- `--verbose`: Enable verbose output
- `--debug`: Enable debug mode
- `--no-color`: Disable colored output
- `--model`: Specify Gemini model (default: gemini-3-pro-preview)
- `--sandbox`: Enable sandbox mode

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test files
uv run pytest src/core/tests/test_gemini_client.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Run linter
uv run ruff check .

# Run type checker
uv run mypy .
```

### Development Mode

For development and testing:

```bash
# Run server in development mode
uv run mcp dev src/main.py

# This allows testing with MCP Inspector
# Visit the provided URL to test tools interactively
```

## Architecture

The server follows a vertical slice architecture:

```
src/
├── main.py                 # Entry point
├── server/                 # FastMCP server implementation
│   ├── gemini_server.py   # Main server with tools
│   └── tests/
├── core/                   # Core utilities
│   ├── gemini_client.py   # Gemini CLI wrapper
│   ├── config.py          # Configuration management
│   └── tests/
├── features/               # Feature modules
│   ├── proofreading/      # Review and proofreading
│   ├── analysis/          # Bug and code analysis
│   ├── utilities/         # Helper utilities
│   └── tests/
└── templates/              # Prompt templates
```

### Key Components

1. **GeminiCLIClient**: Handles subprocess calls to Gemini CLI with proper authentication
2. **ConfigManager**: Manages server configuration and prompt templates
3. **FastMCP Server**: Implements MCP tools and resources
4. **Prompt Templates**: Structured prompts for different use cases

## Troubleshooting

### Common Issues

1. **"Gemini CLI not found"**
   ```bash
   # Install Gemini CLI
   npm install -g @google/gemini-cli
   
   # Verify installation
   which gemini
   gemini --help
   ```

2. **Authentication errors**
   ```bash
   # Authenticate with Google Cloud
   gcloud auth login
   
   # Test authentication
   gemini -p "Hello world"
   ```

3. **"Command failed with exit code 1"**
   - Check your Google authentication status: `gcloud auth list`
   - Verify you have access to Gemini models
   - Check internet connectivity
   - Try with `--debug` flag: `uv run gemini-mcp-cli --debug status check`

4. **Tool timeouts**
   - Large code files may take time to process
   - Consider breaking down large requests
   - Check if you've hit rate limits (60 requests/minute, 1000/day)

5. **MCP Server not appearing in Claude**
   - Verify configuration file syntax with a JSON validator
   - Check that file paths are absolute, not relative
   - Restart Claude Code/Desktop after configuration changes
   - Check Claude's MCP server logs for errors

6. **"No such option: --show-prompts"**
   - Make sure you're using the latest version: `uv run gemini-mcp-cli version`
   - The option must come before the command: `--show-prompts review file` not `review file --show-prompts`

7. **MCP Server "Not connected" or timeout errors**
   - Restart Claude Code after adding the MCP server
   - Verify the server is running: `uv run python src/main.py` (should start without errors)
   - Check that the working directory path is absolute and correct
   - Verify Google authentication: `gemini -p "test"`
   - Try removing and re-adding the MCP server configuration

8. **"No server object found" during MCP install**
   - This was fixed in v0.1.3 - make sure you're using the latest version
   - If still occurring, try the manual installation method above

### Debug Mode

Enable debug mode for detailed logging:

```bash
# CLI debug mode
uv run gemini-mcp-cli --debug status check

# Environment variable
export GEMINI_DEBUG=true
```

### Getting Help

1. **Check the documentation** in this README
2. **Use the CLI help**: `uv run gemini-mcp-cli --help`
3. **Check existing issues** on GitHub
4. **Create a new issue** with:
   - Your operating system and Python version
   - Complete error messages
   - Steps to reproduce the problem
   - Output of `uv run gemini-mcp-cli status check`


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the code style guidelines
4. Add tests for new functionality
5. Run the test suite and ensure all tests pass
6. Submit a pull request

### Code Style

- Follow PEP 8
- Use type hints for all functions
- Add docstrings for all public functions and classes
- Keep functions under 50 lines
- Keep classes under 50 lines
- Use Pydantic models for data validation

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Search existing issues in the repository
3. Create a new issue with detailed information about your problem

## Acknowledgments

- Google Gemini team for the excellent CLI tool
- Anthropic for the Model Context Protocol
- The open-source community for various dependencies
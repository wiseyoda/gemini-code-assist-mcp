"""
Main CLI entry point for Gemini MCP Server.
"""

import sys
from pathlib import Path

import click

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cli.utils.output import OutputFormatter
from src.cli.commands.review import review
from src.cli.commands.feature import feature
from src.cli.commands.bug import bug
from src.cli.commands.explain import explain
from src.cli.commands.status import status


@click.group()
@click.option(
    '--config',
    type=click.Path(exists=True),
    help='Path to configuration file'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.option(
    '--debug', '-d',
    is_flag=True,
    help='Enable debug output'
)
@click.option(
    '--json',
    is_flag=True,
    help='Output results in JSON format'
)
@click.option(
    '--no-color',
    is_flag=True,
    help='Disable colored output'
)
@click.option(
    '--model', '-m',
    default='gemini-3-pro-preview',
    help='Gemini model to use'
)
@click.option(
    '--sandbox', '-s',
    is_flag=True,
    help='Run in sandbox mode'
)
@click.option(
    '--show-prompts',
    is_flag=True,
    help='Show input prompts and raw responses'
)
@click.pass_context
def cli(ctx, config, verbose, debug, json, no_color, model, sandbox, show_prompts):
    """
    Gemini MCP Server CLI - Test and use Gemini AI tools from the command line.
    
    This CLI provides access to all the functionality of the Gemini MCP server
    for testing and manual usage before deploying as an MCP server.
    
    Examples:
        gemini-mcp-cli review file --file code.py --focus security
        gemini-mcp-cli feature review --file plan.md
        gemini-mcp-cli bug analyze --interactive
        gemini-mcp-cli status check
    """
    # Ensure ctx.obj exists
    ctx.ensure_object(dict)
    
    # Store global options in context
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    ctx.obj['json'] = json
    ctx.obj['use_color'] = not no_color
    ctx.obj['model'] = model
    ctx.obj['sandbox'] = sandbox
    ctx.obj['show_prompts'] = show_prompts
    
    # Create output formatter
    ctx.obj['formatter'] = OutputFormatter(
        use_color=not no_color,
        json_output=json
    )
    
    # Enable debug mode if requested
    if debug:
        ctx.obj['formatter'].info(f"Debug mode enabled")
        ctx.obj['formatter'].info(f"Using model: {model}")
        if sandbox:
            ctx.obj['formatter'].info("Sandbox mode enabled")


# Add command groups
cli.add_command(review)
cli.add_command(feature)
cli.add_command(bug)
cli.add_command(explain)
cli.add_command(status)


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    formatter = ctx.obj['formatter']
    
    version_info = {
        "version": "0.1.3",
        "description": "Gemini MCP Server CLI",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    
    if ctx.obj['json']:
        import json
        click.echo(json.dumps(version_info, indent=2))
    else:
        formatter.console.print(f"Gemini MCP Server CLI v{version_info['version']}")
        formatter.console.print(f"Python {version_info['python_version']}")


@cli.command()
@click.pass_context
def examples(ctx):
    """Show usage examples."""
    formatter = ctx.obj['formatter']
    
    if ctx.obj['json']:
        return
    
    examples_text = """
🚀 Gemini CLI Usage Examples

📋 Code Review:
  gemini-mcp-cli review file --file my_code.py --focus security
  gemini-mcp-cli review file --file app.js --language javascript --focus performance
  cat code.py | gemini-mcp-cli review stdin --focus bugs

📝 Feature Planning:
  gemini-mcp-cli feature review --file feature-plan.md --context "React app"
  echo "Add user auth..." | gemini-mcp-cli feature review --focus security,implementation

🐛 Bug Analysis:
  gemini-mcp-cli bug analyze --description "App crashes" --code-file buggy.py
  gemini-mcp-cli bug analyze --interactive

📖 Code Explanation:
  gemini-mcp-cli explain file --file complex.py --level intermediate
  gemini-mcp-cli explain file --file lambda.py --level basic --questions "How does this work?"

🔧 Status & Configuration:
  gemini-mcp-cli status check
  gemini-mcp-cli status config
  gemini-mcp-cli status templates

⚙️  Global Options:
  --json              Output in JSON format
  --no-color          Disable colored output
  --verbose           Enable verbose logging
  --debug             Enable debug information
  --model gemini-pro  Use different model
  --sandbox           Enable sandbox mode

For detailed help on any command:
  gemini-mcp-cli <command> --help
"""
    
    formatter.console.print(examples_text)


if __name__ == "__main__":
    cli()
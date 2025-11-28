"""
Status and configuration commands.
"""

import asyncio
import json
import sys
from pathlib import Path

import click

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.core.config import ConfigManager
from src.core.gemini_client import GeminiCLIClient, GeminiOptions


@click.group()
def status():
    """Status and configuration commands."""
    pass


@status.command()
@click.pass_context
async def check(ctx):
    """Check Gemini CLI status and authentication."""
    formatter = ctx.obj["formatter"]

    try:
        # Create Gemini client with options from context
        options = GeminiOptions(
            model=ctx.obj["model"], sandbox=ctx.obj["sandbox"], debug=ctx.obj["debug"]
        )

        client = GeminiCLIClient(options)

        if ctx.obj["verbose"]:
            formatter.info("Checking Gemini CLI availability...")

        # Test authentication
        auth_valid = await client.verify_authentication()

        status_info = {
            "authenticated": auth_valid,
            "model": options.model,
            "cli_available": True,
            "sandbox_mode": options.sandbox,
        }

        formatter.print_status(status_info)

    except Exception as e:
        error_status = {"authenticated": False, "error": str(e), "cli_available": False}
        formatter.print_status(error_status)
        if not ctx.obj["json"]:
            formatter.error(f"Status check failed: {str(e)}")
        sys.exit(1)


@status.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    formatter = ctx.obj["formatter"]

    try:
        config_manager = ConfigManager()
        config_dict = config_manager.get_config_dict()

        # Add CLI-specific options
        config_dict["cli_options"] = {
            "model": ctx.obj["model"],
            "sandbox": ctx.obj["sandbox"],
            "debug": ctx.obj["debug"],
            "verbose": ctx.obj["verbose"],
        }

        formatter.print_config(config_dict)

    except Exception as e:
        formatter.error(f"Failed to load configuration: {str(e)}")
        sys.exit(1)


@status.command()
@click.pass_context
def templates(ctx):
    """List available prompt templates."""
    formatter = ctx.obj["formatter"]

    try:
        config_manager = ConfigManager()
        templates = config_manager.list_templates()

        formatter.print_templates(templates)

    except Exception as e:
        formatter.error(f"Failed to list templates: {str(e)}")
        sys.exit(1)


@status.command()
@click.pass_context
async def auth(ctx):
    """Test Gemini CLI authentication."""
    formatter = ctx.obj["formatter"]

    try:
        options = GeminiOptions(
            model=ctx.obj["model"], sandbox=ctx.obj["sandbox"], debug=ctx.obj["debug"]
        )

        client = GeminiCLIClient(options)

        if ctx.obj["verbose"]:
            formatter.info("Testing authentication with simple prompt...")

        # Test with a simple prompt
        response = await client.call_gemini("Say hello")

        if response.success:
            auth_result = {
                "authenticated": True,
                "test_response": response.content[:100] + "..."
                if len(response.content) > 100
                else response.content,
                "model": options.model,
            }

            if ctx.obj["json"]:
                click.echo(json.dumps(auth_result, indent=2))
            else:
                formatter.success("Authentication test successful!")
                formatter.info(f"Model: {options.model}")
                formatter.info(f"Response preview: {auth_result['test_response']}")
        else:
            auth_result = {"authenticated": False, "error": response.error}

            if ctx.obj["json"]:
                click.echo(json.dumps(auth_result, indent=2))
            else:
                formatter.error(f"Authentication test failed: {response.error}")
            sys.exit(1)

    except Exception as e:
        if ctx.obj["json"]:
            click.echo(json.dumps({"authenticated": False, "error": str(e)}, indent=2))
        else:
            formatter.error(f"Authentication test failed: {str(e)}")
        sys.exit(1)


# Make commands async-aware
def make_async_command(coro):
    """Convert async command to sync command for Click."""

    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))

    return wrapper


# Wrap async commands
check.callback = make_async_command(check.callback)
auth.callback = make_async_command(auth.callback)

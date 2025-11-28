"""
Bug analysis commands.
"""

import asyncio
import json
import sys
from pathlib import Path

import click

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.cli.utils.file_utils import (
    detect_language_from_file,
    read_file_or_stdin,
    save_output,
)
from src.core.config import ConfigManager
from src.core.gemini_client import GeminiCLIClient, GeminiOptions


async def perform_bug_analysis(
    bug_description: str,
    code_context: str,
    error_logs: str,
    environment: str,
    reproduction_steps: str,
    language: str,
    model: str,
    sandbox: bool,
    debug: bool,
) -> str:
    """
    Perform bug analysis using Gemini.

    Args:
        bug_description: Description of the bug
        code_context: Relevant code snippets
        error_logs: Error messages and logs
        environment: Environment details
        reproduction_steps: Steps to reproduce
        language: Programming language
        model: Gemini model to use
        sandbox: Use sandbox mode
        debug: Enable debug mode

    Returns:
        Analysis result
    """
    # Create Gemini client
    options = GeminiOptions(model=model, sandbox=sandbox, debug=debug)
    client = GeminiCLIClient(options)

    # Get configuration and templates
    config_manager = ConfigManager()
    template = config_manager.get_template("bug_analysis")

    if not template:
        raise ValueError("Bug analysis template not found")

    # Format template
    system_prompt, user_prompt = template.format(
        bug_description=bug_description,
        error_logs=error_logs,
        code_context=code_context,
        language=language or "unknown",
        environment=environment,
        reproduction_steps=reproduction_steps,
    )

    # Call Gemini
    response = await client.call_with_structured_prompt(
        system_prompt=system_prompt, user_prompt=user_prompt
    )

    if not response.success:
        raise ValueError(f"Gemini call failed: {response.error}")

    return response.content


@click.group()
def bug():
    """Bug analysis commands."""
    pass


@bug.command()
@click.option("--description", "-d", required=True, help="Description of the bug")
@click.option(
    "--code-file", type=click.Path(exists=True), help="File containing relevant code"
)
@click.option(
    "--code-context", help="Code context as text (alternative to --code-file)"
)
@click.option(
    "--logs-file", type=click.Path(exists=True), help="File containing error logs"
)
@click.option("--error-logs", help="Error logs as text (alternative to --logs-file)")
@click.option(
    "--environment", "-e", default="", help="Environment details (OS, versions, etc.)"
)
@click.option("--reproduction-steps", help="Steps to reproduce the bug")
@click.option(
    "--language",
    "-l",
    help="Programming language (auto-detected from code file if not specified)",
)
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
@click.pass_context
async def analyze(
    ctx,
    description,
    code_file,
    code_context,
    logs_file,
    error_logs,
    environment,
    reproduction_steps,
    language,
    output,
):
    """Analyze a bug with provided context."""
    formatter = ctx.obj["formatter"]

    try:
        # Get code context
        if code_file and code_context:
            raise click.ClickException(
                "Specify either --code-file or --code-context, not both"
            )

        if code_file:
            code_context = read_file_or_stdin(code_file)
            if not language:
                language = detect_language_from_file(code_file)
        elif not code_context:
            code_context = ""

        # Get error logs
        if logs_file and error_logs:
            raise click.ClickException(
                "Specify either --logs-file or --error-logs, not both"
            )

        if logs_file:
            error_logs = read_file_or_stdin(logs_file)
        elif not error_logs:
            error_logs = ""

        if ctx.obj["verbose"]:
            formatter.info(f"Analyzing bug: {description[:50]}...")
            formatter.info(f"Language: {language or 'unknown'}")
            formatter.info(f"Environment: {environment or 'not specified'}")

        # Show context preview if not in JSON mode
        if not ctx.obj["json"] and ctx.obj["verbose"]:
            if code_context:
                preview = (
                    code_context[:300] + "..."
                    if len(code_context) > 300
                    else code_context
                )
                formatter.console.print(f"\n🐛 Code Context Preview:\n{preview}\n")
            if error_logs:
                preview = (
                    error_logs[:200] + "..." if len(error_logs) > 200 else error_logs
                )
                formatter.console.print(f"📝 Error Logs Preview:\n{preview}\n")
            formatter.print_separator()

        # Perform analysis
        result = await perform_bug_analysis(
            bug_description=description,
            code_context=code_context,
            error_logs=error_logs,
            environment=environment,
            reproduction_steps=reproduction_steps or "",
            language=language or "",
            model=ctx.obj["model"],
            sandbox=ctx.obj["sandbox"],
            debug=ctx.obj["debug"],
        )

        # Output results
        formatter.print_bug_analysis(result)

        # Save to file if requested
        if output:
            if ctx.obj["json"]:
                output_data = {
                    "analysis": result,
                    "bug_description": description,
                    "language": language,
                    "environment": environment,
                    "model": ctx.obj["model"],
                }
                save_output(json.dumps(output_data, indent=2), output)
            else:
                # Create a formatted text output
                text_output = f"Bug Analysis Report\n{'=' * 50}\n\n"
                text_output += f"Bug Description: {description}\n"
                text_output += f"Language: {language or 'Unknown'}\n"
                text_output += f"Environment: {environment}\n"
                text_output += f"Model: {ctx.obj['model']}\n\n"
                text_output += f"Analysis:\n{result}\n"
                save_output(text_output, output)

    except Exception as e:
        formatter.error(f"Bug analysis failed: {str(e)}")
        sys.exit(1)


@bug.command()
@click.pass_context
async def interactive(ctx):
    """Interactive bug analysis wizard."""
    formatter = ctx.obj["formatter"]

    if ctx.obj["json"]:
        formatter.error("Interactive mode not available in JSON output mode")
        sys.exit(1)

    try:
        formatter.console.print("🐛 Interactive Bug Analysis Wizard", style="bold red")
        formatter.console.print("This wizard will guide you through analyzing a bug.\n")

        # Get bug description
        description = formatter.prompt_input("Bug description")
        if not description.strip():
            formatter.error("Bug description is required")
            sys.exit(1)

        # Get code context
        has_code = formatter.prompt_confirmation(
            "Do you have relevant code to include?"
        )
        code_context = ""
        language = ""

        if has_code:
            code_source = click.prompt(
                "Enter code (type 'file' to read from file, or paste code)", type=str
            )

            if code_source.lower() == "file":
                code_file = formatter.prompt_input("Code file path")
                try:
                    code_context = read_file_or_stdin(code_file)
                    language = detect_language_from_file(code_file) or ""
                except Exception as e:
                    formatter.warning(f"Could not read file: {e}")
            else:
                formatter.console.print("Enter your code (press Ctrl+D when done):")
                try:
                    while True:
                        line = input()
                        code_context += line + "\n"
                except EOFError:
                    pass

                language = formatter.prompt_input("Programming language", default="")

        # Get error logs
        has_logs = formatter.prompt_confirmation("Do you have error logs to include?")
        error_logs = ""

        if has_logs:
            logs_source = click.prompt(
                "Enter logs (type 'file' to read from file, or paste logs)", type=str
            )

            if logs_source.lower() == "file":
                logs_file = formatter.prompt_input("Logs file path")
                try:
                    error_logs = read_file_or_stdin(logs_file)
                except Exception as e:
                    formatter.warning(f"Could not read file: {e}")
            else:
                formatter.console.print(
                    "Enter your error logs (press Ctrl+D when done):"
                )
                try:
                    while True:
                        line = input()
                        error_logs += line + "\n"
                except EOFError:
                    pass

        # Get additional context
        environment = formatter.prompt_input(
            "Environment details (OS, versions, etc.)", default=""
        )

        reproduction_steps = formatter.prompt_input(
            "Steps to reproduce the bug", default=""
        )

        # Show summary
        formatter.console.print("\n📋 Analysis Summary:")
        formatter.console.print(f"  Bug: {description}")
        formatter.console.print(f"  Language: {language or 'Unknown'}")
        formatter.console.print(f"  Has Code: {'Yes' if code_context else 'No'}")
        formatter.console.print(f"  Has Logs: {'Yes' if error_logs else 'No'}")
        formatter.console.print(f"  Environment: {environment or 'Not specified'}")

        if not formatter.prompt_confirmation("\nProceed with analysis?"):
            formatter.info("Analysis cancelled")
            sys.exit(0)

        formatter.console.print(f"\n🔍 Analyzing bug with {ctx.obj['model']}...")

        # Perform analysis
        result = await perform_bug_analysis(
            bug_description=description,
            code_context=code_context,
            error_logs=error_logs,
            environment=environment,
            reproduction_steps=reproduction_steps,
            language=language,
            model=ctx.obj["model"],
            sandbox=ctx.obj["sandbox"],
            debug=ctx.obj["debug"],
        )

        # Output results
        formatter.print_bug_analysis(result)

    except KeyboardInterrupt:
        formatter.info("\nAnalysis cancelled by user")
        sys.exit(0)
    except Exception as e:
        formatter.error(f"Interactive bug analysis failed: {str(e)}")
        sys.exit(1)


# Make commands async-aware
def make_async_command(coro):
    """Convert async command to sync command for Click."""

    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))

    return wrapper


# Wrap async commands
analyze.callback = make_async_command(analyze.callback)
interactive.callback = make_async_command(interactive.callback)

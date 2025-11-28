"""
Code explanation commands.
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


async def perform_code_explanation(
    code: str,
    language: str,
    detail_level: str,
    questions: str,
    model: str,
    sandbox: bool,
    debug: bool,
) -> str:
    """
    Perform code explanation using Gemini.

    Args:
        code: Code to explain
        language: Programming language
        detail_level: Level of detail
        questions: Specific questions
        model: Gemini model to use
        sandbox: Use sandbox mode
        debug: Enable debug mode

    Returns:
        Explanation result
    """
    # Create Gemini client
    options = GeminiOptions(model=model, sandbox=sandbox, debug=debug)
    client = GeminiCLIClient(options)

    # Get configuration and templates
    config_manager = ConfigManager()
    template = config_manager.get_template("code_explanation")

    if not template:
        raise ValueError("Code explanation template not found")

    # Format template
    system_prompt, user_prompt = template.format(
        language=language or "auto-detect",
        code=code,
        detail_level=detail_level,
        questions=questions,
    )

    # Call Gemini
    response = await client.call_with_structured_prompt(
        system_prompt=system_prompt, user_prompt=user_prompt
    )

    if not response.success:
        raise ValueError(f"Gemini call failed: {response.error}")

    return response.content


@click.group()
def explain():
    """Code explanation commands."""
    pass


@explain.command()
@click.option("--file", "-f", type=click.Path(exists=True), help="Code file to explain")
@click.option(
    "--language", "-l", help="Programming language (auto-detected if not specified)"
)
@click.option(
    "--level",
    type=click.Choice(["basic", "intermediate", "advanced"]),
    default="intermediate",
    help="Detail level for explanation",
)
@click.option("--questions", "-q", default="", help="Specific questions about the code")
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
@click.pass_context
async def file(ctx, file, language, level, questions, output):
    """Explain code from a file."""
    formatter = ctx.obj["formatter"]

    try:
        # Read code from file
        if not file:
            raise click.ClickException("File path is required")

        code = read_file_or_stdin(file)

        # Auto-detect language if not provided
        if not language:
            language = detect_language_from_file(file)

        if ctx.obj["verbose"]:
            formatter.info(f"Explaining code from: {file}")
            formatter.info(f"Language: {language or 'auto-detect'}")
            formatter.info(f"Detail level: {level}")
            if questions:
                formatter.info(f"Questions: {questions}")

        # Show code preview if not in JSON mode
        if not ctx.obj["json"] and ctx.obj["verbose"]:
            formatter.print_code_with_syntax(
                code[:500] + "..." if len(code) > 500 else code, language
            )
            formatter.print_separator()

        # Perform explanation
        result = await perform_code_explanation(
            code=code,
            language=language or "",
            detail_level=level,
            questions=questions,
            model=ctx.obj["model"],
            sandbox=ctx.obj["sandbox"],
            debug=ctx.obj["debug"],
        )

        # Output results
        formatter.print_code_explanation(result)

        # Save to file if requested
        if output:
            if ctx.obj["json"]:
                output_data = {
                    "explanation": result,
                    "source": file,
                    "language": language,
                    "detail_level": level,
                    "questions": questions,
                    "model": ctx.obj["model"],
                }
                save_output(json.dumps(output_data, indent=2), output)
            else:
                # Create a formatted text output
                text_output = f"Code Explanation\n{'=' * 50}\n\n"
                text_output += f"File: {file}\n"
                text_output += f"Language: {language}\n"
                text_output += f"Detail Level: {level}\n"
                text_output += f"Questions: {questions}\n"
                text_output += f"Model: {ctx.obj['model']}\n\n"
                text_output += f"Explanation:\n{result}\n"
                save_output(text_output, output)

    except Exception as e:
        formatter.error(f"Code explanation failed: {str(e)}")
        sys.exit(1)


@explain.command()
@click.option("--language", "-l", help="Programming language")
@click.option(
    "--level",
    type=click.Choice(["basic", "intermediate", "advanced"]),
    default="intermediate",
    help="Detail level for explanation",
)
@click.option("--questions", "-q", default="", help="Specific questions about the code")
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
@click.pass_context
async def stdin(ctx, language, level, questions, output):
    """Explain code from stdin."""
    formatter = ctx.obj["formatter"]

    try:
        # Read code from stdin
        code = read_file_or_stdin(None)

        if not code.strip():
            raise click.ClickException("No code provided via stdin")

        if ctx.obj["verbose"]:
            formatter.info("Explaining code from stdin")
            formatter.info(f"Language: {language or 'auto-detect'}")
            formatter.info(f"Detail level: {level}")
            if questions:
                formatter.info(f"Questions: {questions}")

        # Perform explanation
        result = await perform_code_explanation(
            code=code,
            language=language or "",
            detail_level=level,
            questions=questions,
            model=ctx.obj["model"],
            sandbox=ctx.obj["sandbox"],
            debug=ctx.obj["debug"],
        )

        # Output results
        formatter.print_code_explanation(result)

        # Save to file if requested
        if output:
            if ctx.obj["json"]:
                output_data = {
                    "explanation": result,
                    "source": "stdin",
                    "language": language,
                    "detail_level": level,
                    "questions": questions,
                    "model": ctx.obj["model"],
                }
                save_output(json.dumps(output_data, indent=2), output)
            else:
                # Create a formatted text output
                text_output = f"Code Explanation\n{'=' * 50}\n\n"
                text_output += "Source: stdin\n"
                text_output += f"Language: {language}\n"
                text_output += f"Detail Level: {level}\n"
                text_output += f"Questions: {questions}\n"
                text_output += f"Model: {ctx.obj['model']}\n\n"
                text_output += f"Explanation:\n{result}\n"
                save_output(text_output, output)

    except Exception as e:
        formatter.error(f"Code explanation failed: {str(e)}")
        sys.exit(1)


@explain.command()
@click.option("--language", "-l", help="Programming language")
@click.option(
    "--level",
    type=click.Choice(["basic", "intermediate", "advanced"]),
    default="intermediate",
    help="Detail level for explanation",
)
@click.pass_context
async def interactive(ctx, language, level):
    """Interactive code explanation."""
    formatter = ctx.obj["formatter"]

    if ctx.obj["json"]:
        formatter.error("Interactive mode not available in JSON output mode")
        sys.exit(1)

    try:
        formatter.console.print("📖 Interactive Code Explanation", style="bold cyan")
        formatter.console.print("Enter your code (press Ctrl+D when done):\n")

        # Read code from user input
        code = ""
        try:
            while True:
                line = input()
                code += line + "\n"
        except EOFError:
            pass

        if not code.strip():
            formatter.error("No code provided")
            sys.exit(1)

        # Get language if not provided
        if not language:
            language = formatter.prompt_input(
                "Programming language (optional)", default=""
            )

        # Confirm detail level
        confirmed_level = click.prompt(
            "Detail level",
            type=click.Choice(["basic", "intermediate", "advanced"]),
            default=level,
            show_default=True,
        )

        # Get specific questions
        questions = formatter.prompt_input(
            "Specific questions about the code (optional)", default=""
        )

        formatter.console.print("\n🔍 Explaining code...")
        formatter.console.print(f"Language: {language or 'auto-detect'}")
        formatter.console.print(f"Detail Level: {confirmed_level}")
        if questions:
            formatter.console.print(f"Questions: {questions}")
        formatter.console.print()

        # Perform explanation
        result = await perform_code_explanation(
            code=code,
            language=language,
            detail_level=confirmed_level,
            questions=questions,
            model=ctx.obj["model"],
            sandbox=ctx.obj["sandbox"],
            debug=ctx.obj["debug"],
        )

        # Output results
        formatter.print_code_explanation(result)

    except KeyboardInterrupt:
        formatter.info("\nExplanation cancelled by user")
        sys.exit(0)
    except Exception as e:
        formatter.error(f"Interactive code explanation failed: {str(e)}")
        sys.exit(1)


# Make commands async-aware
def make_async_command(coro):
    """Convert async command to sync command for Click."""

    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))

    return wrapper


# Wrap async commands
file.callback = make_async_command(file.callback)
stdin.callback = make_async_command(stdin.callback)
interactive.callback = make_async_command(interactive.callback)

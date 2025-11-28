"""
Code review commands.
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


async def perform_code_review(
    code: str, language: str | None, focus: str, model: str, sandbox: bool, debug: bool
) -> dict:
    """
    Perform code review using Gemini.

    Args:
        code: Code content to review
        language: Programming language
        focus: Review focus area
        model: Gemini model to use
        sandbox: Use sandbox mode
        debug: Enable debug mode

    Returns:
        Review result dictionary
    """
    # Create Gemini client
    options = GeminiOptions(model=model, sandbox=sandbox, debug=debug)
    client = GeminiCLIClient(options)

    # Get configuration and templates
    config_manager = ConfigManager()
    template = config_manager.get_template("code_review")

    if not template:
        raise ValueError("Code review template not found")

    # Determine language if not provided
    if not language:
        language = "auto-detect"

    # Create focus instruction
    focus_map = {
        "security": "Focus specifically on security vulnerabilities and potential exploits.",
        "performance": "Focus on performance optimizations and bottlenecks.",
        "style": "Focus on code style, formatting, and best practices.",
        "bugs": "Focus on potential bugs and logical errors.",
        "general": "Provide a comprehensive review covering all aspects.",
    }
    focus_instruction = focus_map.get(focus, focus_map["general"])

    # Format template
    system_prompt, user_prompt = template.format(
        language=language, code=code, focus_instruction=focus_instruction
    )

    # Call Gemini
    response = await client.call_with_structured_prompt(
        system_prompt=system_prompt, user_prompt=user_prompt
    )

    if not response.success:
        raise ValueError(f"Gemini call failed: {response.error}")

    # Parse structured response
    try:
        # Try to extract JSON from response
        content = response.content
        if "```json" in content:
            # Extract JSON block
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                json_content = content[start:end].strip()
                parsed = json.loads(json_content)
            else:
                # Fallback to simple parsing
                parsed = {"summary": content, "issues": [], "suggestions": []}
        else:
            # Create structured response from text
            parsed = {
                "summary": content[:500] + "..." if len(content) > 500 else content,
                "issues": [],
                "suggestions": content.split("\n") if content else [],
            }

        return {
            "summary": parsed.get("summary", "Code review completed"),
            "issues": parsed.get("issues", []),
            "suggestions": parsed.get("suggestions", []),
            "rating": parsed.get("rating", "Review completed"),
            "focus": focus,
            "language": language,
            "model": model,
            "input_prompt": response.input_prompt,
            "gemini_response": response.content,
        }

    except json.JSONDecodeError:
        # Fallback to simple text response
        return {
            "summary": response.content[:200] + "..."
            if len(response.content) > 200
            else response.content,
            "issues": [],
            "suggestions": [response.content],
            "rating": "Review completed (text format)",
            "focus": focus,
            "language": language,
            "model": model,
            "input_prompt": response.input_prompt,
            "gemini_response": response.content,
        }


@click.group()
def review():
    """Code review commands."""
    pass


@review.command()
@click.option("--file", "-f", type=click.Path(exists=True), help="File to review")
@click.option(
    "--language", "-l", help="Programming language (auto-detected if not specified)"
)
@click.option(
    "--focus",
    type=click.Choice(["general", "security", "performance", "style", "bugs"]),
    default="general",
    help="Review focus area",
)
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
@click.pass_context
async def file(ctx, file, language, focus, output):
    """Review code from a file."""
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
            formatter.info(f"Reviewing file: {file}")
            formatter.info(f"Language: {language or 'auto-detect'}")
            formatter.info(f"Focus: {focus}")

        # Show code preview if not in JSON mode
        if not ctx.obj["json"] and ctx.obj["verbose"]:
            formatter.print_code_with_syntax(
                code[:500] + "..." if len(code) > 500 else code, language
            )
            formatter.print_separator()

        # Perform review
        result = await perform_code_review(
            code=code,
            language=language,
            focus=focus,
            model=ctx.obj["model"],
            sandbox=ctx.obj["sandbox"],
            debug=ctx.obj["debug"],
        )

        # Output results
        formatter.print_code_review(result, show_prompts=ctx.obj["show_prompts"])

        # Save to file if requested
        if output:
            if ctx.obj["json"]:
                save_output(json.dumps(result, indent=2), output)
            else:
                # Create a formatted text output
                text_output = f"Code Review Results\n{'=' * 50}\n\n"
                text_output += f"File: {file}\n"
                text_output += f"Language: {language}\n"
                text_output += f"Focus: {focus}\n"
                text_output += f"Model: {ctx.obj['model']}\n\n"
                text_output += f"Summary:\n{result['summary']}\n\n"
                if result["suggestions"]:
                    text_output += "Suggestions:\n"
                    for i, suggestion in enumerate(result["suggestions"], 1):
                        text_output += f"{i}. {suggestion}\n"
                text_output += f"\nRating: {result['rating']}\n"
                save_output(text_output, output)

    except Exception as e:
        if ctx.obj["json"]:
            click.echo(json.dumps({"error": str(e), "success": False}, indent=2))
        else:
            formatter.error(f"Code review failed: {str(e)}")
        sys.exit(1)


@review.command()
@click.option("--language", "-l", help="Programming language")
@click.option(
    "--focus",
    type=click.Choice(["general", "security", "performance", "style", "bugs"]),
    default="general",
    help="Review focus area",
)
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
@click.pass_context
async def stdin(ctx, language, focus, output):
    """Review code from stdin."""
    formatter = ctx.obj["formatter"]

    try:
        # Read code from stdin
        code = read_file_or_stdin(None)

        if not code.strip():
            raise click.ClickException("No code provided via stdin")

        if ctx.obj["verbose"]:
            formatter.info("Reviewing code from stdin")
            formatter.info(f"Language: {language or 'auto-detect'}")
            formatter.info(f"Focus: {focus}")

        # Perform review
        result = await perform_code_review(
            code=code,
            language=language,
            focus=focus,
            model=ctx.obj["model"],
            sandbox=ctx.obj["sandbox"],
            debug=ctx.obj["debug"],
        )

        # Output results
        formatter.print_code_review(result, show_prompts=ctx.obj["show_prompts"])

        # Save to file if requested
        if output:
            if ctx.obj["json"]:
                save_output(json.dumps(result, indent=2), output)
            else:
                # Create a formatted text output
                text_output = f"Code Review Results\n{'=' * 50}\n\n"
                text_output += "Source: stdin\n"
                text_output += f"Language: {language}\n"
                text_output += f"Focus: {focus}\n"
                text_output += f"Model: {ctx.obj['model']}\n\n"
                text_output += f"Summary:\n{result['summary']}\n\n"
                if result["suggestions"]:
                    text_output += "Suggestions:\n"
                    for i, suggestion in enumerate(result["suggestions"], 1):
                        text_output += f"{i}. {suggestion}\n"
                text_output += f"\nRating: {result['rating']}\n"
                save_output(text_output, output)

    except Exception as e:
        if ctx.obj["json"]:
            click.echo(json.dumps({"error": str(e), "success": False}, indent=2))
        else:
            formatter.error(f"Code review failed: {str(e)}")
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

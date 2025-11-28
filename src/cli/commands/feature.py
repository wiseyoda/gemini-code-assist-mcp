"""
Feature plan review commands.
"""

import asyncio
import json
import sys
from pathlib import Path

import click

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.cli.utils.file_utils import read_file_or_stdin, save_output
from src.core.config import ConfigManager
from src.core.gemini_client import GeminiCLIClient, GeminiOptions


async def perform_feature_review(
    feature_plan: str,
    context: str,
    focus_areas: str,
    model: str,
    sandbox: bool,
    debug: bool,
) -> str:
    """
    Perform feature plan review using Gemini.

    Args:
        feature_plan: Feature plan content
        context: Project context
        focus_areas: Areas to focus on
        model: Gemini model to use
        sandbox: Use sandbox mode
        debug: Enable debug mode

    Returns:
        Review result
    """
    # Create Gemini client
    options = GeminiOptions(model=model, sandbox=sandbox, debug=debug)
    client = GeminiCLIClient(options)

    # Get configuration and templates
    config_manager = ConfigManager()
    template = config_manager.get_template("feature_plan_review")

    if not template:
        raise ValueError("Feature plan review template not found")

    # Format template
    system_prompt, user_prompt = template.format(
        feature_plan=feature_plan, context=context, focus_areas=focus_areas
    )

    # Call Gemini
    response = await client.call_with_structured_prompt(
        system_prompt=system_prompt, user_prompt=user_prompt
    )

    if not response.success:
        raise ValueError(f"Gemini call failed: {response.error}")

    return response.content


@click.group()
def feature():
    """Feature planning commands."""
    pass


@feature.command()
@click.option(
    "--file", "-f", type=click.Path(exists=True), help="Feature plan file to review"
)
@click.option("--context", "-c", default="", help="Project context and constraints")
@click.option(
    "--focus-areas",
    default="completeness,feasibility,clarity",
    help="Areas to focus on (comma-separated)",
)
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
@click.pass_context
async def review(ctx, file, context, focus_areas, output):
    """Review a feature plan from file or stdin."""
    formatter = ctx.obj["formatter"]

    try:
        # Read feature plan
        if file:
            feature_plan = read_file_or_stdin(file)
            source = file
        else:
            feature_plan = read_file_or_stdin(None)
            source = "stdin"

        if not feature_plan.strip():
            raise click.ClickException("No feature plan content provided")

        if ctx.obj["verbose"]:
            formatter.info(f"Reviewing feature plan from: {source}")
            formatter.info(f"Context: {context or 'None provided'}")
            formatter.info(f"Focus areas: {focus_areas}")

        # Show plan preview if not in JSON mode
        if not ctx.obj["json"] and ctx.obj["verbose"]:
            preview = (
                feature_plan[:300] + "..." if len(feature_plan) > 300 else feature_plan
            )
            formatter.console.print(f"\n📋 Feature Plan Preview:\n{preview}\n")
            formatter.print_separator()

        # Perform review
        result = await perform_feature_review(
            feature_plan=feature_plan,
            context=context,
            focus_areas=focus_areas,
            model=ctx.obj["model"],
            sandbox=ctx.obj["sandbox"],
            debug=ctx.obj["debug"],
        )

        # Output results
        formatter.print_feature_plan_review(result)

        # Save to file if requested
        if output:
            if ctx.obj["json"]:
                output_data = {
                    "review": result,
                    "source": source,
                    "context": context,
                    "focus_areas": focus_areas,
                    "model": ctx.obj["model"],
                }
                save_output(json.dumps(output_data, indent=2), output)
            else:
                # Create a formatted text output
                text_output = f"Feature Plan Review\n{'=' * 50}\n\n"
                text_output += f"Source: {source}\n"
                text_output += f"Context: {context}\n"
                text_output += f"Focus Areas: {focus_areas}\n"
                text_output += f"Model: {ctx.obj['model']}\n\n"
                text_output += f"Review:\n{result}\n"
                save_output(text_output, output)

    except Exception as e:
        formatter.error(f"Feature plan review failed: {str(e)}")
        sys.exit(1)


@feature.command()
@click.option("--context", "-c", help="Project context and constraints")
@click.option(
    "--focus-areas",
    default="completeness,feasibility,clarity",
    help="Areas to focus on (comma-separated)",
)
@click.pass_context
async def interactive(ctx, context, focus_areas):
    """Interactive feature plan review."""
    formatter = ctx.obj["formatter"]

    if ctx.obj["json"]:
        formatter.error("Interactive mode not available in JSON output mode")
        sys.exit(1)

    try:
        formatter.console.print("🚀 Interactive Feature Plan Review", style="bold blue")
        formatter.console.print("Enter your feature plan (press Ctrl+D when done):\n")

        # Read feature plan from user input
        feature_plan = ""
        try:
            while True:
                line = input()
                feature_plan += line + "\n"
        except EOFError:
            pass

        if not feature_plan.strip():
            formatter.error("No feature plan provided")
            sys.exit(1)

        # Get context if not provided
        if not context:
            context = formatter.prompt_input("Project context (optional)", default="")

        # Confirm focus areas
        confirmed_focus = formatter.prompt_input("Focus areas", default=focus_areas)

        formatter.console.print("\n🔍 Reviewing feature plan...")
        formatter.console.print(f"Context: {context or 'None'}")
        formatter.console.print(f"Focus: {confirmed_focus}\n")

        # Perform review
        result = await perform_feature_review(
            feature_plan=feature_plan,
            context=context,
            focus_areas=confirmed_focus,
            model=ctx.obj["model"],
            sandbox=ctx.obj["sandbox"],
            debug=ctx.obj["debug"],
        )

        # Output results
        formatter.print_feature_plan_review(result)

    except KeyboardInterrupt:
        formatter.info("\nReview cancelled by user")
        sys.exit(0)
    except Exception as e:
        formatter.error(f"Interactive feature plan review failed: {str(e)}")
        sys.exit(1)


# Make commands async-aware
def make_async_command(coro):
    """Convert async command to sync command for Click."""

    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))

    return wrapper


# Wrap async commands
review.callback = make_async_command(review.callback)
interactive.callback = make_async_command(interactive.callback)

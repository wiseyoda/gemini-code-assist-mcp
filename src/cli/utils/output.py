"""
Output formatting utilities for the CLI.
"""

import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table


class OutputFormatter:
    """Handles formatted output for CLI commands."""

    def __init__(self, use_color: bool = True, json_output: bool = False):
        """
        Initialize output formatter.

        Args:
            use_color: Whether to use colored output
            json_output: Whether to output JSON format
        """
        self.use_color = use_color
        self.json_output = json_output
        self.console = Console(color_system="auto" if use_color else None)

    def success(self, message: str) -> None:
        """Print a success message."""
        if self.json_output:
            return
        self.console.print(f"✅ {message}", style="green")

    def error(self, message: str) -> None:
        """Print an error message."""
        if self.json_output:
            return
        self.console.print(f"❌ {message}", style="red", file=sys.stderr)

    def warning(self, message: str) -> None:
        """Print a warning message."""
        if self.json_output:
            return
        self.console.print(f"⚠️  {message}", style="yellow")

    def info(self, message: str) -> None:
        """Print an info message."""
        if self.json_output:
            return
        self.console.print(f"ℹ️  {message}", style="blue")

    def print_code_review(
        self, result: dict[str, Any], show_prompts: bool = False
    ) -> None:
        """
        Print code review results in a formatted way.

        Args:
            result: Code review result dictionary
            show_prompts: Whether to show input prompts and raw responses
        """
        if self.json_output:
            click.echo(json.dumps(result, indent=2))
            return

        # Print summary
        summary = result.get("summary", "No summary available")
        self.console.print(
            Panel(summary, title="📋 Review Summary", border_style="blue")
        )

        # Print issues if any
        issues = result.get("issues", [])
        if issues:
            table = Table(title="🔍 Issues Found")
            table.add_column("Type", style="red")
            table.add_column("Severity", style="yellow")
            table.add_column("Description", style="white")
            table.add_column("Line", style="cyan")

            for issue in issues:
                table.add_row(
                    issue.get("type", "Unknown"),
                    issue.get("severity", "Unknown"),
                    issue.get("description", "No description"),
                    str(issue.get("line_numbers", ["N/A"])[0])
                    if issue.get("line_numbers")
                    else "N/A",
                )
            self.console.print(table)

        # Print suggestions
        suggestions = result.get("suggestions", [])
        if suggestions:
            self.console.print("\n💡 Suggestions:", style="green bold")
            for i, suggestion in enumerate(suggestions, 1):
                self.console.print(f"  {i}. {suggestion}")

        # Print rating
        rating = result.get("rating", "No rating")
        self.console.print(f"\n⭐ Overall Rating: {rating}", style="bold")

        # Show prompts if requested
        if show_prompts:
            self.console.print("\n" + "─" * 80)

            # Show input prompt
            input_prompt = result.get("input_prompt", "No input prompt available")
            self.console.print(
                Panel(
                    input_prompt,
                    title="📤 Prompt Sent to Gemini",
                    border_style="yellow",
                )
            )

            # Show raw response
            gemini_response = result.get("gemini_response", "No response available")
            self.console.print(
                Panel(
                    gemini_response,
                    title="📥 Raw Response from Gemini",
                    border_style="green",
                )
            )

    def print_feature_plan_review(
        self,
        content: str,
        show_prompts: bool = False,
        input_prompt: str = None,
        gemini_response: str = None,
    ) -> None:
        """
        Print feature plan review results.

        Args:
            content: Review content
            show_prompts: Whether to show input prompts and raw responses
            input_prompt: The input prompt sent to Gemini
            gemini_response: The raw response from Gemini
        """
        if self.json_output:
            click.echo(json.dumps({"review": content}, indent=2))
            return

        self.console.print(
            Panel(content, title="📋 Feature Plan Review", border_style="green")
        )

        # Show prompts if requested
        if show_prompts and input_prompt and gemini_response:
            self.console.print("\n" + "─" * 80)

            # Show input prompt
            self.console.print(
                Panel(
                    input_prompt,
                    title="📤 Prompt Sent to Gemini",
                    border_style="yellow",
                )
            )

            # Show raw response
            self.console.print(
                Panel(
                    gemini_response,
                    title="📥 Raw Response from Gemini",
                    border_style="green",
                )
            )

    def print_bug_analysis(self, content: str) -> None:
        """
        Print bug analysis results.

        Args:
            content: Analysis content
        """
        if self.json_output:
            click.echo(json.dumps({"analysis": content}, indent=2))
            return

        self.console.print(Panel(content, title="🐛 Bug Analysis", border_style="red"))

    def print_code_explanation(self, content: str) -> None:
        """
        Print code explanation results.

        Args:
            content: Explanation content
        """
        if self.json_output:
            click.echo(json.dumps({"explanation": content}, indent=2))
            return

        self.console.print(
            Panel(content, title="📖 Code Explanation", border_style="cyan")
        )

    def print_status(self, status: dict[str, Any]) -> None:
        """
        Print status information.

        Args:
            status: Status dictionary
        """
        if self.json_output:
            click.echo(json.dumps(status, indent=2))
            return

        # Authentication status
        auth_status = (
            "✅ Authenticated"
            if status.get("authenticated")
            else "❌ Not Authenticated"
        )
        cli_status = (
            "✅ Available" if status.get("cli_available") else "❌ Not Available"
        )

        table = Table(title="🔧 Gemini CLI Status")
        table.add_column("Component", style="bold")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")

        table.add_row("Authentication", auth_status, "")
        table.add_row("CLI Availability", cli_status, "")
        table.add_row("Model", status.get("model", "Unknown"), "")

        if status.get("error"):
            table.add_row("Error", "❌", status["error"])

        self.console.print(table)

    def print_config(self, config: dict[str, Any]) -> None:
        """
        Print configuration information.

        Args:
            config: Configuration dictionary
        """
        if self.json_output:
            click.echo(json.dumps(config, indent=2))
            return

        self.console.print(
            Panel(
                json.dumps(config, indent=2),
                title="⚙️  Configuration",
                border_style="blue",
            )
        )

    def print_templates(self, templates: dict[str, str]) -> None:
        """
        Print available templates.

        Args:
            templates: Dictionary of template names to descriptions
        """
        if self.json_output:
            click.echo(json.dumps(templates, indent=2))
            return

        table = Table(title="📝 Available Templates")
        table.add_column("Template Name", style="bold cyan")
        table.add_column("Description", style="white")

        for name, description in templates.items():
            table.add_row(name, description)

        self.console.print(table)

    def print_code_with_syntax(self, code: str, language: str | None = None) -> None:
        """
        Print code with syntax highlighting.

        Args:
            code: Code to display
            language: Programming language for syntax highlighting
        """
        if self.json_output:
            return

        if language:
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            self.console.print(
                Panel(syntax, title=f"📄 Code ({language})", border_style="yellow")
            )
        else:
            self.console.print(Panel(code, title="📄 Code", border_style="yellow"))

    def print_separator(self) -> None:
        """Print a visual separator."""
        if not self.json_output:
            self.console.print("─" * 60, style="dim")

    def prompt_confirmation(self, message: str) -> bool:
        """
        Prompt user for confirmation.

        Args:
            message: Confirmation message

        Returns:
            True if confirmed, False otherwise
        """
        if self.json_output:
            return True  # Auto-confirm in JSON mode

        return click.confirm(message)

    def prompt_input(self, prompt: str, default: str | None = None) -> str:
        """
        Prompt user for input.

        Args:
            prompt: Input prompt message
            default: Default value

        Returns:
            User input
        """
        if self.json_output:
            return default or ""

        return click.prompt(prompt, default=default, show_default=True)

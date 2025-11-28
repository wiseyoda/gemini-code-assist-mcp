"""
File handling utilities for the CLI.
"""

import sys
from pathlib import Path
from typing import TextIO

import click


def read_file_or_stdin(file_path: str | None, stdin_input: TextIO | None = None) -> str:
    """
    Read content from a file or stdin.

    Args:
        file_path: Path to file to read (None for stdin)
        stdin_input: Input stream (defaults to sys.stdin)

    Returns:
        File content as string

    Raises:
        click.ClickException: If file cannot be read
    """
    if file_path:
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise click.ClickException(
                f"Error reading file '{file_path}': {str(e)}"
            ) from None
    else:
        # Read from stdin
        stdin = stdin_input or sys.stdin
        try:
            if stdin.isatty():
                click.echo("Reading from stdin (Ctrl+D to finish):", err=True)
            return stdin.read()
        except Exception as e:
            raise click.ClickException(f"Error reading from stdin: {str(e)}") from None


def detect_language_from_file(file_path: str) -> str | None:
    """
    Detect programming language from file extension.

    Args:
        file_path: Path to the file

    Returns:
        Detected language or None if unknown
    """
    if not file_path:
        return None

    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".fish": "fish",
        ".ps1": "powershell",
        ".r": "r",
        ".R": "r",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".xml": "xml",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".conf": "ini",
        ".md": "markdown",
        ".markdown": "markdown",
        ".tex": "latex",
        ".dockerfile": "dockerfile",
        ".Dockerfile": "dockerfile",
    }

    path = Path(file_path)
    extension = path.suffix.lower()

    # Special cases
    if path.name.lower() in ["dockerfile", "makefile", "rakefile"]:
        return path.name.lower()

    return extension_map.get(extension)


def save_output(content: str, output_path: str) -> None:
    """
    Save content to a file.

    Args:
        content: Content to save
        output_path: Path to save the file

    Raises:
        click.ClickException: If file cannot be saved
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        click.echo(f"Output saved to: {output_path}", err=True)
    except Exception as e:
        raise click.ClickException(
            f"Error saving to '{output_path}': {str(e)}"
        ) from None


def validate_file_exists(file_path: str) -> None:
    """
    Validate that a file exists and is readable.

    Args:
        file_path: Path to validate

    Raises:
        click.ClickException: If file doesn't exist or isn't readable
    """
    path = Path(file_path)
    if not path.exists():
        raise click.ClickException(f"File not found: {file_path}")
    if not path.is_file():
        raise click.ClickException(f"Not a file: {file_path}")
    if not path.stat().st_size:
        raise click.ClickException(f"File is empty: {file_path}")


def read_multiple_files(file_paths: list[str]) -> str:
    """
    Read and combine multiple files with headers.

    Args:
        file_paths: List of file paths to read

    Returns:
        Combined content with file headers

    Raises:
        click.ClickException: If any file cannot be read
    """
    combined_content = []

    for file_path in file_paths:
        validate_file_exists(file_path)
        content = read_file_or_stdin(file_path)

        combined_content.append(f"--- {file_path} ---")
        combined_content.append(content)
        combined_content.append("")  # Empty line separator

    return "\n".join(combined_content)

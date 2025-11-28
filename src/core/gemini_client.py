"""
Gemini CLI client wrapper.

This module provides a wrapper around the Gemini CLI, handling subprocess
calls and authentication through gcloud.
"""

import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class GeminiOptions(BaseModel):
    """Configuration options for Gemini CLI calls."""

    model: str = Field(
        default="gemini-3-pro-preview", description="Gemini model to use"
    )
    fallback_models: list[str] = Field(
        default_factory=lambda: ["gemini-2.5-pro"],
        description="Models to try if primary fails",
    )
    sandbox: bool = Field(default=False, description="Run in sandbox mode")
    debug: bool = Field(default=False, description="Enable debug mode")
    all_files: bool = Field(default=False, description="Include all files in context")
    show_memory_usage: bool = Field(default=False, description="Show memory usage")
    yolo: bool = Field(default=False, description="Auto-accept all actions")
    checkpointing: bool = Field(default=False, description="Enable checkpointing")


class GeminiResponse(BaseModel):
    """Response from Gemini CLI call."""

    content: str = Field(description="Response content from Gemini")
    success: bool = Field(description="Whether the call was successful")
    error: str | None = Field(default=None, description="Error message if failed")
    input_prompt: str = Field(description="The prompt that was sent to Gemini")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class GeminiCLIError(Exception):
    """Exception raised when Gemini CLI calls fail."""

    def __init__(self, message: str, error_code: int | None = None):
        super().__init__(message)
        self.error_code = error_code


class GeminiCLIClient:
    """
    Client for interacting with Google Gemini via CLI.

    Uses subprocess to call the Gemini CLI and leverages existing gcloud
    authentication. No API key configuration required.
    """

    def __init__(self, default_options: GeminiOptions | None = None):
        """
        Initialize the Gemini CLI client.

        Args:
            default_options: Default options to use for CLI calls
        """
        self.default_options = default_options or GeminiOptions()
        self._verified_auth = False

    async def verify_authentication(self) -> bool:
        """
        Verify that Gemini CLI is available and authenticated.

        Returns:
            True if authentication is valid, False otherwise

        Raises:
            GeminiCLIError: If CLI is not available or authentication fails
        """
        try:
            # Check if gemini CLI is available (cross-platform)
            gemini_path = shutil.which("gemini")
            if not gemini_path:
                raise GeminiCLIError(
                    "Gemini CLI not found. Please install and configure Gemini CLI."
                )

            # Test basic authentication with a simple prompt
            test_result = await self._call_gemini(
                prompt="Hello", options=GeminiOptions(model=self.default_options.model)
            )

            if not test_result.success:
                raise GeminiCLIError(f"Authentication test failed: {test_result.error}")

            self._verified_auth = True
            return True

        except subprocess.SubprocessError as e:
            raise GeminiCLIError(f"Error verifying Gemini CLI: {str(e)}") from e

    async def call_gemini(
        self,
        prompt: str,
        options: GeminiOptions | None = None,
        input_files: list[str | Path] | None = None,
    ) -> GeminiResponse:
        """
        Make a call to Gemini CLI with the given prompt, with fallback support.

        Args:
            prompt: The prompt to send to Gemini
            options: CLI options to use (defaults to instance default)
            input_files: Optional list of files to include in context

        Returns:
            GeminiResponse with the result

        Raises:
            GeminiCLIError: If the CLI call fails and no fallbacks succeed
        """
        if not self._verified_auth:
            await self.verify_authentication()

        # Use provided options or defaults
        opts = options or self.default_options

        # Create a copy to modify during fallback attempts
        current_opts = opts.model_copy()

        # List of models to try: primary + fallbacks
        models_to_try = [current_opts.model] + current_opts.fallback_models

        last_response = None

        for model in models_to_try:
            current_opts.model = model

            # Log retry if this isn't the first attempt
            if last_response:
                # We could log here if we had a logger, but for now just proceed
                pass

            response = await self._call_gemini(prompt, current_opts, input_files)

            if response.success:
                return response

            last_response = response

        # If we get here, all models failed
        # Return the last response (usually from the fallback model)
        return last_response or GeminiResponse(
            content="",
            success=False,
            error="No models defined to try",
            input_prompt=prompt,
        )

    async def _call_gemini(
        self,
        prompt: str,
        options: GeminiOptions | None = None,
        input_files: list[str | Path] | None = None,
    ) -> GeminiResponse:
        """
        Internal method to call Gemini CLI.

        Args:
            prompt: The prompt to send
            options: CLI options
            input_files: Files to include

        Returns:
            GeminiResponse with the result
        """
        # Use provided options or defaults
        opts = options or self.default_options

        # Build command arguments
        cmd = ["gemini"]

        # Add model selection
        cmd.extend(["-m", opts.model])

        # Add boolean flags
        if opts.sandbox:
            cmd.append("-s")
        if opts.debug:
            cmd.append("-d")
        if opts.all_files:
            cmd.append("-a")
        if opts.show_memory_usage:
            cmd.append("--show_memory_usage")
        if opts.yolo:
            cmd.append("-y")
        if opts.checkpointing:
            cmd.append("-c")

        # Add prompt using -p flag
        cmd.extend(["-p", prompt])

        temp_file_path = None
        try:
            # Handle input files if provided
            if input_files:
                # Create temporary file with file contents for context
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False
                ) as temp_file:
                    for file_path in input_files:
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                temp_file.write(f"--- {file_path} ---\n")
                                temp_file.write(f.read())
                                temp_file.write("\n\n")
                        except Exception as e:
                            # Skip files that can't be read
                            temp_file.write(
                                f"--- {file_path} (Error: {str(e)}) ---\n\n"
                            )

                    temp_file_path = temp_file.name

                # Add file to command via stdin
                with open(temp_file_path) as temp_file:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdin=temp_file,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
            else:
                # No input files, call directly
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

            # Wait for completion and get output
            stdout, stderr = await process.communicate()

            # Decode output
            stdout_text = stdout.decode("utf-8") if stdout else ""
            stderr_text = stderr.decode("utf-8") if stderr else ""

            if process.returncode == 0:
                return GeminiResponse(
                    content=stdout_text.strip(),
                    success=True,
                    input_prompt=prompt,
                    metadata={
                        "command": " ".join(cmd),
                        "model": opts.model,
                        "files_included": len(input_files) if input_files else 0,
                    },
                )
            else:
                error_msg = (
                    stderr_text or f"Command failed with exit code {process.returncode}"
                )
                return GeminiResponse(
                    content="",
                    success=False,
                    error=error_msg,
                    input_prompt=prompt,
                    metadata={
                        "command": " ".join(cmd),
                        "exit_code": process.returncode,
                    },
                )

        except Exception as e:
            return GeminiResponse(
                content="",
                success=False,
                error=f"Subprocess error: {str(e)}",
                input_prompt=prompt,
                metadata={"command": " ".join(cmd)},
            )
        finally:
            # Clean up temp file if it was created
            if temp_file_path:
                try:
                    Path(temp_file_path).unlink(missing_ok=True)
                except OSError:
                    pass  # Ignore cleanup errors

    async def call_with_structured_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str | None = None,
        options: GeminiOptions | None = None,
    ) -> GeminiResponse:
        """
        Call Gemini with a structured prompt format.

        Args:
            system_prompt: System-level instructions
            user_prompt: User request
            context: Optional context information
            options: CLI options

        Returns:
            GeminiResponse with the result
        """
        # Build structured prompt
        full_prompt = f"System: {system_prompt}\n\n"

        if context:
            full_prompt += f"Context:\n{context}\n\n"

        full_prompt += f"User: {user_prompt}"

        return await self.call_gemini(full_prompt, options)

    def update_default_options(self, **kwargs) -> None:
        """
        Update default options for this client.

        Args:
            **kwargs: Options to update
        """
        current_dict = self.default_options.model_dump()
        current_dict.update(kwargs)
        self.default_options = GeminiOptions(**current_dict)

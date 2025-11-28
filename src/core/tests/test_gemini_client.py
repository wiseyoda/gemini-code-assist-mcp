"""
Tests for the Gemini CLI client wrapper.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.core.gemini_client import (
    GeminiCLIClient,
    GeminiCLIError,
    GeminiOptions,
    GeminiResponse,
)


class TestGeminiOptions:
    """Test GeminiOptions model."""

    def test_default_values(self):
        """Test default option values."""
        options = GeminiOptions()
        assert options.model == "gemini-3-pro-preview"
        assert options.sandbox is False
        assert options.debug is False
        assert options.all_files is False

    def test_custom_values(self):
        """Test custom option values."""
        options = GeminiOptions(model="gemini-pro", sandbox=True, debug=True)
        assert options.model == "gemini-pro"
        assert options.sandbox is True
        assert options.debug is True


class TestGeminiResponse:
    """Test GeminiResponse model."""

    def test_success_response(self):
        """Test successful response."""
        response = GeminiResponse(
            content="Test response", success=True, input_prompt="Test prompt"
        )
        assert response.content == "Test response"
        assert response.success is True
        assert response.error is None
        assert response.input_prompt == "Test prompt"

    def test_error_response(self):
        """Test error response."""
        response = GeminiResponse(
            content="", success=False, error="Test error", input_prompt="Test prompt"
        )
        assert response.content == ""
        assert response.success is False
        assert response.error == "Test error"


class TestGeminiCLIClient:
    """Test GeminiCLIClient functionality."""

    def test_initialization(self):
        """Test client initialization."""
        client = GeminiCLIClient()
        assert client.default_options.model == "gemini-3-pro-preview"
        assert not client._verified_auth

    def test_initialization_with_options(self):
        """Test client initialization with custom options."""
        options = GeminiOptions(model="gemini-pro", sandbox=True)
        client = GeminiCLIClient(options)
        assert client.default_options.model == "gemini-pro"
        assert client.default_options.sandbox is True

    @pytest.mark.asyncio
    async def test_verify_authentication_cli_not_found(self):
        """Test authentication verification when CLI is not found."""
        client = GeminiCLIClient()

        with patch("shutil.which", return_value=None):
            # shutil.which returns None when CLI is not found
            with pytest.raises(GeminiCLIError, match="Gemini CLI not found"):
                await client.verify_authentication()

    @pytest.mark.asyncio
    async def test_verify_authentication_success(self):
        """Test successful authentication verification."""
        client = GeminiCLIClient()

        with patch.object(client, "_call_gemini") as mock_call:
            # Mock successful CLI check
            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.wait.return_value = None
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process

                # Mock successful Gemini call
                mock_call.return_value = GeminiResponse(
                    content="Hello response", success=True, input_prompt="Hello"
                )

                result = await client.verify_authentication()
                assert result is True
                assert client._verified_auth is True

    @pytest.mark.asyncio
    async def test_call_gemini_simple(self):
        """Test simple Gemini call."""
        client = GeminiCLIClient()
        client._verified_auth = True  # Skip auth verification

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock successful subprocess
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Test response", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            response = await client.call_gemini("Test prompt")

            assert response.success is True
            assert response.content == "Test response"
            assert response.error is None

    @pytest.mark.asyncio
    async def test_call_gemini_with_options(self):
        """Test Gemini call with custom options."""
        client = GeminiCLIClient()
        client._verified_auth = True

        options = GeminiOptions(model="gemini-pro", sandbox=True, debug=True)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Test response", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            response = await client.call_gemini("Test prompt", options)

            # Verify command was called with correct arguments
            call_args = mock_subprocess.call_args[0]
            assert "gemini" in call_args
            assert "-m" in call_args
            assert "gemini-pro" in call_args
            assert "-s" in call_args  # sandbox flag
            assert "-d" in call_args  # debug flag

            assert response.success is True

    @pytest.mark.asyncio
    async def test_call_gemini_error(self):
        """Test Gemini call with error."""
        client = GeminiCLIClient()
        client._verified_auth = True

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock failed subprocess
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"Error message")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process

            response = await client.call_gemini("Test prompt")

            assert response.success is False
            assert response.error == "Error message"

    @pytest.mark.asyncio
    async def test_call_with_structured_prompt(self):
        """Test structured prompt call."""
        client = GeminiCLIClient()

        with patch.object(client, "call_gemini") as mock_call:
            mock_call.return_value = GeminiResponse(
                content="Structured response",
                success=True,
                input_prompt="System: System instructions\n\nContext:\nContext info\n\nUser: User request",
            )

            response = await client.call_with_structured_prompt(
                system_prompt="System instructions",
                user_prompt="User request",
                context="Context info",
            )

            # Verify the prompt was properly formatted
            call_args = mock_call.call_args[0]
            prompt = call_args[0]
            assert "System: System instructions" in prompt
            assert "Context:\nContext info" in prompt
            assert "User: User request" in prompt

            assert response.content == "Structured response"

    def test_update_default_options(self):
        """Test updating default options."""
        client = GeminiCLIClient()

        client.update_default_options(model="gemini-pro", sandbox=True)

        assert client.default_options.model == "gemini-pro"
        assert client.default_options.sandbox is True
        assert client.default_options.debug is False  # Unchanged

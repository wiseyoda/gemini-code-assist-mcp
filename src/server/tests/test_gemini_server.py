"""
Tests for the main Gemini MCP server.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.core.gemini_client import GeminiResponse
from src.server.gemini_server import (
    CodeIssue,
    CodeReviewResponse,
    CodeSuggestion,
    GeminiToolResponse,
    _normalize_issue,
    _normalize_suggestion,
    create_server,
)


class TestResponseModels:
    """Test response models."""

    def test_code_issue_model(self):
        """Test CodeIssue model."""
        issue = CodeIssue(line=10, severity="high", message="Missing error handling")
        assert issue.line == 10
        assert issue.severity == "high"
        assert issue.message == "Missing error handling"

    def test_code_issue_model_defaults(self):
        """Test CodeIssue with defaults."""
        issue = CodeIssue(message="Some issue")
        assert issue.line is None
        assert issue.severity is None
        assert issue.message == "Some issue"

    def test_code_suggestion_model(self):
        """Test CodeSuggestion model."""
        suggestion = CodeSuggestion(line=5, suggestion="Use type hints")
        assert suggestion.line == 5
        assert suggestion.suggestion == "Use type hints"

    def test_code_suggestion_model_defaults(self):
        """Test CodeSuggestion with defaults."""
        suggestion = CodeSuggestion(suggestion="Add docstring")
        assert suggestion.line is None
        assert suggestion.suggestion == "Add docstring"

    def test_code_review_response(self):
        """Test CodeReviewResponse model."""
        response = CodeReviewResponse(
            summary="Good code",
            issues=[CodeIssue(message="Minor issue")],
            suggestions=[CodeSuggestion(suggestion="Add tests")],
            rating="B+",
            input_prompt="Review this code",
            gemini_response="Good code overall"
        )
        assert response.summary == "Good code"
        assert len(response.issues) == 1
        assert len(response.suggestions) == 1
        assert response.rating == "B+"

    def test_gemini_tool_response(self):
        """Test GeminiToolResponse model."""
        response = GeminiToolResponse(
            result="Analysis complete",
            input_prompt="Analyze this",
            gemini_response="The analysis shows..."
        )
        assert response.result == "Analysis complete"
        assert response.metadata == {}


class TestNormalizationFunctions:
    """Test normalization helper functions."""

    def test_normalize_issue_from_string(self):
        """Test normalizing issue from plain string."""
        issue = _normalize_issue("Missing error handling")
        assert issue.message == "Missing error handling"
        assert issue.line is None
        assert issue.severity is None

    def test_normalize_issue_from_dict(self):
        """Test normalizing issue from dict."""
        issue = _normalize_issue({
            "line": 42,
            "severity": "high",
            "message": "SQL injection risk"
        })
        assert issue.line == 42
        assert issue.severity == "high"
        assert issue.message == "SQL injection risk"

    def test_normalize_issue_from_dict_with_issue_key(self):
        """Test normalizing issue when dict uses 'issue' key instead of 'message'."""
        issue = _normalize_issue({
            "line": 10,
            "issue": "Missing validation"
        })
        assert issue.line == 10
        assert issue.message == "Missing validation"

    def test_normalize_suggestion_from_string(self):
        """Test normalizing suggestion from plain string."""
        suggestion = _normalize_suggestion("Add type hints")
        assert suggestion.suggestion == "Add type hints"
        assert suggestion.line is None

    def test_normalize_suggestion_from_dict(self):
        """Test normalizing suggestion from dict."""
        suggestion = _normalize_suggestion({
            "line": 5,
            "suggestion": "Use encodeURIComponent"
        })
        assert suggestion.line == 5
        assert suggestion.suggestion == "Use encodeURIComponent"

    def test_normalize_suggestion_from_dict_with_text_key(self):
        """Test normalizing suggestion when dict uses 'text' key."""
        suggestion = _normalize_suggestion({
            "line": 3,
            "text": "Check response.ok before parsing"
        })
        assert suggestion.line == 3
        assert suggestion.suggestion == "Check response.ok before parsing"


class TestServerCreation:
    """Test server creation and configuration."""

    def test_create_server(self):
        """Test server creation."""
        server = create_server()
        assert server is not None
        assert server.name == "Gemini MCP Server"

    @patch('src.server.gemini_server.GeminiCLIClient')
    @patch('src.server.gemini_server.ConfigManager')
    def test_server_components_initialized(self, mock_config_manager, mock_client):
        """Test that server components are properly initialized."""
        mock_config_instance = Mock()
        mock_config_instance.config.name = "Test Server"
        mock_config_instance.config.gemini_options = Mock()
        mock_config_manager.return_value = mock_config_instance

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance

        server = create_server()

        mock_config_manager.assert_called_once()
        mock_client.assert_called_once()


class TestServerTools:
    """Test server tool functionality."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock MCP context."""
        context = AsyncMock()
        context.info = AsyncMock()
        context.error = AsyncMock()
        return context

    @pytest.fixture
    def mock_gemini_client(self):
        """Create a mock Gemini client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_code_review_tool_with_structured_response(
        self, mock_context, mock_gemini_client
    ):
        """Test code review with structured JSON response from Gemini."""
        # Gemini returns structured suggestions as dicts
        mock_response = GeminiResponse(
            content='```json\n{"summary": "Good code", "issues": [{"line": 10, "message": "Missing validation"}], "suggestions": [{"line": 2, "suggestion": "Use encodeURIComponent"}], "rating": "B+"}\n```',
            success=True,
            input_prompt="Review this code"
        )
        mock_gemini_client.call_with_structured_prompt.return_value = mock_response

        with patch('src.server.gemini_server.GeminiCLIClient') as mock_client_class:
            mock_client_class.return_value = mock_gemini_client

            server = create_server()

            tool = server._tool_manager.get_tool("gemini_review_code")
            assert tool is not None
            tool_func = tool.fn

            # Call with inline parameters (new API)
            result = await tool_func(
                code="def hello(): return 'world'",
                ctx=mock_context,
                language="python",
                focus="general"
            )

            assert isinstance(result, CodeReviewResponse)
            assert result.summary == "Good code"
            assert result.rating == "B+"
            assert len(result.issues) == 1
            assert result.issues[0].line == 10
            assert result.issues[0].message == "Missing validation"
            assert len(result.suggestions) == 1
            assert result.suggestions[0].line == 2
            assert result.suggestions[0].suggestion == "Use encodeURIComponent"
            mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_code_review_tool_with_string_suggestions(
        self, mock_context, mock_gemini_client
    ):
        """Test code review when suggestions come as plain strings."""
        mock_response = GeminiResponse(
            content='```json\n{"summary": "Good code", "issues": [], "suggestions": ["Add docstring", "Add type hints"], "rating": "B+"}\n```',
            success=True,
            input_prompt="Review this code"
        )
        mock_gemini_client.call_with_structured_prompt.return_value = mock_response

        with patch('src.server.gemini_server.GeminiCLIClient') as mock_client_class:
            mock_client_class.return_value = mock_gemini_client

            server = create_server()
            tool = server._tool_manager.get_tool("gemini_review_code")
            tool_func = tool.fn

            result = await tool_func(
                code="def hello(): return 'world'",
                ctx=mock_context
            )

            assert isinstance(result, CodeReviewResponse)
            assert len(result.suggestions) == 2
            assert result.suggestions[0].suggestion == "Add docstring"
            assert result.suggestions[1].suggestion == "Add type hints"

    @pytest.mark.asyncio
    async def test_code_review_tool_error(self, mock_context, mock_gemini_client):
        """Test code review with error."""
        mock_response = GeminiResponse(
            content="",
            success=False,
            error="API error",
            input_prompt="Review this code"
        )
        mock_gemini_client.call_with_structured_prompt.return_value = mock_response

        with patch('src.server.gemini_server.GeminiCLIClient') as mock_client_class:
            mock_client_class.return_value = mock_gemini_client

            server = create_server()

            tool = server._tool_manager.get_tool("gemini_review_code")
            tool_func = tool.fn

            result = await tool_func(code="test code", ctx=mock_context)

            assert isinstance(result, CodeReviewResponse)
            assert "error" in result.summary.lower() or "failed" in result.summary.lower()
            assert result.rating == "Failed"
            mock_context.error.assert_called()

    @pytest.mark.asyncio
    async def test_feature_plan_tool_success(self, mock_context, mock_gemini_client):
        """Test successful feature plan review."""
        mock_response = GeminiResponse(
            content="The feature plan looks good but needs more details on...",
            success=True,
            input_prompt="Review this plan"
        )
        mock_gemini_client.call_with_structured_prompt.return_value = mock_response

        with patch('src.server.gemini_server.GeminiCLIClient') as mock_client_class:
            mock_client_class.return_value = mock_gemini_client

            server = create_server()

            tool = server._tool_manager.get_tool("gemini_proofread_feature_plan")
            tool_func = tool.fn

            result = await tool_func(
                feature_plan="Add user authentication system",
                ctx=mock_context
            )

            assert isinstance(result, GeminiToolResponse)
            assert "good but needs more details" in result.result
            mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_bug_analysis_tool_success(self, mock_context, mock_gemini_client):
        """Test successful bug analysis."""
        mock_response = GeminiResponse(
            content="The bug is caused by a null pointer exception. To fix...",
            success=True,
            input_prompt="Analyze this bug"
        )
        mock_gemini_client.call_with_structured_prompt.return_value = mock_response

        with patch('src.server.gemini_server.GeminiCLIClient') as mock_client_class:
            mock_client_class.return_value = mock_gemini_client

            server = create_server()

            tool = server._tool_manager.get_tool("gemini_analyze_bug")
            tool_func = tool.fn

            result = await tool_func(
                bug_description="App crashes on startup",
                ctx=mock_context,
                error_logs="NullPointerException at line 42"
            )

            assert isinstance(result, GeminiToolResponse)
            assert "null pointer exception" in result.result.lower()
            mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_code_explanation_tool_success(
        self, mock_context, mock_gemini_client
    ):
        """Test successful code explanation."""
        mock_response = GeminiResponse(
            content="This code defines a lambda function that squares its input...",
            success=True,
            input_prompt="Explain this code"
        )
        mock_gemini_client.call_with_structured_prompt.return_value = mock_response

        with patch('src.server.gemini_server.GeminiCLIClient') as mock_client_class:
            mock_client_class.return_value = mock_gemini_client

            server = create_server()

            tool = server._tool_manager.get_tool("gemini_explain_code")
            tool_func = tool.fn

            result = await tool_func(
                code="lambda x: x**2",
                ctx=mock_context,
                language="python"
            )

            assert isinstance(result, GeminiToolResponse)
            assert "lambda function" in result.result.lower()
            mock_context.info.assert_called()


class TestServerResources:
    """Test server resources."""

    @pytest.mark.asyncio
    async def test_config_resource(self):
        """Test config resource."""
        server = create_server()

        resource = await server._resource_manager.get_resource("gemini://config")
        assert resource is not None

        result = resource.fn()

        config_data = json.loads(result)
        assert "name" in config_data
        assert "gemini_options" in config_data

    @pytest.mark.asyncio
    async def test_templates_resource(self):
        """Test templates resource."""
        server = create_server()

        resource = await server._resource_manager.get_resource("gemini://templates")
        assert resource is not None

        result = resource.fn()

        templates_data = json.loads(result)
        assert isinstance(templates_data, dict)
        assert "code_review" in templates_data

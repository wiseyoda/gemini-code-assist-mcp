"""
Main FastMCP server for Gemini integration.

This module implements the MCP server that provides tools for interacting
with Google Gemini CLI for development assistance.
"""

import json
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from ..core.config import ConfigManager
from ..core.gemini_client import GeminiCLIClient


class CodeIssue(BaseModel):
    """Model for a code review issue."""

    line: int | None = Field(default=None, description="Line number of the issue")
    severity: str | None = Field(default=None, description="Issue severity")
    message: str = Field(description="Issue description")


class CodeSuggestion(BaseModel):
    """Model for a code review suggestion."""

    line: int | None = Field(default=None, description="Line number for suggestion")
    suggestion: str = Field(description="Suggestion text")


class CodeReviewResponse(BaseModel):
    """Response model for code review."""

    summary: str = Field(description="Overall assessment summary")
    issues: list[CodeIssue] = Field(description="List of identified issues")
    suggestions: list[CodeSuggestion] = Field(description="Improvement suggestions")
    rating: str = Field(description="Overall code quality rating")
    input_prompt: str = Field(description="The prompt sent to Gemini")
    gemini_response: str = Field(description="The raw response from Gemini")


class GeminiToolResponse(BaseModel):
    """Generic response model for Gemini tools with input/output transparency."""

    result: str = Field(description="The processed result")
    input_prompt: str = Field(description="The prompt sent to Gemini")
    gemini_response: str = Field(description="The raw response from Gemini")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


def _normalize_issue(item: dict[str, Any] | str) -> CodeIssue:
    """
    Normalize an issue item to CodeIssue model.

    Args:
        item: Issue as dict or string

    Returns:
        Normalized CodeIssue instance
    """
    if isinstance(item, str):
        return CodeIssue(message=item)
    return CodeIssue(
        line=item.get("line"),
        severity=item.get("severity"),
        message=item.get("message", item.get("issue", str(item)))
    )


def _normalize_suggestion(item: dict[str, Any] | str) -> CodeSuggestion:
    """
    Normalize a suggestion item to CodeSuggestion model.

    Args:
        item: Suggestion as dict or string

    Returns:
        Normalized CodeSuggestion instance
    """
    if isinstance(item, str):
        return CodeSuggestion(suggestion=item)
    return CodeSuggestion(
        line=item.get("line"),
        suggestion=item.get("suggestion", item.get("text", str(item)))
    )


def create_server() -> FastMCP:
    """
    Create and configure the Gemini MCP server.
    
    Returns:
        Configured FastMCP server instance
    """
    # Initialize configuration
    config_manager = ConfigManager()
    server_config = config_manager.config

    # Create FastMCP server
    mcp = FastMCP(
        name=server_config.name,
        # Enable stateless HTTP for Claude Code compatibility
        stateless_http=True
    )

    # Initialize Gemini client
    gemini_client = GeminiCLIClient(server_config.gemini_options)

    @mcp.tool()
    async def gemini_review_code(
        code: str,
        ctx: Context,
        language: str | None = None,
        focus: str | None = "general",
    ) -> CodeReviewResponse:
        """
        Analyze code quality, style, and potential issues using Gemini.
        
        Args:
            code: Code to review
            language: Programming language
            focus: Focus area: general, security, performance, style, or bugs
        """
        await ctx.info(f"Starting code review for {len(code)} characters of code")

        try:
            # Get template and format prompt
            template = config_manager.get_template("code_review")
            if not template:
                raise ValueError("Code review template not found")

            # Determine language if not provided
            lang = language or "auto-detect"

            # Create focus instruction
            focus_map = {
                "security": "Focus specifically on security vulnerabilities and potential exploits.",
                "performance": "Focus on performance optimizations and bottlenecks.",
                "style": "Focus on code style, formatting, and best practices.",
                "bugs": "Focus on potential bugs and logical errors.",
                "general": "Provide a comprehensive review covering all aspects."
            }
            focus_instruction = focus_map.get(focus, focus_map["general"])

            # Format template
            system_prompt, user_prompt = template.format(
                language=lang,
                code=code,
                focus_instruction=focus_instruction
            )

            # Call Gemini
            response = await gemini_client.call_with_structured_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt
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
                        "suggestions": content.split('\n') if content else []
                    }

                # Normalize issues and suggestions to proper models
                raw_issues = parsed.get("issues", [])
                raw_suggestions = parsed.get("suggestions", [])

                normalized_issues = [_normalize_issue(i) for i in raw_issues]
                normalized_suggestions = [_normalize_suggestion(s) for s in raw_suggestions if s]

                return CodeReviewResponse(
                    summary=parsed.get("summary", "Code review completed"),
                    issues=normalized_issues,
                    suggestions=normalized_suggestions,
                    rating=parsed.get("rating", "Review completed"),
                    input_prompt=response.input_prompt,
                    gemini_response=response.content
                )

            except json.JSONDecodeError:
                # Fallback to simple text response
                return CodeReviewResponse(
                    summary=response.content[:200] + "..." if len(response.content) > 200 else response.content,
                    issues=[],
                    suggestions=[CodeSuggestion(suggestion=response.content)],
                    rating="Review completed (text format)",
                    input_prompt=response.input_prompt,
                    gemini_response=response.content
                )

        except Exception as e:
            await ctx.error(f"Code review failed: {str(e)}")
            return CodeReviewResponse(
                summary=f"Error during review: {str(e)}",
                issues=[],
                suggestions=[],
                rating="Failed",
                input_prompt="Error occurred before prompt creation",
                gemini_response=f"Error: {str(e)}"
            )

    @mcp.tool()
    async def gemini_proofread_feature_plan(
        feature_plan: str,
        ctx: Context,
        context: str | None = "",
        focus_areas: str | None = "completeness,feasibility,clarity",
    ) -> GeminiToolResponse:
        """
        Review and improve feature plans and specifications using Gemini.
        
        Args:
            feature_plan: Feature plan document
            context: Project context
            focus_areas: Areas to focus on
        """
        await ctx.info("Starting feature plan review")

        try:
            # Get template
            template = config_manager.get_template("feature_plan_review")
            if not template:
                raise ValueError("Feature plan review template not found")

            # Format template
            system_prompt, user_prompt = template.format(
                feature_plan=feature_plan,
                context=context,
                focus_areas=focus_areas
            )

            # Call Gemini
            response = await gemini_client.call_with_structured_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            if not response.success:
                raise ValueError(f"Gemini call failed: {response.error}")

            return GeminiToolResponse(
                result=response.content,
                input_prompt=response.input_prompt,
                gemini_response=response.content
            )

        except Exception as e:
            await ctx.error(f"Feature plan review failed: {str(e)}")
            return GeminiToolResponse(
                result=f"Error during feature plan review: {str(e)}",
                input_prompt="Error occurred before prompt creation",
                gemini_response=f"Error: {str(e)}"
            )

    @mcp.tool()
    async def gemini_analyze_bug(
        bug_description: str,
        ctx: Context,
        code_context: str | None = "",
        error_logs: str | None = "",
        environment: str | None = "",
        reproduction_steps: str | None = "",
        language: str | None = "",
    ) -> GeminiToolResponse:
        """
        Analyze bugs and suggest fixes using Gemini.
        
        Args:
            bug_description: Description of the bug
            code_context: Relevant code snippets
            error_logs: Error messages and logs
            environment: Environment details
            reproduction_steps: Steps to reproduce
            language: Programming language
        """
        await ctx.info("Starting bug analysis")

        try:
            # Get template
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
                reproduction_steps=reproduction_steps
            )

            # Call Gemini
            response = await gemini_client.call_with_structured_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            if not response.success:
                raise ValueError(f"Gemini call failed: {response.error}")

            return GeminiToolResponse(
                result=response.content,
                input_prompt=response.input_prompt,
                gemini_response=response.content
            )

        except Exception as e:
            await ctx.error(f"Bug analysis failed: {str(e)}")
            return GeminiToolResponse(
                result=f"Error during bug analysis: {str(e)}",
                input_prompt="Error occurred before prompt creation",
                gemini_response=f"Error: {str(e)}"
            )

    @mcp.tool()
    async def gemini_explain_code(
        code: str,
        ctx: Context,
        language: str | None = None,
        detail_level: str | None = "intermediate",
        questions: str | None = "",
    ) -> GeminiToolResponse:
        """
        Explain code functionality and implementation using Gemini.
        
        Args:
            code: Code to explain
            language: Programming language
            detail_level: Detail level: basic, intermediate, or advanced
            questions: Specific questions about the code
        """
        await ctx.info(f"Starting code explanation ({detail_level} level)")

        try:
            # Get template
            template = config_manager.get_template("code_explanation")
            if not template:
                raise ValueError("Code explanation template not found")

            # Determine language if not provided
            lang = language or "auto-detect"

            # Format template
            system_prompt, user_prompt = template.format(
                language=lang,
                code=code,
                detail_level=detail_level,
                questions=questions
            )

            # Call Gemini
            response = await gemini_client.call_with_structured_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            if not response.success:
                raise ValueError(f"Gemini call failed: {response.error}")

            return GeminiToolResponse(
                result=response.content,
                input_prompt=response.input_prompt,
                gemini_response=response.content
            )

        except Exception as e:
            await ctx.error(f"Code explanation failed: {str(e)}")
            return GeminiToolResponse(
                result=f"Error during code explanation: {str(e)}",
                input_prompt="Error occurred before prompt creation",
                gemini_response=f"Error: {str(e)}"
            )

    # Add resources for configuration and status
    @mcp.resource("gemini://config")
    def get_config() -> str:
        """Get current Gemini MCP server configuration."""
        config_dict = config_manager.get_config_dict()
        return json.dumps(config_dict, indent=2)

    @mcp.resource("gemini://templates")
    def list_templates() -> str:
        """List available prompt templates."""
        templates = config_manager.list_templates()
        return json.dumps(templates, indent=2)

    @mcp.resource("gemini://status")
    async def get_status() -> str:
        """Get Gemini CLI status and authentication info."""
        try:
            # Test authentication
            auth_valid = await gemini_client.verify_authentication()
            status = {
                "authenticated": auth_valid,
                "model": config_manager.config.gemini_options.model,
                "cli_available": True
            }
        except Exception as e:
            status = {
                "authenticated": False,
                "error": str(e),
                "cli_available": False
            }

        return json.dumps(status, indent=2)

    return mcp

"""
Configuration management for the Gemini MCP Server.

This module handles server configuration, including Gemini CLI options
and template management.
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .gemini_client import GeminiOptions


class ServerConfig(BaseModel):
    """Configuration for the MCP server."""

    name: str = Field(default="Gemini MCP Server", description="Server name")
    version: str = Field(default="0.1.0", description="Server version")
    description: str = Field(
        default="MCP server for Google Gemini CLI integration",
        description="Server description"
    )

    # Gemini CLI settings
    gemini_options: GeminiOptions = Field(
        default_factory=GeminiOptions,
        description="Default Gemini CLI options"
    )

    # Server behavior
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    max_file_size_mb: float = Field(default=10.0, description="Maximum file size to process")
    max_context_files: int = Field(default=20, description="Maximum files to include in context")

    # Template settings
    templates_dir: Path | None = Field(default=None, description="Custom templates directory")

    model_config = ConfigDict(extra="forbid")


class PromptTemplate(BaseModel):
    """Template for generating prompts."""

    name: str = Field(description="Template name")
    description: str = Field(description="Template description")
    system_prompt: str = Field(description="System-level instructions")
    user_template: str = Field(description="User prompt template with placeholders")
    variables: dict[str, str] = Field(
        default_factory=dict,
        description="Template variable descriptions"
    )

    def format(self, **kwargs) -> tuple[str, str]:
        """
        Format the template with provided variables.
        
        Args:
            **kwargs: Variables to substitute in template
            
        Returns:
            Tuple of (system_prompt, formatted_user_prompt)
        """
        user_prompt = self.user_template.format(**kwargs)
        return self.system_prompt, user_prompt


class ConfigManager:
    """Manages server configuration and templates."""

    def __init__(self, config: ServerConfig | None = None):
        """
        Initialize configuration manager.
        
        Args:
            config: Server configuration (uses defaults if None)
        """
        self.config = config or ServerConfig()
        self._templates: dict[str, PromptTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default prompt templates."""
        # Code review template
        self._templates["code_review"] = PromptTemplate(
            name="code_review",
            description="Template for code review and analysis",
            system_prompt=(
                "You are an expert code reviewer. Analyze the provided code for:\n"
                "1. Code quality and style issues\n"
                "2. Potential bugs and security vulnerabilities\n"
                "3. Performance optimizations\n"
                "4. Best practices and maintainability\n\n"
                "Provide specific, actionable feedback with line numbers when possible. "
                "Format your response as structured JSON with sections for issues, "
                "suggestions, and overall assessment."
            ),
            user_template=(
                "Please review the following {language} code:\n\n"
                "```{language}\n{code}\n```\n\n"
                "{focus_instruction}"
            ),
            variables={
                "language": "Programming language",
                "code": "Code to review",
                "focus_instruction": "Specific focus areas or instructions"
            }
        )

        # Feature plan review template
        self._templates["feature_plan_review"] = PromptTemplate(
            name="feature_plan_review",
            description="Template for reviewing feature plans and specifications",
            system_prompt=(
                "You are a senior software architect and product manager. "
                "Review the provided feature plan for:\n"
                "1. Clarity and completeness of requirements\n"
                "2. Technical feasibility and implementation approach\n"
                "3. Missing considerations (security, performance, testing)\n"
                "4. User experience and edge cases\n"
                "5. Dependencies and integration points\n\n"
                "Provide constructive feedback to improve the plan."
            ),
            user_template=(
                "Please review this feature plan:\n\n"
                "{feature_plan}\n\n"
                "Context: {context}\n\n"
                "Focus areas: {focus_areas}"
            ),
            variables={
                "feature_plan": "Feature plan document",
                "context": "Project context and constraints",
                "focus_areas": "Specific areas to focus on"
            }
        )

        # Bug analysis template
        self._templates["bug_analysis"] = PromptTemplate(
            name="bug_analysis",
            description="Template for analyzing bugs and suggesting fixes",
            system_prompt=(
                "You are a debugging expert. Analyze the provided bug report and code to:\n"
                "1. Identify the root cause of the issue\n"
                "2. Explain why the bug occurs\n"
                "3. Suggest specific fixes with code examples\n"
                "4. Recommend preventive measures\n"
                "5. Consider edge cases and testing strategies\n\n"
                "Be thorough but concise in your analysis."
            ),
            user_template=(
                "Bug Description: {bug_description}\n\n"
                "Error Logs:\n{error_logs}\n\n"
                "Relevant Code:\n```{language}\n{code_context}\n```\n\n"
                "Environment: {environment}\n\n"
                "Steps to reproduce: {reproduction_steps}"
            ),
            variables={
                "bug_description": "Description of the bug",
                "error_logs": "Error messages and logs",
                "code_context": "Relevant code snippets",
                "language": "Programming language",
                "environment": "Environment details",
                "reproduction_steps": "Steps to reproduce the issue"
            }
        )

        # Code explanation template
        self._templates["code_explanation"] = PromptTemplate(
            name="code_explanation",
            description="Template for explaining code functionality",
            system_prompt=(
                "You are a technical educator. Explain the provided code in a clear, "
                "comprehensive way that helps others understand:\n"
                "1. What the code does (high-level purpose)\n"
                "2. How it works (step-by-step breakdown)\n"
                "3. Key concepts and patterns used\n"
                "4. Important implementation details\n"
                "5. Potential improvements or alternatives\n\n"
                "Adjust your explanation level based on the requested detail level."
            ),
            user_template=(
                "Please explain this {language} code:\n\n"
                "```{language}\n{code}\n```\n\n"
                "Detail level: {detail_level}\n"
                "Specific questions: {questions}"
            ),
            variables={
                "language": "Programming language",
                "code": "Code to explain",
                "detail_level": "Level of detail (basic, intermediate, advanced)",
                "questions": "Specific questions about the code"
            }
        )

    def get_template(self, name: str) -> PromptTemplate | None:
        """
        Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            PromptTemplate if found, None otherwise
        """
        return self._templates.get(name)

    def list_templates(self) -> dict[str, str]:
        """
        List available templates.
        
        Returns:
            Dictionary mapping template names to descriptions
        """
        return {name: template.description for name, template in self._templates.items()}

    def add_template(self, template: PromptTemplate) -> None:
        """
        Add a custom template.
        
        Args:
            template: PromptTemplate to add
        """
        self._templates[template.name] = template

    def update_gemini_options(self, **kwargs) -> None:
        """
        Update Gemini CLI options.
        
        Args:
            **kwargs: Options to update
        """
        current_dict = self.config.gemini_options.model_dump()
        current_dict.update(kwargs)
        self.config.gemini_options = GeminiOptions(**current_dict)

    def get_config_dict(self) -> dict:
        """
        Get configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config.model_dump()

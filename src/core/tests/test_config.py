"""
Tests for configuration management.
"""

from src.core.config import ConfigManager, PromptTemplate, ServerConfig
from src.core.gemini_client import GeminiOptions


class TestServerConfig:
    """Test ServerConfig model."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ServerConfig()
        assert config.name == "Gemini MCP Server"
        assert config.version == "0.1.0"
        assert config.enable_caching is True
        assert config.max_file_size_mb == 10.0

    def test_custom_values(self):
        """Test custom configuration values."""
        gemini_opts = GeminiOptions(model="gemini-pro")
        config = ServerConfig(
            name="Custom Server",
            gemini_options=gemini_opts,
            enable_caching=False
        )
        assert config.name == "Custom Server"
        assert config.gemini_options.model == "gemini-pro"
        assert config.enable_caching is False


class TestPromptTemplate:
    """Test PromptTemplate functionality."""

    def test_template_creation(self):
        """Test creating a prompt template."""
        template = PromptTemplate(
            name="test_template",
            description="Test template",
            system_prompt="System instructions",
            user_template="User prompt with {variable}",
            variables={"variable": "Test variable"}
        )
        assert template.name == "test_template"
        assert template.description == "Test template"

    def test_template_formatting(self):
        """Test template formatting with variables."""
        template = PromptTemplate(
            name="test",
            description="Test",
            system_prompt="System instructions",
            user_template="User: {request}",
            variables={"request": "Test request"}
        )

        # Note: format() only formats user_template, system_prompt is returned as-is
        system, user = template.format(request="Help me")
        assert system == "System instructions"
        assert user == "User: Help me"


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_initialization(self):
        """Test config manager initialization."""
        manager = ConfigManager()
        assert manager.config.name == "Gemini MCP Server"
        assert len(manager._templates) > 0

    def test_initialization_with_config(self):
        """Test config manager with custom config."""
        config = ServerConfig(name="Custom Server")
        manager = ConfigManager(config)
        assert manager.config.name == "Custom Server"

    def test_default_templates_loaded(self):
        """Test that default templates are loaded."""
        manager = ConfigManager()

        # Check that key templates exist
        assert manager.get_template("code_review") is not None
        assert manager.get_template("feature_plan_review") is not None
        assert manager.get_template("bug_analysis") is not None
        assert manager.get_template("code_explanation") is not None

    def test_get_template(self):
        """Test getting a template by name."""
        manager = ConfigManager()

        template = manager.get_template("code_review")
        assert template is not None
        assert template.name == "code_review"
        assert "code reviewer" in template.system_prompt.lower()

        # Test non-existent template
        assert manager.get_template("nonexistent") is None

    def test_list_templates(self):
        """Test listing available templates."""
        manager = ConfigManager()

        templates = manager.list_templates()
        assert isinstance(templates, dict)
        assert "code_review" in templates
        assert "feature_plan_review" in templates
        assert len(templates) >= 4

    def test_add_template(self):
        """Test adding a custom template."""
        manager = ConfigManager()

        custom_template = PromptTemplate(
            name="custom_test",
            description="Custom test template",
            system_prompt="Custom system",
            user_template="Custom user {var}",
            variables={"var": "variable"}
        )

        manager.add_template(custom_template)

        retrieved = manager.get_template("custom_test")
        assert retrieved is not None
        assert retrieved.name == "custom_test"
        assert retrieved.description == "Custom test template"

    def test_update_gemini_options(self):
        """Test updating Gemini options."""
        manager = ConfigManager()

        # Check initial value
        assert manager.config.gemini_options.model == "gemini-3-pro-preview"
        assert manager.config.gemini_options.sandbox is False

        # Update options
        manager.update_gemini_options(model="gemini-pro", sandbox=True)

        # Check updated values
        assert manager.config.gemini_options.model == "gemini-pro"
        assert manager.config.gemini_options.sandbox is True
        assert manager.config.gemini_options.debug is False  # Unchanged

    def test_get_config_dict(self):
        """Test getting configuration as dictionary."""
        manager = ConfigManager()

        config_dict = manager.get_config_dict()
        assert isinstance(config_dict, dict)
        assert "name" in config_dict
        assert "gemini_options" in config_dict
        assert config_dict["name"] == "Gemini MCP Server"

    def test_code_review_template_formatting(self):
        """Test code review template formatting."""
        manager = ConfigManager()
        template = manager.get_template("code_review")

        system, user = template.format(
            language="python",
            code="def hello(): pass",
            focus_instruction="Focus on style"
        )

        assert "code reviewer" in system.lower()
        assert "python" in user
        assert "def hello(): pass" in user
        assert "Focus on style" in user

    def test_feature_plan_template_formatting(self):
        """Test feature plan template formatting."""
        manager = ConfigManager()
        template = manager.get_template("feature_plan_review")

        system, user = template.format(
            feature_plan="Add user login",
            context="Web application",
            focus_areas="security,usability"
        )

        assert "architect" in system.lower() or "product manager" in system.lower()
        assert "Add user login" in user
        assert "Web application" in user
        assert "security,usability" in user

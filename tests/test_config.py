import os
import pytest
from main import C, efloat, eint, estr, elist


class TestConfigHelpers:
    """Tests for configuration helper functions."""

    @pytest.mark.parametrize(
        "value,default,expected",
        [
            ("123.45", 0.0, 123.45),  # Normal case
            ("0", 1.0, 0.0),  # Zero
            ("-10.5", 1.0, -10.5),  # Negative
            ("invalid", 99.9, 99.9),  # Invalid - use default
            (None, 42.0, 42.0),  # None - use default
        ],
    )
    def test_efloat(self, monkeypatch, value, default, expected):
        """Test efloat helper with various inputs."""
        if value is not None:
            monkeypatch.setenv("TEST_VAR", value)
        else:
            monkeypatch.delenv("TEST_VAR", raising=False)

        result = efloat("TEST_VAR", default)
        assert result == expected
        assert isinstance(result, float)

    @pytest.mark.parametrize(
        "value,default,expected",
        [
            ("test", "default", "test"),  # Normal case
            ("", "default", "default"),  # Empty string - should use default
            (None, "default", "default"),  # None - use default
        ],
        ids=["normal", "empty", "none"],
    )
    def test_estr(self, monkeypatch, value, default, expected):
        """Test estr helper with various inputs."""
        if value is not None:
            monkeypatch.setenv("TEST_VAR", value)
        else:
            monkeypatch.delenv("TEST_VAR", raising=False)

        result = estr("TEST_VAR", default)
        assert result == expected
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        "value,default,expected",
        [
            ("a,b,c", ["default"], ["a", "b", "c"]),  # Normal case
            ("single", ["default"], ["single"]),  # Single item
            ("a, b, c", ["default"], ["a", "b", "c"]),  # With spaces
            ("", ["default"], ["default"]),  # Empty string - should use default
            (None, ["default"], ["default"]),  # None - use default
        ],
        ids=["normal", "single", "spaces", "empty", "none"],
    )
    def test_elist(self, monkeypatch, value, default, expected):
        """Test elist helper with various inputs."""
        if value is not None:
            monkeypatch.setenv("TEST_VAR", value)
        else:
            monkeypatch.delenv("TEST_VAR", raising=False)

        result = elist("TEST_VAR", default)
        assert result == expected
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)


class TestConfigClass:
    """Tests for the C configuration class."""

    def test_config_loading(self, mock_env, monkeypatch):
        """Test configuration loading from environment."""
        # We need to reload the module to pick up the mocked environment variables
        import importlib
        import main as main_module

        importlib.reload(main_module)

        # Now test the reloaded C class
        assert main_module.C.EMAIL_ADDRESS == "test@example.com"
        assert main_module.C.EMAIL_PASSWORD == "test_password"
        assert main_module.C.FRED_API_KEY == "test_fred_key"

        # Test float values
        assert main_module.C.BTC_DOM_THRESHOLD == 45.0
        assert main_module.C.M2_FLAT_THRESHOLD == 0.001
        assert main_module.C.ALT_PULLBACK == 0.90
        assert isinstance(main_module.C.BTC_DOM_THRESHOLD, float)

        # Test int values
        assert main_module.C.TRENDS_HITS_REQ == 2
        assert isinstance(main_module.C.TRENDS_HITS_REQ, int)

        # Test list values
        assert main_module.C.SOCIAL_TERMS == ["bitcoin", "crypto", "eth"]
        assert isinstance(main_module.C.SOCIAL_TERMS, list)
        assert all(isinstance(term, str) for term in main_module.C.SOCIAL_TERMS)

    def test_config_defaults(self, monkeypatch):
        """Test configuration defaults when environment variables are not set."""
        # Clear all relevant environment variables
        for key in [
            "EMAIL_ADDRESS",
            "EMAIL_PASSWORD",
            "FRED_API_KEY",
            "BTC_DOM_THRESHOLD",
            "M2_FLAT_THRESHOLD",
            "ALT_PULLBACK",
            "TRENDS_HITS_REQ",
            "SOCIAL_TERMS",
        ]:
            monkeypatch.delenv(key, raising=False)

        # Reload the module to pick up the default values
        import importlib
        import main as main_module

        importlib.reload(main_module)

        # Test default values
        assert main_module.C.BTC_DOM_THRESHOLD == 45.0
        assert main_module.C.M2_FLAT_THRESHOLD == 0.001
        assert main_module.C.ALT_PULLBACK == 0.90
        assert main_module.C.TRENDS_HITS_REQ == 2
        assert isinstance(main_module.C.SOCIAL_TERMS, list)

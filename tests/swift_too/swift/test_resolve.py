from unittest.mock import Mock, patch

from swifttools.swift_too.swift.resolve import TOOAPIAutoResolve


class TestValidateName:
    def test_validate_name_with_name_field(self):
        """Test that validate_name resolves coordinates when name is provided."""
        mock_resolve = Mock()
        mock_resolve.status.warnings = []
        mock_resolve.status.errors = []
        mock_resolve.ra = 123.456
        mock_resolve.dec = 78.901

        with patch("swifttools.swift_too.api_resolve.SwiftResolve", return_value=mock_resolve):
            values = {"name": "M31"}
            result = TOOAPIAutoResolve.validate_name(values)

            assert result["ra"] == 123.456
            assert result["dec"] == 78.901
            assert result["name"] == "M31"

    def test_validate_name_with_source_name_field(self):
        """Test that validate_name handles source_name field and sets it as name."""
        mock_resolve = Mock()
        mock_resolve.status.warnings = []
        mock_resolve.status.errors = []
        mock_resolve.ra = 45.678
        mock_resolve.dec = -12.345

        with patch("swifttools.swift_too.api_resolve.SwiftResolve", return_value=mock_resolve):
            values = {"source_name": "NGC1234"}
            result = TOOAPIAutoResolve.validate_name(values)

            assert result["ra"] == 45.678
            assert result["dec"] == -12.345
            assert result["name"] == "NGC1234"

    def test_validate_name_with_resolve_warnings(self):
        """Test that validate_name doesn't set coordinates when resolve has warnings."""
        mock_resolve = Mock()
        mock_resolve.status.warnings = ["Some warning"]
        mock_resolve.status.errors = []

        with patch("swifttools.swift_too.api_resolve.SwiftResolve", return_value=mock_resolve):
            values = {"name": "InvalidSource"}
            result = TOOAPIAutoResolve.validate_name(values)

            assert "ra" not in result
            assert "dec" not in result
            assert result["name"] == "InvalidSource"

    def test_validate_name_with_resolve_errors(self):
        """Test that validate_name doesn't set coordinates when resolve has errors."""
        mock_resolve = Mock()
        mock_resolve.status.warnings = []
        mock_resolve.status.errors = ["Resolution failed"]

        with patch("swifttools.swift_too.api_resolve.SwiftResolve", return_value=mock_resolve):
            values = {"name": "InvalidSource"}
            result = TOOAPIAutoResolve.validate_name(values)

            assert "ra" not in result
            assert "dec" not in result
            assert result["name"] == "InvalidSource"

    def test_validate_name_with_none_name(self):
        """Test that validate_name handles None name gracefully."""
        values = {"name": None}
        result = TOOAPIAutoResolve.validate_name(values)

        assert result == {"name": None}

    def test_validate_name_with_no_name_field(self):
        """Test that validate_name handles missing name field gracefully."""
        values = {"other_field": "value"}
        result = TOOAPIAutoResolve.validate_name(values)

        assert result == {"other_field": "value"}

    def test_validate_name_with_non_string_name(self):
        """Test that validate_name handles non-string name gracefully."""
        values = {"name": 12345}
        result = TOOAPIAutoResolve.validate_name(values)

        assert result == {"name": 12345}

    def test_validate_name_preserves_existing_fields(self):
        """Test that validate_name preserves other fields in values."""
        mock_resolve = Mock()
        mock_resolve.status.warnings = []
        mock_resolve.status.errors = []
        mock_resolve.ra = 100.0
        mock_resolve.dec = 50.0

        with patch("swifttools.swift_too.api_resolve.SwiftResolve", return_value=mock_resolve):
            values = {"name": "M31", "existing_field": "existing_value"}
            result = TOOAPIAutoResolve.validate_name(values)

            assert result["ra"] == 100.0
            assert result["dec"] == 50.0
            assert result["name"] == "M31"
            assert result["existing_field"] == "existing_value"

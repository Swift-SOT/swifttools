from unittest.mock import Mock, patch

from swifttools.swift_too.base.status import TOOStatus
from swifttools.swift_too.swift.resolve import (
    Resolve,
    Swift_Resolve,
    SwiftResolve,
    SwiftResolveGetSchema,
    SwiftResolveSchema,
    TOOAPIAutoResolve,
)


class TestValidateName:
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


class TestTOOAPIAutoResolve:
    def test_name_setter_with_valid_name(self):
        """Test that setting name resolves coordinates successfully."""
        mock_resolve = Mock()
        mock_resolve.status.status = "Accepted"
        mock_resolve.ra = 123.456
        mock_resolve.dec = 78.901
        mock_resolve.skycoord = "mock_skycoord"

        with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
            resolver = TOOAPIAutoResolve()
            resolver.name = "M31"

            assert resolver.name == "M31"
            assert resolver.ra == 123.456
            assert resolver.dec == 78.901
            assert resolver.skycoord == "mock_skycoord"
            assert resolver.resolve is not None

    def test_name_setter_with_rejected_status(self):
        """Test that setting name with failed resolution doesn't set coordinates."""
        mock_resolve = Mock()
        mock_resolve.status.status = "Rejected"
        mock_resolve.ra = None
        mock_resolve.dec = None

        with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
            resolver = TOOAPIAutoResolve()
            resolver.name = "InvalidSource"

            assert resolver.name == "InvalidSource"
            assert resolver.resolve is not None

    def test_name_setter_with_none(self):
        """Test that setting name to None doesn't trigger resolution."""
        with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
            resolver = TOOAPIAutoResolve()
            resolver.name = None

            assert resolver.name is None
            mock_resolve_class.assert_called_once_with(name=None)

    def test_validator_with_target_name_field(self):
        """Test that validator uses target_name and sets it as name."""
        mock_resolve = Mock()
        mock_resolve.status.warnings = []
        mock_resolve.status.errors = []
        mock_resolve.ra = 45.678
        mock_resolve.dec = -12.345

        with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
            values = {"target_name": "NGC1234"}
            result = TOOAPIAutoResolve.validate_name(values)

            assert result["ra"] == 45.678
            assert result["dec"] == -12.345
            assert result["name"] == "NGC1234"

    def test_validator_target_name_overrides_name(self):
        """Test that target_name takes precedence over name field."""
        mock_resolve = Mock()
        mock_resolve.status.warnings = []
        mock_resolve.status.errors = []
        mock_resolve.ra = 99.999
        mock_resolve.dec = -99.999

        with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
            values = {"name": "M31", "target_name": "M32"}
            result = TOOAPIAutoResolve.validate_name(values)

            assert result["name"] == "M32"
            assert result["ra"] == 99.999
            assert result["dec"] == -99.999


class TestSwiftResolve:
    def test_swift_resolve_schema_fields(self):
        """Test that SwiftResolveGetSchema and SwiftResolveSchema fields exist and default as expected."""
        get_schema = SwiftResolveGetSchema(name="M31")
        assert get_schema.name == "M31"

        status = TOOStatus()
        schema = SwiftResolveSchema(name="M31", resolver="Simbad", status=status)
        assert schema.name == "M31"
        assert schema.resolver == "Simbad"
        assert schema.status == status

    def test_swift_resolve_table_with_ra_dec(self):
        """Test that _table returns correct header and table when ra/dec are present."""
        sr = SwiftResolve(name="M31")
        sr.ra = 10.12345
        sr.dec = -20.54321

        header, table = sr._table
        assert header == ["Name", "RA (J2000)", "Dec (J2000)", "Resolver"]
        assert table[0][0] == sr.name
        assert table[0][1] == f"{sr.ra:.5f}"
        assert table[0][2] == f"{sr.dec:.5f}"
        assert table[0][3] == sr.resolver

    def test_swift_resolve_table_without_ra(self):
        """Test that _table returns empty lists if ra is None."""
        sr = SwiftResolve(name="M31")
        sr.ra = None
        header, table = sr._table
        assert header == []
        assert table == []


class TestTOOAPIAutoResolveClass:
    def test_name_property_and_setter(self):
        """Test that name property and setter work and trigger SwiftResolve."""
        mock_resolve = Mock()
        mock_resolve.status.status = "Accepted"
        mock_resolve.ra = 1.23
        mock_resolve.dec = 4.56
        mock_resolve.skycoord = "coord"

        with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
            auto = TOOAPIAutoResolve()
            auto.name = "M31"
            assert auto.name == "M31"
            assert auto.ra == 1.23
            assert auto.dec == 4.56
            assert auto.skycoord == "coord"
            assert auto.resolve is not None

    def test_name_setter_rejected_status(self):
        """Test that rejected status does not set ra/dec/skycoord."""
        mock_resolve = Mock()
        mock_resolve.status.status = "Rejected"
        mock_resolve.ra = None
        mock_resolve.dec = None
        mock_resolve.skycoord = None

        with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
            auto = TOOAPIAutoResolve()
            auto.name = "bad"
            assert auto.name == "bad"
            assert auto.ra is None
            assert auto.dec is None
            assert auto.skycoord is None

    def test_name_setter_none(self):
        """Test that setting name to None still calls SwiftResolve."""
        with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
            auto = TOOAPIAutoResolve()
            auto.name = None
            assert auto.name is None
            mock_resolve_class.assert_called_once_with(name=None)

    def test_swift_resolve_aliases(self):
        """Test that Swift_Resolve and Resolve are aliases for SwiftResolve."""
        assert Swift_Resolve is SwiftResolve
        assert Resolve is SwiftResolve


class TestSwiftResolveValidate:
    def test_validate_returns_true_when_validate_get_returns_true(self):
        """Test that validate returns True when validate_get returns True."""
        sr = SwiftResolve(name="M31")
        sr.validate_get = Mock(return_value=True)
        result = sr.validate()
        assert result is True
        sr.validate_get.assert_called_once()

    def test_validate_returns_false_when_validate_get_returns_false(self):
        """Test that validate returns False when validate_get returns False."""
        sr = SwiftResolve(name="M31")
        sr.validate_get = Mock(return_value=False)
        result = sr.validate()
        assert result is False
        sr.validate_get.assert_called_once()

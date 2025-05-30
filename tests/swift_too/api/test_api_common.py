import datetime as dt
from datetime import datetime

from swifttools.swift_too.api_common import _tablefy, convert_to_dt


class TestConvertToDt:
    def test_convert_to_dt_with_datetime(self):
        """Test that convert_to_dt handles datetime objects."""
        dt = datetime(2023, 1, 15, 12, 30, 45)
        result = convert_to_dt(dt)
        assert result == datetime(2023, 1, 15, 12, 30, 45)
        assert result.tzinfo is None

    def test_convert_to_dt_with_string(self):
        """Test that convert_to_dt handles string representations."""
        dt_str = "2023-01-15T12:30:45"
        result = convert_to_dt(dt_str)
        assert result == datetime(2023, 1, 15, 12, 30, 45)

    def test_convert_to_dt_with_timezone_aware(self):
        """Test that convert_to_dt removes timezone info."""
        tz_aware = datetime(2023, 1, 15, 12, 30, 45, tzinfo=dt.timezone.utc)
        result = convert_to_dt(tz_aware)
        assert result.tzinfo is None


class TestTablefy:
    def test_tablefy_with_header(self):
        """Test _tablefy with header and data."""
        table = [["row1col1", "row1col2"], ["row2col1", "row2col2"]]
        header = ["Header1", "Header2"]
        result = _tablefy(table, header)

        assert "<table>" in result
        assert "<thead>" in result
        assert "<th style='text-align: left;'>Header1</th>" in result
        assert "<th style='text-align: left;'>Header2</th>" in result
        assert "<td style='text-align: left;'>row1col1</td>" in result

    def test_tablefy_without_header(self):
        """Test _tablefy without header."""
        table = [["data1", "data2"]]
        result = _tablefy(table)

        assert "<table>" in result
        assert "<thead>" not in result
        assert "<td style='text-align: left;'>data1</td>" in result

    def test_tablefy_with_newlines(self):
        """Test _tablefy replaces newlines with <br>."""
        table = [["line1\nline2", "single"]]
        result = _tablefy(table)

        assert "line1<br>line2" in result

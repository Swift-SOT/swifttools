from datetime import datetime, timedelta

import pytest
from swifttools.swift_too.swift_datetime import swiftdatetime


class TestSwiftDatetimeSub:
    def test_sub_same_utc_base(self):
        """Test subtraction when both swiftdatetime objects have isutc=True."""
        dt1 = swiftdatetime(2023, 1, 1, 12, 0, 0)
        dt1.isutc = True
        dt2 = swiftdatetime(2023, 1, 1, 10, 0, 0)
        dt2.isutc = True

        result = dt1 - dt2
        assert result == timedelta(hours=2)

    def test_sub_same_swift_base(self):
        """Test subtraction when both swiftdatetime objects have isutc=False."""
        dt1 = swiftdatetime(2023, 1, 1, 12, 0, 0)
        dt1.isutc = False
        dt2 = swiftdatetime(2023, 1, 1, 10, 0, 0)
        dt2.isutc = False

        result = dt1 - dt2
        assert result == timedelta(hours=2)

    def test_sub_mixed_base_with_utcf(self):
        """Test subtraction with different time bases when both have UTCF."""
        dt1 = swiftdatetime(2023, 1, 1, 12, 0, 0)
        dt1.isutc = True
        dt1.utcf = 100.0

        dt2 = swiftdatetime(2023, 1, 1, 10, 0, 0)
        dt2.isutc = False
        dt2.utcf = 50.0

        result = dt1 - dt2
        expected = dt1 - dt2.utctime
        assert result == expected

    def test_sub_mixed_base_swift_minus_utc(self):
        """Test subtraction when self is Swift time and other is UTC time."""
        dt1 = swiftdatetime(2023, 1, 1, 12, 0, 0)
        dt1.isutc = False
        dt1.utcf = 100.0

        dt2 = swiftdatetime(2023, 1, 1, 10, 0, 0)
        dt2.isutc = True
        dt2.utcf = 50.0

        result = dt1 - dt2
        expected = dt1.utctime - dt2.utctime
        assert result == expected

    def test_sub_mixed_base_no_utcf_raises_error(self):
        """Test that subtraction with mismatched bases and no UTCF raises ArithmeticError."""
        dt1 = swiftdatetime(2023, 1, 1, 12, 0, 0)
        dt1.isutc = True

        dt2 = swiftdatetime(2023, 1, 1, 10, 0, 0)
        dt2.isutc = False

        with pytest.raises(ArithmeticError, match="Cannot subtract mismatched time zones with no UTCF"):
            dt1 - dt2

    def test_sub_mixed_base_partial_utcf_raises_error(self):
        """Test that subtraction raises error when only one object has UTCF."""
        dt1 = swiftdatetime(2023, 1, 1, 12, 0, 0)
        dt1.isutc = True
        dt1.utcf = 100.0

        dt2 = swiftdatetime(2023, 1, 1, 10, 0, 0)
        dt2.isutc = False
        # dt2.utcf is None

        with pytest.raises(ArithmeticError, match="Cannot subtract mismatched time zones with no UTCF"):
            dt1 - dt2

    def test_sub_with_timedelta(self):
        """Test subtraction with a timedelta object."""
        dt = swiftdatetime(2023, 1, 1, 12, 0, 0)
        dt.isutc = True
        td = timedelta(hours=2)

        result = dt - td
        expected = swiftdatetime(2023, 1, 1, 10, 0, 0)
        expected.isutc = True

        assert result.year == expected.year
        assert result.month == expected.month
        assert result.day == expected.day
        assert result.hour == expected.hour
        assert result.minute == expected.minute
        assert result.second == expected.second
        assert result.isutc == expected.isutc

    def test_sub_with_regular_datetime(self):
        """Test subtraction with a regular datetime object."""
        dt = swiftdatetime(2023, 1, 1, 12, 0, 0)
        dt.isutc = True
        regular_dt = datetime(2023, 1, 1, 10, 0, 0)

        result = dt - regular_dt
        assert result == timedelta(hours=2)

    def test_sub_preserves_isutc_attribute(self):
        """Test that subtraction with timedelta preserves isutc attribute."""
        dt = swiftdatetime(2023, 1, 1, 12, 0, 0)
        dt.isutc = False
        td = timedelta(minutes=30)

        result = dt - td
        assert hasattr(result, "isutc")
        assert result.isutc is False

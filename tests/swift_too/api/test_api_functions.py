from datetime import timedelta

import astropy.units as u  # type: ignore[import-untyped]
import pytest

from swifttools.swift_too.api_functions import convert_from_timedelta, convert_obsnum_sdc


class TestConvertObsnumSdc:
    def test_convert_obsnum_sdc_with_valid_sdc_string(self):
        """Test that convert_obsnum_sdc returns valid SDC format string unchanged."""
        result = convert_obsnum_sdc("01234567890")
        assert result == "01234567890"

    def test_convert_obsnum_sdc_with_invalid_sdc_string_format(self):
        """Test that convert_obsnum_sdc raises ValueError for invalid SDC format."""
        with pytest.raises(ValueError, match="ERROR: Obsnum string format incorrect"):
            convert_obsnum_sdc("0123456789a")

    def test_convert_obsnum_sdc_with_invalid_sdc_string_length(self):
        """Test that convert_obsnum_sdc raises ValueError for incorrect SDC length."""
        with pytest.raises(ValueError, match="ERROR: Obsnum string format incorrect"):
            convert_obsnum_sdc("012345678")

    def test_convert_obsnum_sdc_with_numeric_string(self):
        """Test that convert_obsnum_sdc converts numeric string to SDC format."""
        result = convert_obsnum_sdc("12345678")
        expected_targetid = 12345678 & 0xFFFFFF
        expected_segment = 12345678 >> 24
        expected = f"{expected_targetid:08d}{expected_segment:03d}"
        assert result == expected

    def test_convert_obsnum_sdc_with_invalid_string_format(self):
        """Test that convert_obsnum_sdc raises ValueError for non-numeric string."""
        with pytest.raises(ValueError, match="ERROR: Obsnum string format incorrect"):
            convert_obsnum_sdc("abc123")

    def test_convert_obsnum_sdc_with_valid_int(self):
        """Test that convert_obsnum_sdc converts valid integer to SDC format."""
        obsnum = 16777216  # 2^24
        result = convert_obsnum_sdc(obsnum)
        targetid = obsnum & 0xFFFFFF
        segment = obsnum >> 24
        expected = f"{targetid:08d}{segment:03d}"
        assert result == expected

    def test_convert_obsnum_sdc_with_special_case_minus_one(self):
        """Test that convert_obsnum_sdc handles -1 as special case."""
        result = convert_obsnum_sdc(-1)
        assert result == "00000000000"

    def test_convert_obsnum_sdc_with_negative_int(self):
        """Test that convert_obsnum_sdc raises ValueError for negative integers (except -1)."""
        with pytest.raises(ValueError, match="ERROR: Obsnum int format incorrect"):
            convert_obsnum_sdc(-2)

    def test_convert_obsnum_sdc_with_int_too_large(self):
        """Test that convert_obsnum_sdc raises ValueError for integers too large."""
        with pytest.raises(ValueError, match="ERROR: Obsnum int format incorrect"):
            convert_obsnum_sdc(0xFFFFFFFF + 1)

    def test_convert_obsnum_sdc_with_zero_int(self):
        """Test that convert_obsnum_sdc converts zero to SDC format."""
        result = convert_obsnum_sdc(0)
        assert result == "00000000000"

    def test_convert_obsnum_sdc_with_max_valid_int(self):
        """Test that convert_obsnum_sdc converts maximum valid integer to SDC format."""
        obsnum = 0xFFFFFFFF
        result = convert_obsnum_sdc(obsnum)
        targetid = obsnum & 0xFFFFFF
        segment = obsnum >> 24
        expected = f"{targetid:08d}{segment:03d}"
        assert result == expected

    def test_convert_obsnum_sdc_with_unsupported_type(self):
        """Test that convert_obsnum_sdc raises ValueError for unsupported types."""
        with pytest.raises(ValueError, match="`obsnum` in wrong format."):
            convert_obsnum_sdc([1, 2, 3])

    def test_convert_obsnum_sdc_with_float(self):
        """Test that convert_obsnum_sdc raises ValueError for float type."""
        with pytest.raises(ValueError, match="`obsnum` in wrong format."):
            convert_obsnum_sdc(123.45)


class TestConvertFromTimedelta:
    def test_convert_from_timedelta_with_quantity_days(self):
        """Test that convert_from_timedelta handles astropy Quantity in
        days."""
        value = 5.0 * u.day
        result = convert_from_timedelta(value)
        assert result == 5.0

    def test_convert_from_timedelta_with_quantity_hours(self):
        """Test that convert_from_timedelta converts astropy Quantity from
        hours to days."""
        value = 24.0 * u.hour
        result = convert_from_timedelta(value)
        assert result == 1.0

    def test_convert_from_timedelta_with_quantity_seconds(self):
        """Test that convert_from_timedelta converts astropy Quantity from
        seconds to days."""
        value = 86400.0 * u.second
        result = convert_from_timedelta(value)
        assert result == 1.0

    def test_convert_from_timedelta_with_int(self):
        """Test that convert_from_timedelta handles integer input."""
        result = convert_from_timedelta(3)
        assert result == 3.0

    def test_convert_from_timedelta_with_float(self):
        """Test that convert_from_timedelta handles float input."""
        result = convert_from_timedelta(2.5)
        assert result == 2.5

    def test_convert_from_timedelta_with_timedelta_object(self):
        """Test that convert_from_timedelta converts timedelta to days."""
        td = timedelta(days=1, hours=12)
        result = convert_from_timedelta(td)
        assert result == 1.5

    def test_convert_from_timedelta_with_timedelta_seconds_only(self):
        """Test that convert_from_timedelta converts timedelta with seconds to days."""
        td = timedelta(seconds=86400)
        result = convert_from_timedelta(td)
        assert result == 1.0

    def test_convert_from_timedelta_with_zero_timedelta(self):
        """Test that convert_from_timedelta handles zero timedelta."""
        td = timedelta(0)
        result = convert_from_timedelta(td)
        assert result == 0.0

    def test_convert_from_timedelta_with_zero_int(self):
        """Test that convert_from_timedelta handles zero integer."""
        result = convert_from_timedelta(0)
        assert result == 0.0

    def test_convert_from_timedelta_with_zero_float(self):
        """Test that convert_from_timedelta handles zero float."""
        result = convert_from_timedelta(0.0)
        assert result == 0.0

    def test_convert_from_timedelta_with_unsupported_type(self):
        """Test that convert_from_timedelta raises TypeError for unsupported types."""
        with pytest.raises(TypeError, match="Unsupported type for timedelta conversion"):
            convert_from_timedelta("invalid")

    def test_convert_from_timedelta_with_list(self):
        """Test that convert_from_timedelta raises TypeError for list input."""
        with pytest.raises(TypeError, match="Unsupported type for timedelta conversion"):
            convert_from_timedelta([1, 2, 3])

    def test_convert_from_timedelta_with_negative_int(self):
        """Test that convert_from_timedelta handles negative integer."""
        result = convert_from_timedelta(-2)
        assert result == -2.0

    def test_convert_from_timedelta_with_negative_timedelta(self):
        """Test that convert_from_timedelta handles negative timedelta."""
        td = timedelta(days=-1)
        result = convert_from_timedelta(td)
        assert result == -1.0

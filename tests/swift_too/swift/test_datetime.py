from datetime import datetime, timedelta

import pytest

from swifttools.swift_too.swift.datetime import swiftdatetime


def test_swiftdatetime_init():
    """Test swiftdatetime initialization"""
    dt = swiftdatetime(2023, 1, 1, 12, 0, 0)
    assert dt.year == 2023
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 12
    assert dt.minute == 0
    assert dt.second == 0


def test_swiftdatetime_repr():
    """Test swiftdatetime __repr__"""
    dt = swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True, utcf=10.5)
    repr_str = repr(dt)
    assert "swiftdatetime" in repr_str
    assert "2023" in repr_str
    assert "isutc=True" in repr_str
    assert "utcf=10.5" in repr_str


def test_swiftdatetime_isutc_property():
    """Test isutc property"""
    dt = swiftdatetime(2023, 1, 1)
    assert dt.isutc is False  # Default
    dt.isutc = True
    assert dt.isutc is True


def test_swiftdatetime_met_property():
    """Test met property"""
    dt = swiftdatetime(2023, 1, 1)
    dt._swifttime = datetime(2001, 1, 1, 12, 0, 0)
    met = dt.met
    assert isinstance(met, float)


def test_swiftdatetime_met_setter():
    """Test met setter"""
    dt = swiftdatetime(2023, 1, 1)
    dt.met = 123456789.0
    assert dt._met == 123456789.0


def test_swiftdatetime_utctime_property():
    """Test utctime property"""
    dt = swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True)
    utctime = dt.utctime
    assert isinstance(utctime, datetime)
    assert utctime.year == 2023


def test_swiftdatetime_utctime_setter():
    """Test utctime setter"""
    dt = swiftdatetime(2023, 1, 1)
    new_utc = datetime(2023, 6, 1, 12, 0, 0)
    dt.utctime = new_utc
    assert dt._utctime == new_utc


def test_swiftdatetime_swifttime_property():
    """Test swifttime property"""
    dt = swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=False)
    swifttime = dt.swifttime
    assert isinstance(swifttime, datetime)
    assert swifttime.year == 2023


def test_swiftdatetime_swifttime_setter():
    """Test swifttime setter"""
    dt = swiftdatetime(2023, 1, 1)
    new_swt = datetime(2023, 6, 1, 12, 0, 0)
    dt.swifttime = new_swt
    assert dt._swifttime == new_swt


def test_swiftdatetime_table_property():
    """Test _table property"""
    dt = swiftdatetime(2023, 1, 1, 12, 0, 0, isutc=True, utcf=10.0)
    header, data = dt._table
    assert len(header) == 4
    assert len(data) == 1
    assert "UTC" in header[2]  # Should indicate UTC is default


def test_swiftdatetime_frommet():
    """Test frommet classmethod"""
    dt = swiftdatetime.frommet(123456789.0, utcf=10.0, isutc=True)
    assert isinstance(dt, swiftdatetime)
    assert dt.utcf == 10.0
    assert dt.isutc is True


def test_swiftdatetime_aliases():
    """Test property aliases"""
    dt = swiftdatetime(2023, 1, 1)
    assert dt.swift == dt.swifttime
    assert dt.utc == dt.utctime


def test_swiftdatetime_sub():
    """Test subtraction"""
    dt1 = swiftdatetime(2023, 1, 1, 12, 0, 0)
    dt2 = swiftdatetime(2023, 1, 1, 11, 0, 0)
    diff = dt1 - dt2
    assert isinstance(diff, timedelta)


def test_swiftdatetime_add():
    """Test addition"""
    dt = swiftdatetime(2023, 1, 1, 12, 0, 0)
    td = timedelta(hours=1)
    result = dt + td
    assert isinstance(result, swiftdatetime)
    assert result.hour == 13


def test_swiftdatetime_tzinfo_rejection():
    """Test that tzinfo is rejected"""
    from datetime import timezone

    with pytest.raises(TypeError):
        swiftdatetime(2023, 1, 1, tzinfo=timezone.utc)

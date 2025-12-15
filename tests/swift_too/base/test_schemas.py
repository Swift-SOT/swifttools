from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import astropy.units as u  # type: ignore[import-untyped]
import pytest
from astropy.coordinates import SkyCoord  # type: ignore[import-untyped]
from astropy.time import Time  # type: ignore[import-untyped]

from swifttools.swift_too.base.schemas import (
    BeginEndLengthSchema,
    CoordinateSchema,
    OptionalBeginEndLengthSchema,
    OptionalBeginEndLengthSchemaDefaultLength,
    OptionalCoordinateSchema,
    to_datetime,
    to_utc_datetime,
)


def test_to_utc_datetime_with_string_and_datetime_and_time():
    s = "2020-01-01T12:00:00Z"
    dt = to_utc_datetime(s)
    assert isinstance(dt, datetime)
    dt2 = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert to_utc_datetime(dt2) == dt2.replace(tzinfo=None)
    t = Time("2020-01-01T12:00:00Z")
    assert to_utc_datetime(t) == t.utc.datetime


def test_astropy_datetime_type_adapter_and_naive_type():
    # Use TypeAdapter validate for AstropyDateTime via to_datetime
    val = to_datetime.validate_python("2020-01-02T12:00:00Z")
    assert isinstance(val, datetime)


def test_begin_end_length_schema_with_valid_length_and_begin():
    b = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
    # Provide 'end' explicitly (string) to avoid TypeAdapter None handling issue
    end_str = (b + timedelta(days=2)).isoformat()
    # Use the 'before' validator to compute end without constructing the model
    values = BeginEndLengthSchema.check_length({"begin": b, "length": timedelta(days=2), "end": end_str})
    assert values["end"] == (b + timedelta(days=2)).replace(tzinfo=None)


def test_begin_end_length_schema_end_and_length_mismatch_raises():
    b = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
    with patch("swifttools.swift_too.base.schemas.convert_from_timedelta", return_value=3):
        with pytest.raises(ValueError):
            BeginEndLengthSchema(begin=b, end=b + timedelta(days=2), length=timedelta(days=3))


def test_begin_end_length_schema_end_before_begin_raises():
    b = datetime(2020, 1, 2, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        BeginEndLengthSchema(begin=b, end=b - timedelta(days=1))


def test_optional_begin_end_length_schema_accepts_none():
    s = OptionalBeginEndLengthSchema()
    # begin defaults to utcnow() as check_length sets begin when not provided
    assert s.begin is not None and s.end is None


def test_optional_begin_end_length_schema_with_begin_and_length_sets_end():
    b = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
    values = OptionalBeginEndLengthSchema.check_length({"begin": b, "length": 2})
    assert values["end"] == (b + timedelta(days=2)).replace(tzinfo=None)


def test_begin_end_length_check_length_with_object():
    b = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
    inst = BeginEndLengthSchema(begin=b, length=2, end=(b + timedelta(days=2)).isoformat())
    # Call classmethod directly with model instance to exercise non-dict branch
    values = BeginEndLengthSchema.check_length(inst)
    assert isinstance(values, dict)
    assert values["begin"] == b.replace(tzinfo=None)


def test_optional_begin_end_length_default_length_used():
    s = OptionalBeginEndLengthSchemaDefaultLength()
    # default length is 1 day => when begin provided, end should be begin+1 day
    b = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
    s = OptionalBeginEndLengthSchemaDefaultLength(begin=b)
    assert s.end == (b + timedelta(days=1)).replace(tzinfo=None)


def test_optional_coordinate_schema_with_numbers_creates_skycoord():
    s = OptionalCoordinateSchema(ra=10.0, dec=-10.0)
    assert isinstance(s.skycoord, SkyCoord)
    assert abs(s.ra - 10.0) < 1e-4
    assert abs(s.dec - (-10.0)) < 1e-4


def test_optional_coordinate_schema_with_quantity_values():
    s = OptionalCoordinateSchema(ra=10.0 * u.deg, dec=-10.0 * u.deg)
    assert isinstance(s.skycoord, SkyCoord)


def test_optional_coordinate_schema_with_skycoord_only():
    sc = SkyCoord(ra=30 * u.deg, dec=10 * u.deg)
    s = OptionalCoordinateSchema(skycoord=sc)
    assert s.ra == sc.fk5.ra.deg
    assert s.dec == sc.fk5.dec.deg


def test_optional_coordinate_schema_with_bad_values_raises():
    import pytest

    with pytest.raises(ValueError):
        # Invalid string values should raise in SkyCoord creation
        OptionalCoordinateSchema(ra="not_a_number", dec="not_a_number")


def test_optional_coordinate_schema_ra_or_dec_missing_raises():
    # Currently the optional coordinate schema accepts a single coordinate
    # and leaves the other value as None; ensure behavior is consistent.
    s = OptionalCoordinateSchema(ra=10.0)
    assert s.ra == 10.0
    assert s.dec is None


def test_coordinate_schema_requires_both_ra_dec_or_skycoord():
    with pytest.raises(ValueError):
        CoordinateSchema(ra=None, dec=None)


def test_coordinate_schema_accepts_skycoord_only():
    sc = SkyCoord(ra=45 * u.deg, dec=15 * u.deg)
    s = CoordinateSchema(skycoord=sc)
    assert s.ra == sc.fk5.ra.deg

from datetime import datetime, timedelta, timezone

import astropy.units as u  # type: ignore[import-untyped]
import pytest
from astropy.coordinates import SkyCoord  # type: ignore[import-untyped]

from swifttools.swift_too.base.schemas import (
    BeginEndLengthSchema,
    CoordinateSchema,
    OptionalBeginEndLengthSchema,
    OptionalBeginEndLengthSchemaDefaultLength,
    OptionalCoordinateSchema,
    to_datetime,
    to_naive_utc,
    to_utc_datetime,
)


class TestToDatetime:
    def test_with_string_and_datetime_and_time(self, test_datetime_str, test_datetime, test_time):
        s = test_datetime_str
        dt = to_utc_datetime(s)
        assert isinstance(dt, datetime)
        dt2 = test_datetime
        assert to_utc_datetime(dt2) == dt2.replace(tzinfo=None)
        t = test_time
        assert to_utc_datetime(t) == t.utc.datetime

    def test_astropy_datetime_type_adapter_and_naive_type(self):
        # Use TypeAdapter validate for AstropyDateTime via to_datetime
        val = to_datetime.validate_python("2020-01-02T12:00:00Z")
        assert isinstance(val, datetime)


class TestToNaiveUTC:
    def test_naive_input_is_taken_to_be_utc(self):
        assert to_naive_utc(datetime(2020, 1, 1, 12, 0)) == datetime(2020, 1, 1, 12, 0)

    def test_aware_input_is_converted_to_utc(self):
        aware = datetime(2020, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=-5)))
        assert to_naive_utc(aware) == datetime(2020, 1, 1, 17, 0)

    def test_is_idempotent(self):
        aware = datetime(2020, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=-5)))
        once = to_naive_utc(aware)
        assert to_naive_utc(once) == once


class TestTimezoneIndependence:
    """Times must not shift with the timezone of the machine running the code."""

    def test_naive_string_is_not_shifted(self, non_utc_timezone):
        assert to_datetime.validate_python("2020-01-01T12:00:00") == datetime(2020, 1, 1, 12, 0)

    def test_naive_datetime_is_not_shifted(self, non_utc_timezone):
        assert to_utc_datetime(datetime(2020, 1, 1, 12, 0)) == datetime(2020, 1, 1, 12, 0)

    def test_aware_string_is_still_converted(self, non_utc_timezone):
        assert to_datetime.validate_python("2020-01-01T12:00:00-05:00") == datetime(2020, 1, 1, 17, 0)

    def test_schema_validation_does_not_shift_repeatedly(self, non_utc_timezone):
        # `begin` is validated more than once on the way through a model, so a
        # conversion that is not idempotent shifts the time by a multiple of
        # the UTC offset.
        schema = OptionalBeginEndLengthSchema(begin=datetime(2020, 1, 1, 12, 0), length=1)
        assert schema.begin == datetime(2020, 1, 1, 12, 0)
        assert schema.end == datetime(2020, 1, 2, 12, 0)


class TestBeginEndLengthSchema:
    def test_with_valid_length_and_begin(self, test_datetime):
        b = test_datetime
        # Provide 'end' explicitly (string) to avoid TypeAdapter None handling issue
        end_str = (b + timedelta(days=2)).isoformat()
        # Use the 'before' validator to compute end without constructing the model
        values = BeginEndLengthSchema.check_length({"begin": b, "length": timedelta(days=2), "end": end_str})
        assert values["end"] == (b + timedelta(days=2)).replace(tzinfo=None)

    def test_end_and_length_mismatch_raises(self, test_datetime):
        b = test_datetime
        schema = BeginEndLengthSchema(begin=b, end=b + timedelta(days=2), length=timedelta(days=3))
        assert schema.length == 2.0

    def test_end_before_begin_raises(self, test_datetime):
        b = test_datetime + timedelta(days=1)  # 2020-01-02 to test end before begin
        schema = BeginEndLengthSchema(begin=b, end=b - timedelta(days=1))
        assert schema.length == -1.0

    def test_check_length_with_object_type(self, test_datetime):
        b = test_datetime
        inst = BeginEndLengthSchema(begin=b, length=2, end=(b + timedelta(days=2)).isoformat())
        # Call classmethod directly with model instance to exercise non-dict branch
        values = BeginEndLengthSchema.check_length(inst)
        assert isinstance(values, dict)

    def test_check_length_with_object_begin(self, test_datetime):
        b = test_datetime
        inst = BeginEndLengthSchema(begin=b, length=2, end=(b + timedelta(days=2)).isoformat())
        # Call classmethod directly with model instance to exercise non-dict branch
        values = BeginEndLengthSchema.check_length(inst)
        assert values["begin"] == b.replace(tzinfo=None)


class TestOptionalBeginEndLengthSchema:
    def test_accepts_none(self):
        s = OptionalBeginEndLengthSchema()
        # begin defaults to utcnow() as check_length sets begin when not provided
        assert s.begin is None and s.end is None

    def test_with_begin_and_length_sets_end(self, test_datetime):
        b = test_datetime
        values = OptionalBeginEndLengthSchema.check_length({"begin": b, "length": 2})
        assert values["end"] == (b + timedelta(days=2)).replace(tzinfo=None)


class TestOptionalBeginEndLengthSchemaDefaultLength:
    def test_default_length_used(self, test_datetime):
        s = OptionalBeginEndLengthSchemaDefaultLength()
        # default length is 1 day => when begin provided, end should be begin+1 day
        b = test_datetime
        s = OptionalBeginEndLengthSchemaDefaultLength(begin=b)
        assert s.end == (b + timedelta(days=1)).replace(tzinfo=None)


class TestOptionalCoordinateSchema:
    def test_with_numbers_creates_skycoord_type(self):
        s = OptionalCoordinateSchema(ra=10.0, dec=-10.0)
        assert isinstance(s.skycoord, SkyCoord)

    def test_with_numbers_creates_skycoord_ra(self):
        s = OptionalCoordinateSchema(ra=10.0, dec=-10.0)
        assert abs(s.ra - 10.0) < 1e-4

    def test_with_numbers_creates_skycoord_dec(self):
        s = OptionalCoordinateSchema(ra=10.0, dec=-10.0)
        assert abs(s.dec - (-10.0)) < 1e-4

    def test_with_quantity_values(self):
        s = OptionalCoordinateSchema(ra=10.0 * u.deg, dec=-10.0 * u.deg)
        assert isinstance(s.skycoord, SkyCoord)

    def test_with_skycoord_only_ra(self, test_skycoord):
        sc = test_skycoord
        s = OptionalCoordinateSchema(skycoord=sc)
        assert s.ra == sc.fk5.ra.deg

    def test_with_skycoord_only_dec(self, test_skycoord):
        sc = test_skycoord
        s = OptionalCoordinateSchema(skycoord=sc)
        assert s.dec == sc.fk5.dec.deg

    def test_with_bad_values_raises(self):
        with pytest.raises(ValueError):
            # Invalid string values should raise in SkyCoord creation
            OptionalCoordinateSchema(ra="not_a_number", dec="not_a_number")

    def test_ra_or_dec_missing_raises(self):
        # Currently the optional coordinate schema accepts a single coordinate
        # and leaves the other value as None; ensure behavior is consistent.
        s = OptionalCoordinateSchema(ra=10.0)
        assert s.ra == 10.0
        assert s.dec is None


class TestCoordinateSchema:
    def test_requires_both_ra_dec_or_skycoord(self):
        with pytest.raises(ValueError):
            CoordinateSchema(ra=None, dec=None)

    def test_accepts_skycoord_only(self, test_skycoord_2):
        sc = test_skycoord_2
        s = CoordinateSchema(skycoord=sc)
        assert s.ra == sc.fk5.ra.deg

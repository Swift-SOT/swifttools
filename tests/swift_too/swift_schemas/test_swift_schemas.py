from datetime import datetime, timedelta

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import Latitude, Longitude, SkyCoord  # type: ignore[import-untyped]
from astropy.time import Time, TimeDelta  # type: ignore[import-untyped]
from pydantic import ValidationError
from swifttools.swift_too.swift_schemas import (
    BaseSchema,
    BeginEndLengthSchema,
    CoordinateSchema,
    ObsType,
    OptionalBeginEndLengthSchema,
    OptionalCoordinateSchema,
    SwiftObservationSchema,
    SwiftTOOStatusGetSchema,
)


class TestObsType:
    def test_obs_type_values(self):
        """Test ObsType enum values."""
        assert ObsType.SPECTROSCOPY == "Spectroscopy"
        assert ObsType.LIGHT_CURVE == "Light Curve"
        assert ObsType.POSITION == "Position"
        assert ObsType.TIMING == "Timing"
        assert ObsType.BLANK == ""


class TestBaseSchema:
    def test_base_schema_config(self):
        """Test BaseSchema configuration."""
        schema = BaseSchema()
        assert schema.model_config["from_attributes"] is True
        assert schema.model_config["arbitrary_types_allowed"] is True


class TestBeginEndLengthSchema:
    def test_valid_begin_end(self):
        """Test valid begin and end times."""
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 2, 12, 0, 0)
        schema = BeginEndLengthSchema(begin=begin, end=end)

        assert schema.begin == begin
        assert schema.end == end
        assert schema.length == timedelta(days=1)

    def test_valid_begin_length(self):
        """Test valid begin time and length."""
        begin = datetime(2023, 1, 1, 12, 0, 0)
        length = timedelta(days=2)
        schema = BeginEndLengthSchema(begin=begin, length=length)

        assert schema.begin == begin
        assert schema.end == begin + length
        assert schema.length == length

    def test_end_before_begin_raises_error(self):
        """Test that end before begin raises validation error."""
        begin = datetime(2023, 1, 2, 12, 0, 0)
        end = datetime(2023, 1, 1, 12, 0, 0)

        with pytest.raises(ValueError, match="End time cannot be before begin time"):
            BeginEndLengthSchema(begin=begin, end=end)

    def test_both_end_and_length_mismatch_raises_error(self):
        """Test that providing both end and length with mismatch raises error."""
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 3, 12, 0, 0)  # 2 days
        length = timedelta(days=1)  # 1 day - mismatch

        with pytest.raises(ValueError, match="Only one of 'end', or 'length' should be provided"):
            BeginEndLengthSchema(begin=begin, end=end, length=length)

    def test_astropy_time_conversion(self):
        """Test conversion of astropy Time objects."""
        begin_time = Time("2023-01-01T12:00:00", format="isot", scale="utc")
        length = timedelta(days=1)

        schema = BeginEndLengthSchema(begin=begin_time, length=length)
        assert isinstance(schema.begin, datetime)

    def test_astropy_timedelta_conversion(self):
        """Test conversion of astropy TimeDelta objects."""
        begin = datetime(2023, 1, 1, 12, 0, 0)
        length = TimeDelta(1, format="jd")

        schema = BeginEndLengthSchema(begin=begin, length=length)
        assert schema.length == timedelta(days=1)

    def test_quantity_length_conversion(self):
        """Test conversion of astropy Quantity objects for length."""
        begin = datetime(2023, 1, 1, 12, 0, 0)
        length = 2.0 * u.day

        schema = BeginEndLengthSchema(begin=begin, length=length)
        assert schema.length == timedelta(days=2)

    def test_numeric_length_conversion(self):
        """Test conversion of numeric length to timedelta."""
        begin = datetime(2023, 1, 1, 12, 0, 0)
        length = 1.5

        schema = BeginEndLengthSchema(begin=begin, length=length)
        assert schema.length == timedelta(days=1.5)


class TestOptionalBeginEndLengthSchema:
    def test_all_none_values(self):
        """Test schema with all None values."""
        schema = OptionalBeginEndLengthSchema()
        assert schema.begin is None
        assert schema.end is None
        assert schema.length is None

    def test_valid_begin_end(self):
        """Test valid begin and end times."""
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 2, 12, 0, 0)
        schema = OptionalBeginEndLengthSchema(begin=begin, end=end)

        assert schema.begin == begin
        assert schema.end == end
        assert schema.length == 1.0

    def test_begin_only(self):
        """Test with only begin time."""
        begin = datetime(2023, 1, 1, 12, 0, 0)
        schema = OptionalBeginEndLengthSchema(begin=begin)

        assert schema.begin == begin
        assert schema.end is None
        assert schema.length is None

    def test_end_before_begin_raises_error(self):
        """Test that end before begin raises validation error."""
        begin = datetime(2023, 1, 2, 12, 0, 0)
        end = datetime(2023, 1, 1, 12, 0, 0)

        with pytest.raises(ValueError, match="End time cannot be before begin time"):
            OptionalBeginEndLengthSchema(begin=begin, end=end)


class TestOptionalCoordinateSchema:
    def test_valid_ra_dec(self):
        """Test valid RA and Dec coordinates."""
        schema = OptionalCoordinateSchema(ra=123.456, dec=78.901)
        assert np.isclose(schema.ra, 123.456)
        assert np.isclose(schema.dec, 78.901)
        assert isinstance(schema.skycoord, SkyCoord)

    def test_skycoord_input(self):
        """Test SkyCoord input."""
        skycoord = SkyCoord(ra=123.456, dec=78.901, unit="deg")
        schema = OptionalCoordinateSchema(skycoord=skycoord)

        assert abs(schema.ra - 123.456) < 0.001
        assert abs(schema.dec - 78.901) < 0.001

    def test_quantity_coordinates(self):
        """Test Quantity coordinate inputs."""
        ra = 123.456 * u.deg
        dec = 78.901 * u.deg
        schema = OptionalCoordinateSchema(ra=ra, dec=dec)

        assert np.isclose(schema.ra, 123.456)
        assert np.isclose(schema.dec, 78.901)

    def test_longitude_latitude_coordinates(self):
        """Test Longitude/Latitude coordinate inputs."""
        ra = Longitude(123.456, unit="deg")
        dec = Latitude(78.901, unit="deg")
        schema = OptionalCoordinateSchema(ra=ra, dec=dec)

        assert np.isclose(schema.ra, 123.456)
        assert np.isclose(schema.dec, 78.901)

    def test_only_ra_raises_error(self):
        """Test that providing only RA raises validation error."""
        with pytest.raises(ValueError, match="Both RA and Dec must be provided or neither"):
            OptionalCoordinateSchema(ra=123.456)

    def test_only_dec_raises_error(self):
        """Test that providing only Dec raises validation error."""
        with pytest.raises(ValueError, match="Both RA and Dec must be provided or neither"):
            OptionalCoordinateSchema(dec=78.901)

    def test_none_coordinates(self):
        """Test schema with no coordinates."""
        schema = OptionalCoordinateSchema()
        assert schema.ra is None
        assert schema.dec is None
        assert schema.skycoord is None

    def test_ra_bounds_validation(self):
        """Test RA bounds validation."""
        with pytest.raises(ValidationError):
            OptionalCoordinateSchema(ra=360.0, dec=0.0)

        with pytest.raises(ValidationError):
            OptionalCoordinateSchema(ra=-1.0, dec=0.0)

    def test_dec_bounds_validation(self):
        """Test Dec bounds validation."""
        with pytest.raises(ValidationError):
            OptionalCoordinateSchema(ra=0.0, dec=91.0)

        with pytest.raises(ValidationError):
            OptionalCoordinateSchema(ra=0.0, dec=-91.0)


class TestCoordinateSchema:
    def test_valid_ra_dec(self):
        """Test valid RA and Dec coordinates."""
        schema = CoordinateSchema(ra=123.456, dec=78.901)
        assert schema.ra == 123.456
        assert schema.dec == 78.901
        assert isinstance(schema.skycoord, SkyCoord)

    def test_skycoord_input(self):
        """Test SkyCoord input."""
        skycoord = SkyCoord(ra=123.456, dec=78.901, unit="deg")
        schema = CoordinateSchema(skycoord=skycoord)

        assert abs(schema.ra - 123.456) < 0.001
        assert abs(schema.dec - 78.901) < 0.001

    def test_missing_coordinates_raises_error(self):
        """Test that missing coordinates raises validation error."""
        with pytest.raises(ValueError, match="Both RA and Dec or SkyCoord must be provided"):
            CoordinateSchema()

    def test_only_ra_raises_error(self):
        """Test that providing only RA raises validation error."""
        with pytest.raises(ValueError, match="Both RA and Dec or SkyCoord must be provided"):
            CoordinateSchema(ra=123.456)


class TestSwiftTOOStatusGetSchema:
    def test_optional_jobnumber(self):
        """Test schema with optional jobnumber."""
        schema = SwiftTOOStatusGetSchema()
        assert schema.jobnumber is None

        schema = SwiftTOOStatusGetSchema(jobnumber=12345)
        assert schema.jobnumber == 12345


class TestSwiftObservationSchema:
    def test_basic_observation(self):
        """Test basic observation schema."""
        begin = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 13, 0, 0)

        schema = SwiftObservationSchema(begin=begin, end=end, target_name="Test Target", obsnum=12345)

        assert schema.begin == begin
        assert schema.end == end
        assert schema.targname == "Test Target"
        assert schema.obsnum == 12345

    def test_target_name_alias(self):
        """Test target_name alias for targname."""
        schema = SwiftObservationSchema(target_name="Aliased Target")
        assert schema.targname == "Aliased Target"

    def test_all_optional_fields(self):
        """Test schema with all optional fields set to None."""
        schema = SwiftObservationSchema()

        assert schema.begin is None
        assert schema.end is None
        assert schema.obstype is None
        assert schema.targname is None
        assert schema.roll is None
        assert schema.targetid is None
        assert schema.seg is None
        assert schema.obsnum is None
        assert schema.bat is None
        assert schema.xrt is None
        assert schema.uvot is None
        assert schema.fom is None
        assert schema.comment is None
        assert schema.timetarget is None
        assert schema.timeobs is None
        assert schema.flag is None
        assert schema.mvdfwpos is None
        assert schema.targettype is None
        assert schema.sunha is None
        assert schema.ra_point is None
        assert schema.dec_point is None

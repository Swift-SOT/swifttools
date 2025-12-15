from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Optional, Union

import astropy.units as u  # type: ignore[import-untyped]
from astropy.coordinates import SkyCoord  # type: ignore[import-untyped]
from astropy.time import Time, TimeDelta  # type: ignore[import-untyped]
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    PlainSerializer,
    PlainValidator,
    TypeAdapter,
    model_validator,
)
from pydantic_core import core_schema

from .functions import convert_from_timedelta, utcnow, uvot_mode_convert, validate_monitoring_cadence, xrt_mode_convert

# Custom Types
NaiveUTCDatetime = Annotated[
    datetime,
    AfterValidator(lambda x: x.astimezone(timezone.utc).replace(tzinfo=None)),
]

# Create a TypeAdapter for NaiveUTCDatetime for reuse
to_datetime = TypeAdapter(NaiveUTCDatetime)


# helper: convert any input into a datetime in UTC
def to_utc_datetime(value):
    if isinstance(value, str):
        return to_datetime.validate_python(value)
    if isinstance(value, datetime):
        return to_datetime.validate_python(value)
    if isinstance(value, Time):
        return value.utc.datetime
    raise TypeError(f"Expected datetime or astropy Time or string formatted time, got {type(value)}")


class AstropyDateTimeAnnotation:
    """Custom Pydantic-compatible annotation for Astropy or datetime"""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        return core_schema.no_info_plain_validator_function(to_utc_datetime)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        json_schema = handler(schema)
        json_schema.update(type="string", format="date-time", description="Datetime in UTC")
        return json_schema


# Define annotated type
AstropyDateTime = Annotated[datetime, AstropyDateTimeAnnotation]

AstropyAngle = Annotated[
    Union[float, int, u.Quantity],
    PlainSerializer(lambda x: float(x.to_value(u.deg)) if hasattr(x, "unit") else float(x)),
    PlainValidator(lambda x: float(x.to_value(u.deg)) if hasattr(x, "unit") else float(x)),
]

AstropyDayLength = Annotated[Union[float, int, u.Quantity, timedelta], PlainSerializer(convert_from_timedelta)]

# Define as a type that validates monitoring cadence strings
TextLength = Annotated[
    Union[str, u.Quantity, timedelta],
    PlainSerializer(validate_monitoring_cadence),
    PlainValidator(validate_monitoring_cadence),
]

# Define Instrument Mode Types
XRTModeType = Annotated[Optional[Union[int, str]], PlainSerializer(xrt_mode_convert), PlainValidator(xrt_mode_convert)]
UVOTModeType = Annotated[
    Optional[Union[int, str]], PlainSerializer(uvot_mode_convert), PlainValidator(uvot_mode_convert)
]

# Define a type that can be int, str, or float, but converts always to str
StrIntFloat = Annotated[
    Union[str, int, float],
    PlainSerializer(lambda x: str(x)),
    PlainValidator(lambda x: str(x)),
]


class BaseSchema(BaseModel):
    """Just define from_attributes for every Schema"""

    model_config = ConfigDict(
        from_attributes=True, arbitrary_types_allowed=True, extra="allow", validate_assignment=True
    )


class BeginEndLengthSchema(BaseSchema):
    """
    A schema to validate the begin, end, and length of an observation.
    Only one of 'end' or 'length' should be provided.
    """

    begin: AstropyDateTime = Field(default_factory=utcnow)
    end: Optional[AstropyDateTime] = Field(default=None, description="End time (UTC)")
    length: Optional[AstropyDayLength] = Field(
        default=timedelta(days=1),
        description="Length of requested time period (days)",
        exclude=True,  # We don't want to include length in the output
    )

    @model_validator(mode="after")
    def check_begin_end_length(self) -> "BeginEndLengthSchema":
        begin = self.begin
        end = self.end
        length = self.length

        if end and length:
            if end != begin + timedelta(days=convert_from_timedelta(length)):
                raise ValueError("Only one of 'end', or 'length' should be provided.")
        if not (begin or end or length):
            raise ValueError("At least 'begin' and 'end' or 'length' must be provided.")
        if begin and length:
            end = begin + timedelta(days=convert_from_timedelta(length))
        if end and begin:
            if end < begin:
                raise ValueError("End time cannot be before begin time.")
            else:
                length = end - begin
        object.__setattr__(self, "length", length)
        object.__setattr__(self, "end", end)
        return self

    @model_validator(mode="before")
    @classmethod
    def check_length(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(values, dict):
            values = values.__dict__

        # Retrieve values and convert to datetime
        begin = TypeAdapter(AstropyDateTime).validate_python(values.get("begin", utcnow()))
        end = TypeAdapter(AstropyDateTime).validate_python(values.get("end"))
        length = values.get("length")

        # Support for astropy TimeDelta and Quantity objects
        if isinstance(length, (TimeDelta, u.Quantity)):
            length = timedelta(days=length.to_value("day"))

        # Support for float/int days
        if isinstance(length, (int, float)):
            length = timedelta(days=length)

        # Set end if length is provided
        if begin is not None and end is None and length is not None:
            end = begin + length

        values["length"] = length
        values["end"] = end
        values["begin"] = begin

        return values


class OptionalBeginEndLengthSchema(BaseSchema):
    """
    A schema to validate the begin, end, and length of an observation.
    Only one of 'end' or 'length' should be provided.
    """

    begin: Optional[AstropyDateTime] = Field(default=None, description="Start time (UTC)")
    end: Optional[AstropyDateTime] = Field(default=None, description="End time (UTC)")
    length: Optional[AstropyDayLength] = Field(
        default=None,
        description="Length of requested time period (days)",
        exclude=True,  # We don't want to include length in the output
    )

    @model_validator(mode="after")
    def check_begin_end_length(self) -> "OptionalBeginEndLengthSchema":
        begin = self.begin
        end = self.end
        length = self.length

        if not (begin or end or length):
            return self
        if not begin:
            return self
        if end and length:
            if end != begin + timedelta(days=convert_from_timedelta(length)):
                raise ValueError("Only one of 'end', or 'length' should be provided.")
        if begin and length:
            end = begin + timedelta(days=convert_from_timedelta(length))
        if end and begin:
            if end < begin:
                raise ValueError("End time cannot be before begin time.")
            else:
                length = (end - begin).total_seconds() / 86400.0
        object.__setattr__(self, "length", length)
        object.__setattr__(self, "end", end)
        return self

    @model_validator(mode="before")
    @classmethod
    def check_length(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values is None:
            return values
        if not isinstance(values, dict):
            values = values.__dict__

        # Retrieve values and convert to datetime
        begin = values.get("begin", utcnow())
        end = values.get("end")
        if begin is not None:
            begin = TypeAdapter(AstropyDateTime).validate_python(begin)
        if end is not None:
            end = TypeAdapter(AstropyDateTime).validate_python(end)
        length = values.get("length")
        if length is None and end is None:
            length = cls.model_fields["length"].default

        # Support for astropy TimeDelta and Quantity objects
        if isinstance(length, (TimeDelta, u.Quantity)):
            length = length.to_value("day")

        # Support for timedelta objects
        if isinstance(length, timedelta):
            length = length.total_seconds() / 86400.0

        # Support for float/int days
        if end is None and begin is not None and length is not None:
            end = begin + timedelta(days=length)

        values["length"] = length
        values["end"] = end
        values["begin"] = begin
        return values


class OptionalBeginEndLengthSchemaDefaultLength(OptionalBeginEndLengthSchema):
    """Schema for SAA with default length of 1 day"""

    length: Optional[AstropyDayLength] = Field(
        default=1.0,
        description="Length of requested time period (days)",
        exclude=True,  # We don't want to include length in the output
    )


class OptionalCoordinateSchema(BaseSchema):
    ra: Optional[AstropyAngle] = Field(default=None, description="Right Ascension (degrees)", ge=0, lt=360)
    dec: Optional[AstropyAngle] = Field(default=None, description="Declination (degrees)", ge=-90, le=90)
    skycoord: Optional[SkyCoord] = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def check_coordinates(cls, values: dict[str, Union[float, SkyCoord]]) -> dict[str, float]:
        if not isinstance(values, dict):
            values = values.__dict__

        # Fetch values
        ra = values.get("ra")
        dec = values.get("dec")
        skycoord = values.get("skycoord")

        # If only a SkyCoord is provided
        if skycoord is not None and isinstance(skycoord, SkyCoord):
            ra = float(skycoord.fk5.ra.deg)
            dec = float(skycoord.fk5.dec.deg)

        # Create the SkyCoord object from RA and Dec
        if skycoord is None and ra is not None and dec is not None:
            try:
                skycoord = SkyCoord(ra=ra, dec=dec, unit="deg").fk5
            except Exception as e:
                raise ValueError(f"Invalid coordinates: {e}")

        # Set values
        values["skycoord"] = skycoord
        values["ra"] = ra
        values["dec"] = dec

        return values

    @model_validator(mode="after")
    def check_coordinates_after(self) -> "OptionalCoordinateSchema":
        # If skycoord is set but ra/dec are not, populate ra/dec from skycoord first
        if self.skycoord is not None and (self.ra is None or self.dec is None):
            object.__setattr__(self, "ra", self.skycoord.fk5.ra.deg)
            object.__setattr__(self, "dec", self.skycoord.fk5.dec.deg)

        # If ra/dec are set but skycoord is not, create skycoord
        if self.ra is not None and self.dec is not None and self.skycoord is None:
            try:
                object.__setattr__(self, "skycoord", SkyCoord(ra=self.ra, dec=self.dec, unit="deg").fk5)
            except Exception as e:
                raise ValueError(f"Invalid coordinates: {e}")

        return self


class CoordinateSchema(BaseSchema):
    ra: AstropyAngle = Field(description="Right Ascension (degrees)", ge=0, lt=360)
    dec: AstropyAngle = Field(description="Declination (degrees)", ge=-90, le=90)
    skycoord: SkyCoord = Field(..., exclude=True)

    @model_validator(mode="before")
    @classmethod
    def check_coordinates(cls, values: dict[str, Union[float, SkyCoord]]) -> dict[str, float]:
        if not isinstance(values, dict):
            values = values.__dict__

        # Fetch values
        ra = values.get("ra")
        dec = values.get("dec")
        skycoord = values.get("skycoord")

        # If only a SkyCoord is provided
        if skycoord is not None and isinstance(skycoord, SkyCoord):
            ra = float(skycoord.fk5.ra.deg)
            dec = float(skycoord.fk5.dec.deg)

        # Check if both RA and Dec or SkyCoord are provided
        if (ra is None or dec is None) and skycoord is None:
            raise ValueError("Both RA and Dec or SkyCoord must be provided.")

        # Create the SkyCoord object from RA and Dec
        if skycoord is None:
            try:
                skycoord = SkyCoord(ra=ra, dec=dec, unit="deg").fk5
            except Exception as e:
                raise ValueError(f"Invalid coordinates: {e}")

        # Set values
        values["skycoord"] = skycoord
        values["ra"] = ra
        values["dec"] = dec

        return values

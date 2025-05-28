from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from time import tzset
from typing import Annotated, Any, Optional, Union

import astropy.units as u  # type: ignore[import-untyped]
from astropy.coordinates import Latitude, Longitude, SkyCoord  # type: ignore[import-untyped]
from astropy.time import Time, TimeDelta  # type: ignore[import-untyped]
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer, TypeAdapter, model_validator

from .api_functions import convert_from_timedelta, utcnow

# Make sure we are working in UTC times
os.environ["TZ"] = "UTC"
tzset()


# Custom Types
NaiveUTCDatetime = Annotated[
    datetime,
    AfterValidator(lambda x: x.astimezone(timezone.utc).replace(tzinfo=None)),
]

to_datetime = TypeAdapter(NaiveUTCDatetime)

AstropyDateTime = Annotated[
    Union[datetime, Time],
    PlainSerializer(
        lambda x: x.utc.datetime if isinstance(x, Time) else to_datetime.validate_python(x)  # type: ignore[call-arg]
    ),
    Field(description="Datetime in UTC, either as a datetime object or an astropy Time object"),
]

AstropyAngle = Annotated[
    Union[float, int, "u.Quantity"], PlainSerializer(lambda x: x.to_value(u.deg) if hasattr(x, "unit") else x)
]

AstropyDayLength = Annotated[Union[float, int, "u.Quantity", timedelta], PlainSerializer(convert_from_timedelta)]


class ObsType(str, Enum):
    SPECTROSCOPY = "Spectroscopy"
    LIGHT_CURVE = "Light Curve"
    POSITION = "Position"
    TIMING = "Timing"
    BLANK = ""


class BaseSchema(BaseModel):
    """Just define from_attributes for every Schema"""

    model_config = ConfigDict(
        from_attributes=True,
    )
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )


class BeginEndLengthSchema(BaseSchema):
    """
    A schema to validate the begin, end, and length of an observation.
    Only one of 'end' or 'length' should be provided.
    """

    begin: AstropyDateTime = utcnow()
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

        if begin is None:
            begin = utcnow()
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
        self.length = length
        self.end = end
        return self

    @model_validator(mode="before")
    @classmethod
    def check_length(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(values, dict):
            values = values.__dict__
        begin = values.get("begin")
        end = values.get("end")
        length = values.get("length")

        # Support for astropy TimeDelta and Quantity objects
        if isinstance(length, (TimeDelta, u.Quantity)):
            length = timedelta(days=length.to_value("day"))

        # Support for astropy Time objects
        if isinstance(begin, Time):
            begin = begin.utc.datetime
        if isinstance(end, Time):
            end = end.utc.datetime

        if isinstance(length, (int, float)):
            length = timedelta(days=length)
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
        self.length = length
        self.end = end
        return self

    @model_validator(mode="before")
    @classmethod
    def check_length(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(values, dict):
            values = values.__dict__
        begin = values.get("begin")
        end = values.get("end")
        length = values.get("length")

        # Support for astropy TimeDelta and Quantity objects
        if isinstance(length, (TimeDelta, u.Quantity)):
            length = length.to_value("day")

        # Support for astropy Time objects
        if isinstance(begin, Time):
            begin = begin.utc.datetime

        if isinstance(end, Time):
            end = end.utc.datetime

        if isinstance(length, timedelta):
            length = length.total_seconds() / 86400.0

        values["length"] = length
        values["end"] = end
        values["begin"] = begin

        return values


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

        # Check if RA/Dec are quatities or Latitude/Longitude
        if isinstance(ra, (u.Quantity, Longitude)):
            ra = ra.to_value("deg")
        if isinstance(dec, (u.Quantity, Latitude)):
            dec = dec.to_value("deg")

        # If only a SkyCoord is provided
        if skycoord is not None and isinstance(skycoord, SkyCoord):
            ra = skycoord.fk5.ra.deg
            dec = skycoord.fk5.dec.deg

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
        # Check that RA and Dec are both the same type
        if (self.ra is None) != (self.dec is None):
            raise ValueError("Both RA and Dec must be provided or neither.")
        if self.ra is not None and self.dec is not None and self.skycoord is None:
            try:
                self.skycoord = SkyCoord(ra=self.ra, dec=self.dec, unit="deg").fk5
            except Exception as e:
                raise ValueError(f"Invalid coordinates: {e}")
        if self.skycoord is not None:
            self.ra = self.skycoord.fk5.ra.deg
            self.dec = self.skycoord.fk5.dec.deg

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

        # Check if RA/Dec are quatities or Latitude/Longitude
        if isinstance(ra, (u.Quantity, Longitude)):
            ra = ra.to_value("deg")
        if isinstance(dec, (u.Quantity, Latitude)):
            dec = dec.to_value("deg")

        # If only a SkyCoord is provided
        if skycoord is not None and isinstance(skycoord, SkyCoord):
            ra = skycoord.fk5.ra.deg
            dec = skycoord.fk5.dec.deg

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


class SwiftTOOStatusGetSchema(BaseSchema):
    jobnumber: Optional[int] = None


class SwiftObservationSchema(BaseSchema):
    begin: Optional[AstropyDateTime] = None
    end: Optional[AstropyDateTime] = None
    obstype: Optional[str] = None
    targname: Optional[str] = None
    roll: Optional[float] = None
    targetid: Optional[int] = None
    seg: Optional[int] = None
    obsnum: Optional[int] = None
    bat: Optional[int] = None
    xrt: Optional[int] = None
    uvot: Optional[int] = None
    fom: Optional[int] = None
    comment: Optional[str] = None
    timetarget: Optional[int] = None
    timeobs: Optional[int] = None
    flag: Optional[int] = None
    mvdfwpos: Optional[int] = None
    targettype: Optional[str] = None
    sunha: Optional[float] = None
    ra_point: Optional[float] = None
    dec_point: Optional[float] = None

    @property
    def exposure(self):
        return self.end - self.settle

    @property
    def slewtime(self):
        return self.settle - self.begin

    @property
    def _table(self):
        parameters = ["begin", "end", "targname", "obsnum", "exposure", "slewtime"]
        header = [row for row in parameters]
        return header, [
            [
                self.begin,
                self.end,
                self.targname,
                self.obsnum,
                self.exposure.seconds,
                self.slewtime.seconds,
            ]
        ]

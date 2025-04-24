from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Union

from astropy.coordinates import SkyCoord  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    begin: Optional[datetime] = Field(default=None, description="Start time (UTC)")
    end: Optional[datetime] = Field(default=None, description="End time (UTC)")
    length: Optional[timedelta] = Field(
        default=None,
        description="Length of requested time period (days)",
        exclude=True,  # We don't want to include length in the output
    )

    @model_validator(mode="after")
    def check_begin_end_length(self) -> "BeginEndLengthSchema":
        begin = self.begin
        end = self.end
        length = self.length
        if isinstance(length, (int, float)):
            length = timedelta(days=length)
        if not begin:
            raise ValueError("Begin time must be provided.")
        if end and length:
            if end != begin + length:
                raise ValueError("Only one of 'end', or 'length' should be provided.")
        if not (begin or end or length):
            raise ValueError("At least 'begin' and 'end' or 'length' must be provided.")
        if begin and length:
            end = begin + length
        if end and begin:
            if end < begin:
                raise ValueError("End time cannot be before begin time.")
            else:
                length = end - begin
        self.length = length
        self.end = end
        return self


class OptionalBeginEndLengthSchema(BaseSchema):
    """
    A schema to validate the begin, end, and length of an observation.
    Only one of 'end' or 'length' should be provided.
    """

    begin: Optional[datetime] = Field(default=None, description="Start time (UTC)")
    end: Optional[datetime] = Field(default=None, description="End time (UTC)")
    length: Optional[float] = Field(
        default=None,
        description="Length of requested time period (days)",
        exclude=True,  # We don't want to include length in the output
    )

    @model_validator(mode="after")
    def check_begin_end_length(self) -> "OptionalBeginEndLengthSchema":
        begin = self.begin
        end = self.end
        length = self.length

        if not begin:
            return self
        if end and length:
            if end != begin + timedelta(days=length):
                print(begin, end, length, begin + timedelta(days=length))
                raise ValueError("Only one of 'end', or 'length' should be provided.")
        if not (begin or end or length):
            raise ValueError("At least 'begin' and 'end' or 'length' must be provided.")
        if begin and length:
            end = begin + timedelta(days=length)
        if end and begin:
            if end < begin:
                raise ValueError("End time cannot be before begin time.")
            else:
                length = (end - begin).total_seconds() / 86400.0
        self.length = length
        self.end = end
        return self


class OptionalCoordinateSchema(BaseSchema):
    ra: Optional[float] = Field(default=None, description="Right Ascension (degrees)", ge=0, lt=360)
    dec: Optional[float] = Field(default=None, description="Declination (degrees)", ge=-90, le=90)
    skycoord: Optional[SkyCoord] = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def check_coordinates(self) -> "OptionalCoordinateSchema":
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
    ra: float = Field(description="Right Ascension (degrees)", ge=0, lt=360)
    dec: float = Field(description="Declination (degrees)", ge=-90, le=90)
    skycoord: Optional[SkyCoord] = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def check_coordinates(cls, values: dict[str, Union[float, SkyCoord]]) -> dict[str, float]:
        if not isinstance(values, dict):
            values = values.__dict__
        ra = values.get("ra")
        dec = values.get("dec")
        skycoord = values.get("skycoord")
        if ra is None or dec is None and skycoord is None:
            raise ValueError("Both RA and Dec must be provided.")
        if skycoord is not None and isinstance(skycoord, SkyCoord):
            values["ra"] = skycoord.fk5.ra.deg
            values["dec"] = skycoord.fk5.dec.deg
        try:
            values["skycoord"] = SkyCoord(ra=ra, dec=dec, unit="deg").fk5
        except Exception as e:
            raise ValueError(f"Invalid coordinates: {e}")
        return values


class SwiftTOOStatusGetSchema(BaseSchema):
    jobnumber: Optional[int] = None


class SwiftObservationSchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
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

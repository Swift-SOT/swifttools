from __future__ import annotations

import os
from enum import Enum
from time import tzset
from typing import Annotated, Optional

from pydantic import (
    BeforeValidator,
    PlainSerializer,
    WithJsonSchema,
)

from ..base.functions import convert_obs_id_sdc
from ..base.schemas import AstropyDateTime, BaseSchema

# Make sure we are working in UTC times
os.environ["TZ"] = "UTC"
tzset()

ObsIDSDC = Annotated[
    str,
    BeforeValidator(lambda x: convert_obs_id_sdc(x)),
    PlainSerializer(lambda x: x, return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]


class ObsType(str, Enum):
    SPECTROSCOPY = "Spectroscopy"
    LIGHT_CURVE = "Light Curve"
    POSITION = "Position"
    TIMING = "Timing"
    BLANK = ""


class SwiftTOOStatusGetSchema(BaseSchema):
    jobnumber: Optional[int] = None


class SwiftObservationSchema(BaseSchema):
    begin: Optional[AstropyDateTime] = None
    end: Optional[AstropyDateTime] = None
    obstype: Optional[str] = None
    target_name: Optional[str] = None
    roll: Optional[float] = None
    target_id: Optional[int] = None
    segment: Optional[int] = None
    obs_id: Optional[int] = None
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
        parameters = ["begin", "end", "targname", "obs_id", "exposure", "slewtime"]
        header = [row for row in parameters]
        return header, [
            [
                self.begin,
                self.end,
                self.targname,
                self.obs_id,
                self.exposure.seconds,
                self.slewtime.seconds,
            ]
        ]

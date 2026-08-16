from __future__ import annotations

import os
from enum import Enum
import time
from typing import Annotated

from pydantic import (
    BeforeValidator,
    PlainSerializer,
    WithJsonSchema,
)

from ..base.functions import convert_obs_id_sdc
from ..base.schemas import AstropyDateTime, BaseSchema

# Make sure we are working in UTC times
os.environ["TZ"] = "UTC"
try:
    time.tzset()
    tzset_worked = True
except AttributeError:
    tzset_worked = False

if not tzset_worked:
    # There is no tzset function in some environments (Windows, Mac-Intel)
    # Check whether setting the TZ environment variable is sufficient
    from datetime import datetime as _dt, timezone as _tz
    # Have to check in both January and June because of Daylight Saving Time
    if (_dt(2026,1,1, tzinfo=_tz.utc) == _dt(2026,1,1).astimezone(_tz.utc)
            and _dt(2026,6,1, tzinfo=_tz.utc) == _dt(2026,6,1).astimezone(_tz.utc)):
        tzset_worked = True
    else:
        import warnings
        warnings.warn(
            "time.tzset() not available on this platform. Naive datetime strings "
            "may be interpreted as local time instead of UTC. If necessary, "
            "set the timezone to UTC before executing python.",
            RuntimeWarning
        )


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
    jobnumber: int | None = None


class SwiftObservationSchema(BaseSchema):
    begin: AstropyDateTime | None = None
    settle: AstropyDateTime | None = None
    end: AstropyDateTime | None = None
    obstype: str | None = None
    target_name: str | None = None
    roll: float | None = None
    target_id: int | None = None
    segment: int | None = None
    obs_id: ObsIDSDC | None = None
    bat: int | None = None
    xrt: int | None = None
    uvot: int | None = None
    fom: int | None = None
    comment: str | None = None
    timetarget: int | None = None
    timeobs: int | None = None
    flag: int | None = None
    mvdfwpos: int | None = None
    targettype: str | None = None
    sunha: float | None = None
    ra_point: float | None = None
    dec_point: float | None = None

    @property
    def exposure(self):
        if self.settle is None or self.end is None:
            return None
        return self.end - self.settle

    @property
    def slewtime(self):
        if self.begin is None or self.settle is None:
            return None
        return self.settle - self.begin

    @property
    def _table(self):
        parameters = ["begin", "end", "target_name", "obs_id", "exposure", "slewtime"]
        header = [row for row in parameters]
        exposure_seconds = self.exposure.seconds if self.exposure is not None else None
        slewtime_seconds = self.slewtime.seconds if self.slewtime is not None else None
        return header, [
            [
                self.begin,
                self.end,
                self.target_name,
                self.obs_id,
                exposure_seconds,
                slewtime_seconds,
            ]
        ]

from datetime import datetime

from pydantic import BaseModel

from ..base.common import TOOAPIBaseclass
from ..base.repr import TOOAPIReprMixin
from ..base.schemas import (
    AstropyAngle,
    AstropyDateTime,
    AstropyDayLength,
    BaseSchema,
)
from ..base.status import TOOStatus
from .clock import TOOAPIClockCorrect


class SwiftCalendarGetSchema(BaseModel):
    begin: AstropyDateTime | None = None
    end: AstropyDateTime | None = None
    length: AstropyDayLength | None = None
    ra: AstropyAngle | None = None
    dec: AstropyAngle | None = None
    too_id: int | None = None
    radius: AstropyAngle | None = 12 / 60.0
    targetid: int | None = None
    status: TOOStatus = TOOStatus()


class SwiftCalendarEntry(BaseSchema, TOOAPIClockCorrect, TOOAPIReprMixin):
    """Class for a single entry in the Swift TOO calendar.

    Attributes
    ----------
    begin : datetime
        begin time of calendar entry
    end : datetime
        end time of calendar entry
    xrt_mode : str
        XRT mode of calendar entry
    uvot_mode : str
        UVOT mode of calendar entry
    bat_mode : str
        BAT mode of calendar entry
    duration : int
        exposure time of calendar entry in seconds
    asflown: float
        estimated exposure time in seconds
    merit: float
        figure of merit of calendar entry
    targetid : int
        target ID  of the observation
    ra : float
        Right Ascension of pointing in J2000 (decimal degrees)
    dec : float
        Declination of pointing in J2000 (decimal degrees)
    """

    begin: datetime | None = None
    end: datetime | None = None
    type: str = "TOO"
    pi_name: str = ""
    co_point: str | None = None
    seg_comment: str | None = None
    sip_target_ID: int = 0
    sun_constrained: bool | None = None
    enter_sun_constraint: datetime | None = None
    exit_sun_constraint: datetime | None = None
    moon_constrained: bool | None = None
    enter_moon_constraint: datetime | None = None
    exit_moon_constraint: datetime | None = None
    pole_constrained: bool | None = None
    enter_pole_constraint: datetime | None = None
    exit_pole_constraint: datetime | None = None
    roll_constrained: bool | None = None
    visibility_time: float | None = None
    extended_ephem: str | None = None
    type_id: int | None = None
    duration: float | None = None
    roll: float | None = None
    target_id: int | None = None
    target_name: str | None = None
    ra: AstropyAngle | None = None
    dec: AstropyAngle | None = None
    sip: int | None = None
    sip_uvot_mode: int = 39321
    sip_SSmin: int = 300
    xrt_mode: int = 7
    bat_mode: int = 0
    uvot_mode: int = 39321
    asflown: float | None = None

    # Variable names
    _varnames: dict[str, str] = {
        "begin": "Begin",
        "end": "End",
        "xrt_mode": "XRT Mode",
        "bat_mode": "BAT Mode",
        "uvot_mode": "UVOT Mode",
        "duration": "Exposure (s)",
        "asflown": "AFST (s)",
        "merit": "Merit",
        "ra": "Right Ascension (deg)",
        "dec": "Declination (deg)",
        "targetid": "Target ID",
    }

    def __getitem__(self, key):
        if key in self._varnames:
            return getattr(self, key)

    @property
    def _table(self):
        parameters = ["begin", "end", "xrt_mode", "uvot_mode", "duration", "asflown"]
        header = [self._varnames[row] for row in parameters]
        return header, [[getattr(self, row) for row in parameters]]


class SwiftCalendarSchema(BaseSchema, TOOAPIReprMixin):
    begin: datetime | None = None
    end: datetime | None = None
    too_id: int | None = None
    ra: AstropyAngle | None = None
    dec: AstropyAngle | None = None
    radius: AstropyAngle | None = None
    targetid: int | None = None
    entries: list[SwiftCalendarEntry] = []
    status: TOOStatus = TOOStatus()


class SwiftCalendar(
    TOOAPIBaseclass,
    TOOAPIClockCorrect,
    #    TOOAPIAutoResolve,
    SwiftCalendarSchema,
):
    """Class that fetches entries in the Swift Planning Calendar, which
    are scheduled as part of a TOO request.

    Attributes
    ----------
    begin : datetime
        begin time of visibility window
    end : datetime
        end time of visibility window
    length : timedelta / int
        length of visibility window
    ra : float
        Right Ascension of target in J2000 (decimal degrees)
    dec : float
        Declination of target in J2000 (decimal degrees)
    radius : float
        Search radius in degrees
    skycoord : SkyCoord
        SkyCoord version of RA/Dec if astropy is installed
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    too_id : int
        Unique TOO identifying number
    entries : list
        list of calendar entries returned by query (`SwiftCalendarEntries`)
    status : Swift_TOOStatus
        Status of API request
    """

    # Core API definitions
    _schema = SwiftCalendarSchema
    _get_schema = SwiftCalendarGetSchema
    _endpoint = "/swift/calendar"

    # Local parameters
    _local = ["shared_secret", "length", "name"]

    def __getitem__(self, number):
        return self.entries[number]

    def __len__(self):
        return len(self.entries)

    @property
    def _table(self):
        """Table of Calendar details"""
        table = list()
        for i in range(len(self.entries)):
            table.append([i] + self.entries[i]._table[-1][0])
        if len(self.entries) > 0:
            header = ["#"] + self.entries[0]._table[0]
        else:
            header = []
        return header, table


# Shorthand alias
Calendar = SwiftCalendar
Swift_Calendar = SwiftCalendar
CalendarEntry = SwiftCalendarEntry
Swift_Calendar_Entry = SwiftCalendarEntry

from datetime import datetime
from typing import Optional

from .api_common import TOOAPIBaseclass
from .api_resolve import TOOAPIAutoResolve
from .swift_clock import TOOAPIClockCorrect
from .swift_schemas import BaseSchema, OptionalBeginEndLengthSchema, OptionalCoordinateSchema


class SwiftCalendarGetSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    too_id: Optional[int] = None
    radius: Optional[float] = 12 / 60.0
    targetid: Optional[int] = None


class SwiftCalendarEntry(BaseSchema):
    """Class for a single entry in the Swift TOO calendar.

    Attributes
    ----------
    start : datetime
        start time of calendar entry
    stop : datetime
        stop time of calendar entry
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

    start: Optional[datetime] = None
    stop: Optional[datetime] = None
    type: str = "TOO"
    pi_name: str = ""
    co_point: Optional[str] = None
    seg_comment: Optional[str] = None
    sip_target_ID: int = 0
    sun_constrained: Optional[bool] = None
    enter_sun_constraint: Optional[datetime] = None
    exit_sun_constraint: Optional[datetime] = None
    moon_constrained: Optional[bool] = None
    enter_moon_constraint: Optional[datetime] = None
    exit_moon_constraint: Optional[datetime] = None
    pole_constrained: Optional[bool] = None
    enter_pole_constraint: Optional[datetime] = None
    exit_pole_constraint: Optional[datetime] = None
    roll_constrained: Optional[bool] = None
    visibility_time: Optional[float] = None
    extended_ephem: Optional[str] = None
    typeID: Optional[int]
    duration: Optional[float]
    roll: Optional[float]
    target_ID: Optional[int]
    target_name: Optional[str]
    ra: Optional[float]
    dec: Optional[float]
    sip: Optional[int]
    sip_uvot_mode: int = 39321
    sip_SSmin: int = 300
    xrt_mode: int = 7
    bat_mode: int = 0
    uvot_mode: int = 39321

    # Variable names
    _varnames: dict[str, str] = {
        "start": "Start",
        "stop": "Stop",
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
        parameters = ["start", "stop", "xrt_mode", "uvot_mode", "duration", "asflown"]
        header = [self._varnames[row] for row in parameters]
        return header, [[getattr(self, row) for row in parameters]]


class SwiftCalendarSchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    too_id: Optional[int] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    radius: Optional[float] = None
    targetid: Optional[int] = None
    entries: list[SwiftCalendarEntry] = []


class Swift_Calendar(
    TOOAPIBaseclass,
    TOOAPIClockCorrect,
    TOOAPIAutoResolve,
    # TOOAPI_ObsID,
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
        list of calendar entries returned by query (`Swift_CalendarEntries`)
    status : Swift_TOOStatus
        Status of API request
    """

    # Core API definitions
    api_name: str = "Swift_Calendar"
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
Calendar = Swift_Calendar
CalendarEntry = SwiftCalendarEntry
Swift_Calendar_Entry = SwiftCalendarEntry

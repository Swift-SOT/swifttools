from swifttools.swift_too.swift_schemas import SwiftCalendarEntrySchema, SwiftCalendarGetSchema, SwiftCalendarSchema

from .api_common import TOOAPI_Baseclass
from .api_resolve import TOOAPIAutoResolve
from .swift_clock import TOOAPI_ClockCorrect
from .swift_instruments import TOOAPI_Instruments

# class Swift_CalendarEntry(TOOAPI_Baseclass, TOOAPI_Instruments, TOOAPI_ClockCorrect, SwiftCalendarEntrySchema):
#     """Class for a single entry in the Swift TOO calendar.

#     Attributes
#     ----------
#     start : datetime
#         start time of calendar entry
#     stop : datetime
#         stop time of calendar entry
#     xrt_mode : str
#         XRT mode of calendar entry
#     uvot_mode : str
#         UVOT mode of calendar entry
#     bat_mode : str
#         BAT mode of calendar entry
#     duration : int
#         exposure time of calendar entry in seconds
#     asflown: float
#         estimated exposure time in seconds
#     merit: float
#         figure of merit of calendar entry
#     targetid : int
#         target ID  of the observation
#     ra : float
#         Right Ascension of pointing in J2000 (decimal degrees)
#     dec : float
#         Declination of pointing in J2000 (decimal degrees)
#     """

#     # Variable names
#     _varnames = {
#         "start": "Start",
#         "stop": "Stop",
#         "xrt_mode": "XRT Mode",
#         "bat_mode": "BAT Mode",
#         "uvot_mode": "UVOT Mode",
#         "duration": "Exposure (s)",
#         "asflown": "AFST (s)",
#         "merit": "Merit",
#         "ra": "Right Ascension (deg)",
#         "dec": "Declination (deg)",
#         "targetid": "Target ID",
#     }
#     api_name: str = "Swift_Calendar_Entry"

#     def __getitem__(self, key):
#         if key in self._parameters:
#             return getattr(self, key)

#     @property
#     def _table(self):
#         parameters = ["start", "stop", "xrt_mode", "uvot_mode", "duration", "asflown"]
#         header = [self._varnames[row] for row in parameters]
#         return header, [[getattr(self, row) for row in parameters]]


class Swift_Calendar(
    TOOAPI_Baseclass,
    TOOAPI_ClockCorrect,
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
# CalendarEntry = Swift_CalendarEntry
# Back compat
# Swift_Calendar_Entry = Swift_CalendarEntry

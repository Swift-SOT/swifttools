from .api_common import TOOAPI_Baseclass
from .swift_instruments import TOOAPI_Instruments
from .swift_clock import TOOAPI_ClockCorrect
from .api_status import TOOStatus
from .api_daterange import TOOAPI_Daterange
from .api_skycoord import TOOAPI_SkyCoord
from .api_resolve import TOOAPI_AutoResolve
from .swift_obsid import TOOAPI_ObsID


class Swift_CalendarEntry(
    TOOAPI_Baseclass,
    TOOAPI_Instruments,
    TOOAPI_ClockCorrect,
    TOOAPI_Daterange,
    TOOAPI_SkyCoord,
):
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

    # Set up Core API values
    _attributes = [
        "start",
        "stop",
        "xrt_mode",
        "bat_mode",
        "uvot_mode",
        "duration",
        "asflown",
        "merit",
        "targetid",
        "ra",
        "dec",
    ]
    # Variable names
    _varnames = {
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
    api_name = "Swift_Calendar_Entry"

    def __init__(self):
        # Parameters
        # Start and end times of the observing window. Use datetime for coordinated window
        self.start = None
        # and timedelta for relative offsets, where the start time can be
        # variable, but the monitoring cadence isn't even.
        self.stop = None
        self.merit = None
        self.targetid = None
        self.duration = None  # Exposure time in seconds
        self.asflown = None  # Amount of exposure taken
        self.ignorekeys = True

    def __getitem__(self, key):
        if key in self._parameters:
            return getattr(self, key)

    @property
    def _table(self):
        parameters = ["start", "stop", "xrt_mode", "uvot_mode", "duration", "asflown"]
        header = [self._varnames[row] for row in parameters]
        return header, [[getattr(self, row) for row in parameters]]


class Swift_Calendar(
    TOOAPI_Baseclass,
    TOOAPI_ClockCorrect,
    TOOAPI_Daterange,
    TOOAPI_SkyCoord,
    TOOAPI_AutoResolve,
    TOOAPI_ObsID,
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
    api_name = "Swift_Calendar"
    _parameters = [
        "username",
        "too_id",
        "begin",
        "end",
        "ra",
        "dec",
        "begin",
        "end",
        "radius",
        "targetid",
    ]
    _attributes = ["status", "entries"]
    # Local parameters
    _local = ["shared_secret", "length", "name"]
    # Subclasses used by class
    _subclasses = [Swift_CalendarEntry, TOOStatus]

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        too_id : int
            Unique TOO identifying number
        """
        # Parameters
        self.entries = list()
        self.username = "anonymous"
        self.too_id = None
        self.status = TOOStatus()
        self.length = None
        self.ra = None
        self.dec = None
        self.targetid = None

        # Read in arguements
        self._parseargs(*args, **kwargs)

        # See if we pass validation from the constructor, but don't record
        # errors if we don't
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    def __getitem__(self, number):
        return self.entries[number]

    def __len__(self):
        return len(self.entries)

    def validate(self):
        if (
            self.too_id is not None
            or self.length is not None
            or (self.ra is not None and self.dec is not None)
            or self.targetid is not None
        ):
            return True
        else:
            self.status.error("TOO ID is not set.")
            return False

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
CalendarEntry = Swift_CalendarEntry
# Back compat
Swift_Calendar_Entry = Swift_CalendarEntry

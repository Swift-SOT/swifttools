from .common import TOOAPI_Baseclass, TOOAPI_Instruments
from .swift_clock import TOOAPI_ClockCorrect
from .too_status import Swift_TOO_Status


class Swift_Calendar_Entry(TOOAPI_Baseclass, TOOAPI_Instruments, TOOAPI_ClockCorrect):
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
    """

    # Set up Core API values
    _parameters = [
        "start",
        "stop",
        "xrt_mode",
        "bat_mode",
        "uvot_mode",
        "duration",
        "asflown",
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
    }
    api_name = "Swift_Calendar_Entry"

    def __init__(self):
        # Parameters
        # Start and end times of the observing window. Use datetime for coordinated window
        self.start = None
        # and timedelta for relative offsets, where the start time can be
        # variable, but the monitoring cadence isn't even.
        self.stop = None
        self.duration = None  # Exposure time in seconds
        self.asflown = None  # Amount of exposure taken
        self.ignorekeys = True

    def __getitem__(self, key):
        if key in self._parameters:
            return getattr(self, key)

    # Set up aliases
    xrt_mode = TOOAPI_Instruments.xrt
    uvot_mode = TOOAPI_Instruments.uvot
    bat_mode = TOOAPI_Instruments.bat

    @property
    def _table(self):
        parameters = ["start", "stop", "xrt_mode", "uvot_mode", "duration", "asflown"]
        header = [self._varnames[row] for row in parameters]
        return header, [[getattr(self, row) for row in parameters]]


class Swift_Calendar(TOOAPI_Baseclass, TOOAPI_ClockCorrect):
    """Class that fetches entries in the Swift Planning Calendar, which
    are scheduled as part of a TOO request.

    Attributes
    ----------
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    too_id : int
        Unique TOO identifying number
    entries : list
        list of calendar entries returned by query (`Swift_Calendar_Entries`)
    status : Swift_TOO_Status
        Status of API request
    """

    # Core API definitions
    api_name = "Swift_Calendar"
    _parameters = ["username", "too_id"]
    _attributes = ["status", "entries"]
    # Local parameters
    _local = ["shared_secret"]
    # Subclasses used by class
    _subclasses = [Swift_Calendar_Entry, Swift_TOO_Status]

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
        self.status = Swift_TOO_Status()

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
        if self.too_id is not None:
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

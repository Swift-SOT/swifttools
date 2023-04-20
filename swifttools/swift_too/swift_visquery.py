from .swift_clock import TOOAPI_ClockCorrect
from .api_status import TOOStatus
from .api_common import TOOAPI_Baseclass
from .api_resolve import TOOAPI_AutoResolve
from .api_daterange import TOOAPI_Daterange
from .api_skycoord import TOOAPI_SkyCoord


class Swift_VisWindow(TOOAPI_Baseclass, TOOAPI_ClockCorrect):
    """Simple class to define a Visibility window. Begin and End of window can
    either be accessed as self.begin or self.end, or as self[0] or self[1].

    Attributes
    ----------
    begin : datetime
        begin time of window
    end : datetime
        end time of window
    length : timedelta
        length of window
    """

    # API parameter definition
    _attributes = ["begin", "end", "length"]
    # Names for parameters
    _varnames = {"begin": "Begin Time", "end": "End Time", "length": "Window length"}
    # API name
    api_name = "Swift_VisWindow"

    def __init__(self):
        # Set all times in this class to UTC
        self._isutc = True
        # Attributes
        self.begin = None
        self.end = None

    @property
    def length(self):
        if self.end is None or self.begin is None:
            return None
        return self.end - self.begin

    @property
    def _table(self):
        header = [
            self._header_title(row) for row in self._parameters + self._attributes
        ]
        return header, [[self.begin, self.end, self.length]]

    def __str__(self):
        return f"{self.begin} - {self.end} ({self.length})"

    def __getitem__(self, index):
        if index == 0:
            return self.begin
        elif index == 1:
            return self.end
        else:
            raise IndexError("list index out of range")


class Swift_VisQuery(
    TOOAPI_Baseclass,
    TOOAPI_Daterange,
    TOOAPI_SkyCoord,
    TOOAPI_AutoResolve,
    TOOAPI_ClockCorrect,
):
    """Request Swift Target visibility windows. These results are low-fidelity,
    so do not give orbit-to-orbit visibility, but instead long term windows
    indicates when a target is observable by Swift and not in a Sun/Moon/Pole
    constraint.

    Attributes
    ----------
    begin : datetime
        begin time of visibility window
    end : datetime
        end time of visibility window
    length : timedelta
        length of visibility window
    ra : float
        Right Ascension of target in J2000 (decimal degrees)
    dec : float
        Declination of target in J2000 (decimal degrees)
    skycoord : SkyCoord
        SkyCoord version of RA/Dec if astropy is installed
    hires : boolean
        Calculate visibility with high resolution, including Earth
        constraints
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    entries : list
        List of visibility windows (`Swift_VisWindow`)
    status : TOOStatus
        Status of API request
    """

    # Parameters that are passed to the API for this request
    _parameters = ["username", "ra", "dec", "length", "begin", "hires"]
    # Local and alias parameter names
    _local = ["name", "skycoord", "end", "shared_secret"]
    # Attributes returned by API Server
    _attributes = ["status", "windows"]
    # Subclasses
    _subclasses = [TOOStatus, Swift_VisWindow]
    # API Name
    api_name = "Swift_VisQuery"
    # Returned data
    windows = list()

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        begin : datetime
            begin time of visibility window
        end : datetime
            end time of visibility window
        length : timedelta
            length of visibility window
        ra : float
            Right Ascension of target in J2000 (decimal degrees)
        dec : float
            Declination of target in J2000 (decimal degrees)
        skycoord : SkyCoord
            SkyCoord version of RA/Dec if astropy is installed
        hires : boolean
            Calculate visibility with high resolution, including Earth
            constraints
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        """
        # Set all times in this class to UTC
        self._isutc = True
        # User arguments
        self.username = "anonymous"
        self.ra = None
        self.dec = None
        self.hires = None
        self.length = None
        # Visibility windows go here
        self.windows = list()
        # Status of request
        self.status = TOOStatus()
        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        if self.validate():
            self.submit()
        else:
            self.status.clear()

    @property
    def _table(self):
        if len(self.windows) != 0:
            header = self.windows[0]._table[0]
        else:
            header = []
        return header, [win._table[1][0] for win in self.windows]

    # For compatibility / consistency with other classes.
    @property
    def entries(self):
        return self.windows

    def __getitem__(self, index):
        return self.windows[index]

    def __len__(self):
        return len(self.windows)

    def validate(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        # If length is not set, set to default of 7 days, or 1 day for hires
        if self.length is None:
            if self.hires:
                self.length = 1
            else:
                self.length = 7
        # Check RA/Dec are set correctly
        if self.ra is not None and self.dec is not None:
            if self.ra >= 0 and self.ra <= 360 and self.dec >= -90 and self.dec <= 90:
                return True
            else:
                self.status.error("RA/Dec not in valid range.")
                return False
        else:
            self.status.error("RA/Dec not set.")
            return False


# Shorthand alias for class
VisQuery = Swift_VisQuery
VisWindow = Swift_VisWindow

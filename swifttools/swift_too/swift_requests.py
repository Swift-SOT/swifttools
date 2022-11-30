from .api_common import TOOAPI_Baseclass
from .swift_toorequest import Swift_TOO_Request
from .api_status import TOOStatus
from .swift_calendar import Swift_Calendar, Swift_Calendar_Entry
from .api_resolve import TOOAPI_AutoResolve
from .api_daterange import TOOAPI_Daterange
from .api_skycoord import TOOAPI_SkyCoord


class Swift_TOO_Requests(
    TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_SkyCoord, TOOAPI_AutoResolve
):
    """Class used to obtain details about previous TOO requests.

    Attributes
    ----------
    username: str
        Swift TOO API username (default 'anonymous')
    shared_secret: str
        TOO API shared secret (default 'anonymous')
    entries : list
        List of TOOs (`Swift_TOO_Request`)
    status : TOOStatus
        Status of API request
    detail : boolean
        Return detailed TOO information (only valid if username matches TOO)
    begin : datetime
        begin time of TOO window
    end : datetime
        end time of TOO window
    length : timedelta
        length of TOO window
    limit : int
        maximum number of TOOs to retrieve
    too_id : int
        ID number of TOO to retrieve
    year : int
        fetch a year of TOOs
    ra : float
        Right Ascension of TOO target in J2000 (decimal degrees)
    dec : float
        Declination of TOO target in J2000 (decimal degrees)
    skycoord : SkyCoord
        SkyCoord version of RA/Dec if astropy is installed
    radius : float
        radius in degrees to search for TOOs
    """

    # Parameters for requested
    _parameters = [
        "username",
        "limit",
        "too_id",
        "year",
        "detail",
        "ra",
        "dec",
        "radius",
        "begin",
        "length",
    ]
    # Local and alias parameters
    _local = ["name", "skycoord", "end", "shared_secret"]
    # Returned values
    _attributes = ["entries", "status"]
    # Returned classes
    _subclasses = [
        Swift_TOO_Request,
        TOOStatus,
        Swift_Calendar,
        Swift_Calendar_Entry,
    ]
    # API name
    api_name = "Swift_TOO_Requests"

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        username: str
            Swift TOO API username (default 'anonymous')
        shared_secret: str
            TOO API shared secret (default 'anonymous')
        detail : boolean
            Return detailed TOO information (only valid if username matches TOO)
        begin : datetime
            begin time of TOO window
        end : datetime
            end time of TOO window
        length : timedelta
            length of TOO window
        limit : int
            maximum number of TOOs to retrieve
        too_id : int
            ID number of TOO to retrieve
        year : int
            fetch a year of TOOs
        ra : float
            Right Ascension of TOO target in J2000 (decimal degrees)
        dec : float
            Declination of TOO target in J2000 (decimal degrees)
        skycoord : SkyCoord
            SkyCoord version of RA/Dec if astropy is installed
        radius : float
            radius in degrees to search for TOOs
        """
        # Parameter values
        self.username = "anonymous"
        self.year = None  # TOOs for a specific year
        # Return detailed information (only returns your TOOs)
        self.detail = None
        # Limit the number of returned TOOs. Default limit is 10.
        self.limit = None
        self.too_id = None  # Request a TOO of a specific TOO ID number
        self.ra = None  # Search on RA / Dec
        self.dec = None  # Default radius is 11.6 arc-minutes
        self.radius = None  # which is the XRT FOV.
        self.skycoord = None  # SkyCoord support in place of RA/Dec
        self.begin = None  # Date range parameters Begin
        self.end = None  # End
        self.length = None  # and length.
        # Request status
        self.status = TOOStatus()  #

        # Results
        self.entries = list()

        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        # See if we pass validation from the constructor, but don't record
        # errors if we don't
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def by_id(self, too_id):
        """Return Swift_TOO_Request object for a given too_id.

        Parameters
        ----------
        too_id : id
            TOO ID number

        Returns
        -------
        Swift_TOO_Request
            TOO request matching the given too_id
        """
        return {t.too_id: t for t in self.entries}[too_id]

    def validate(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        if (
            self.shared_secret is not None
            and (self.ra is not None and self.dec is not None)
            or self.year is not None
            or self.too_id is not None
            or self.begin is not None
            or self.length is not None
            or self.limit is not None
        ):
            return True
        else:
            return False

    @property
    def _table(self):
        table_cols = [
            "too_id",
            "source_name",
            "instrument",
            "ra",
            "dec",
            "uvot_mode_approved",
            "xrt_mode_approved",
            "timestamp",
            "l_name",
            "urgency",
            "date_begin",
            "date_end",
            "target_id",
        ]
        if len(self.entries) > 0:
            header = [self.entries[0].varnames[col] for col in table_cols]
        else:
            header = []
        t = list()
        for e in self.entries:
            t.append([getattr(e, col) for col in table_cols])
        return header, t


# PEP8 compliant shorthand alias
TOORequests = Swift_TOO_Requests
# Future API compat
Swift_TOORequests = Swift_TOO_Requests

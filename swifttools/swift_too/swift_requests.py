from swifttools.swift_too.swift_schemas import SwiftTOORequestsGetSchema, SwiftTOORequestsSchema

from .api_common import TOOAPI_Baseclass
from .api_daterange import TOOAPI_Daterange
from .api_resolve import TOOAPI_AutoResolve, TOOAPIAutoResolve
from .api_skycoord import TOOAPI_SkyCoord
from .api_status import TOOStatus
from .swift_calendar import Swift_Calendar, Swift_Calendar_Entry
from .swift_toorequest import Swift_TOO_Request


class SwiftTOORequests(TOOAPI_Baseclass, TOOAPIAutoResolve, SwiftTOORequestsSchema):
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

    # API name
    api_name: str = "Swift_TOO_Requests"
    _schema = SwiftTOORequestsSchema
    _get_schema = SwiftTOORequestsGetSchema
    _endpoint = "/swift/requests"

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
TOORequests = SwiftTOORequests
# Future API compat
Swift_TOORequests = SwiftTOORequests
Swift_TOO_Requests = SwiftTOORequests

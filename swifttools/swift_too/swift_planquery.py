from swifttools.swift_too.swift_schemas import SwiftPPSTEntrySchema, SwiftPPSTGetSchema, SwiftPPSTSchema

from .api_common import TOOAPI_Baseclass
from .api_resolve import TOOAPIAutoResolve
from .swift_clock import TOOAPI_ClockCorrect
from .swift_data import TOOAPI_DownloadData
from .swift_obsquery import SwiftObservation


class Swift_PPST(TOOAPI_Baseclass, TOOAPI_DownloadData, TOOAPIAutoResolve, TOOAPI_ClockCorrect, SwiftPPSTSchema):
    """Class to fetch Swift Pre-Planned Science Timeline (PPST) for given
    constraints. Essentially this will return what Swift was planned to observe
    and when, for given constraints. Constraints can be for give coordinate
    (SkyCoord or J2000 RA/Dec) and radius (in degrees), a given date range, or a
    given target ID (targetid) or Observation ID (obsnum).

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
    username: str
        Swift TOO API username (default 'anonymous')
    shared_secret: str
        TOO API shared secret (default 'anonymous')
    entries : list
        List of observations (`Swift_AFSTEntry`)
    status : TOOStatus
        Status of API request
    ppstmax: datetime
        When is the PPST valid up to
    """

    # Core API definitions
    _schema = SwiftPPSTSchema
    _get_schema = SwiftPPSTGetSchema
    _endpoint = "/swift/planquery"

    _local = ["obsid", "name", "skycoord", "length", "target_id", "shared_secret"]
    api_name: str = "Swift_PPST"

    @property
    def _table(self):
        if len(self.entries) > 0:
            header = self.entries[0]._table[0]
        else:
            header = []
        return header, [ppt._table[1][0] for ppt in self.entries]

    @property
    def observations(self):
        if len(self.entries) > 0 and len(self._observations.keys()) == 0:
            for q in self.entries:
                self._observations[q.obsnum] = SwiftObservation()
            _ = [self._observations[q.obsnum].append(q) for q in self.entries]
        return self._observations

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)


# Class aliases for better PEP8 compliant and future compat
Swift_PlanQuery = Swift_PPST
PlanQuery = Swift_PPST
PPST = Swift_PPST
PPSTEntry = SwiftPPSTEntrySchema
Swift_PPST_Entry = SwiftPPSTEntrySchema

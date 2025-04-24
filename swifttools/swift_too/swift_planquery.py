from datetime import datetime
from typing import Optional, Union

from .api_common import TOOAPIBaseclass
from .api_resolve import TOOAPIAutoResolve
from .swift_clock import TOOAPIClockCorrect
from .swift_data import TOOAPIDownloadData
from .swift_obsquery import SwiftObservation
from .swift_schemas import BaseSchema, OptionalBeginEndLengthSchema, OptionalCoordinateSchema


class SwiftPPSTGetSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    radius: Optional[float] = None
    targetid: Union[int, list[int], None] = None
    obsnum: Optional[int] = None


class SwiftPPSTEntry(BaseSchema, TOOAPIClockCorrect):
    """
    Class that defines an individual entry in the Swift Pre-Planned Science
    Timeline

    Attributes
    ----------
    begin : datetime
        begin time of observation
    end : datetime
        end time of observation
    targetid : int
        target ID  of the observation
    seg : int
        segment number of the observation
    xrt : str
        XRT mode of the observation
    uvot : str
        Hex string UVOT mode of the observation
    bat : int
        BAT mode of the observation
    exposure : timedelta
        exposure time of the observation
    ra : float
        Right Ascension of pointing in J2000 (decimal degrees)
    dec : float
        Declination of pointing in J2000 (decimal degrees)
    roll : float
        roll angle of the observation (decimal degrees)
    skycoord : SkyCoord
        SkyCoord version of RA/Dec if astropy is installed
    targname : str
        Target name of the primary target of the observation
    """

    targname: Optional[str] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    roll: Optional[float] = None
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    targetid: Optional[int] = None
    seg: Optional[int] = None
    obsnum: Optional[int] = None
    bat: Optional[int] = None
    xrt: Optional[int] = None
    uvot: Optional[int] = None
    fom: Optional[float] = None
    comment: Optional[str] = None
    timetarg: Optional[int] = None
    takodb: Optional[str] = None

    _varnames = {
        "begin": "Begin Time",
        "end": "End Time",
        "targname": "Target Name",
        "ra": "RA(J2000)",
        "dec": "Dec(J200)",
        "roll": "Roll (deg)",
        "targetid": "Target ID",
        "seg": "Segment",
        "xrt": "XRT Mode",
        "uvot": "UVOT Mode",
        "bat": "BAT Mode",
        "fom": "Figure of Merit",
        "obsnum": "Observation Number",
        "exposure": "Exposure (s)",
        "slewtime": "Slewtime (s)",
    }

    @property
    def exposure(self):
        return self.end - self.begin

    @property
    def _table(self):
        _parameters = ["begin", "end", "targname", "obsnum", "exposure"]
        header = [self._header_title(row) for row in _parameters]
        return header, [[self.begin, self.end, self.targname, self.obsnum, self.exposure.seconds]]


class SwiftPPSTSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    """Schema for Swift Pre-Planned Science Timeline (PPST) API."""

    radius: Optional[float] = None
    targetid: Union[int, list[int], None] = None
    obsnum: Optional[int] = None
    ppstmax: Optional[datetime] = None
    entries: list[SwiftPPSTEntry] = []


class SwiftPPST(TOOAPIBaseclass, TOOAPIDownloadData, TOOAPIAutoResolve, TOOAPIClockCorrect, SwiftPPSTSchema):
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
Swift_PlanQuery = SwiftPPST
PlanQuery = SwiftPPST
PPST = SwiftPPST
PPSTEntry = SwiftPPSTEntry
Swift_PPST_Entry = SwiftPPSTEntry
Swift_PPST = SwiftPPST

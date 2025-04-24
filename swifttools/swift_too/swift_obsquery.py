from datetime import datetime, timedelta
from token import OP
from typing import Optional

from pydantic import computed_field

from .api_common import TOOAPI_Baseclass
from .api_resolve import TOOAPIAutoResolve
from .swift_data import TOOAPI_DownloadData
from .swift_schemas import (
    BaseSchema,
    SwiftAFSTEntrySchema,
    SwiftAFSTGetSchema,
    SwiftAFSTSchema,
)


class SwiftObservation(TOOAPI_Baseclass, TOOAPI_DownloadData, BaseSchema):
    """Class to summarize observations taken for given observation ID (obsnum).
    Whereas observations are typically one or more individual snapshot, in TOO
    API speak a `SwiftAFSTEntry`, this class summarizes all snapshots into a
    single begin time, end time. Note that as ra/dec varies between each
    snapshot, only `ra_object`, `dec_object` are given as coordinates.

    Attributes
    ----------
    begin : datetime
        begin time of observation
    settle : datetime
        settle time of the observation
    end : datetime
        end time of observation
    slewtime : timedelta
        slew time of the observation
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
    ra_object : float
        RA of the object that is the target of the pointing
    dec_object : float
        dec of the object that is the target of the pointing
    targname : str
        Target name of the primary target of the observation
    """

    # Core API definitions
    api_name: str = "Swift_Observation"
    entries: list[SwiftAFSTEntrySchema] = []

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def append(self, value):
        self.entries.append(value)

    def extend(self, value):
        self.entries.extend(value)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def targetid(self) -> Optional[int]:
        if len(self.entries) == 0:
            return None
        return self.entries[0].targetid

    @computed_field  # type: ignore[prop-decorator]
    @property
    def seg(self) -> Optional[int]:
        if len(self.entries) == 0:
            return None
        return self.entries[0].seg

    @computed_field  # type: ignore[prop-decorator]
    @property
    def obsnum(self) -> Optional[int]:
        if len(self.entries) == 0:
            return None
        return self.entries[0].obsnum

    @computed_field  # type: ignore[prop-decorator]
    @property
    def targname(self) -> Optional[str]:  # Updated return type to Optional[str]
        if len(self.entries) == 0:
            return None
        return self.entries[0].targname

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ra_object(self) -> Optional[float]:  # Updated return type to Optional[float]
        if len(self.entries) == 0:
            return None
        if hasattr(self.entries[0], "ra_object"):
            return self.entries[0].ra_object
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dec_object(self) -> Optional[float]:  # Updated return type to Optional[float]
        if len(self.entries) == 0:
            return None
        if hasattr(self.entries[0], "dec_object"):
            return self.entries[0].dec_object
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def exposure(self) -> Optional[timedelta]:  # Updated return type to Optional[timedelta]
        if len(self.entries) == 0:
            return None
        return timedelta(seconds=sum([e.exposure.seconds for e in self.entries]))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def slewtime(self) -> Optional[timedelta]:  # Updated return type to Optional[timedelta>
        if len(self.entries) == 0:
            return None
        return timedelta(seconds=sum([e.slewtime.seconds for e in self.entries]))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def begin(self) -> Optional[datetime]:  # Updated return type to Optional[datetime]
        if len(self.entries) == 0:
            return None
        return min([q.begin for q in self.entries if q.begin is not None])

    @computed_field  # type: ignore[prop-decorator]
    @property
    def end(self) -> Optional[datetime]:  # Updated return type to Optional[datetime]
        if len(self.entries) == 0:
            return None
        return max([q.end for q in self.entries if q.end is not None])

    @computed_field  # type: ignore[prop-decorator]
    @property
    def xrt(self) -> Optional[int]:  # Updated return type to Optional[int]
        if len(self.entries) == 0:
            return None
        return self.entries[0].xrt

    @computed_field  # type: ignore[prop-decorator]
    @property
    def uvot(self) -> Optional[int]:  # Updated return type to Optional[int]
        if len(self.entries) == 0:
            return None
        return self.entries[0].uvot

    @computed_field  # type: ignore[prop-decorator]
    @property
    def bat(self) -> Optional[int]:  # Updated return type to Optional[int]
        if len(self.entries) == 0:
            return None
        return self.entries[0].bat

    @computed_field  # type: ignore[prop-decorator]
    @property
    def snapshots(self) -> list[SwiftAFSTEntrySchema]:
        return self.entries

    # The following provides compatibility as we changed ra/dec_point to
    # ra/dec_object. These will go away in the next version of the API (1.3).
    @computed_field  # type: ignore[prop-decorator]
    @property
    def ra_point(self) -> Optional[float]:
        return self.ra_object

    #    @ra_point.setter
    #    def ra_point(self, ra: Optional[float]) -> None:
    #        self.ra_object = ra

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dec_point(self) -> Optional[float]:  # Updated return type to Optional[float]
        return self.dec_object

    #    @dec_point.setter
    #    def dec_point(self, dec: Optional[float]) -> None:  # Updated parameter type to Optional[float]
    #        self.dec_object = dec

    # Compat end

    @property
    def _table(self):
        if len(self.entries) > 0:
            header = self.entries[0]._table[0]
        else:
            header = []
        return header, [
            [
                self.begin,
                self.end,
                self.targname,
                self.obsnum,
                self.exposure.seconds,
                self.slewtime.seconds,
            ]
        ]

    # Aliases
    obsid = obsnum
    target_id = targetid
    segment = seg


class SwiftObservations(dict, TOOAPI_Baseclass):
    """Adapted dictionary class for containing observations that mostly is just
    to ensure that data can be displayed in a consistent format. Key is
    typically the Swift Observation ID in SDC format (e.g. '00012345012')."""

    @property
    def _table(self):
        if len(self.values()) > 0:
            header = list(self.values())[0]._table[0]
        else:
            header = []
        return header, [self[obsid]._table[1][0] for obsid in self.keys()]


class SwiftAFST(
    TOOAPI_Baseclass,
    TOOAPIAutoResolve,
    #    TOOAPI_ClockCorrect,
    SwiftAFSTSchema,
):
    """Class to fetch Swift As-Flown Science Timeline (AFST) for given
    constraints. Essentially this will return what Swift observed and when, for
    given constraints. Constraints can be for give coordinate (SkyCoord or J2000
    RA/Dec) and radius (in degrees), a given date range, or a given target ID
    (targetid) or Observation ID (obsnum).

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
    username: str
        Swift TOO API username (default 'anonymous')
    shared_secret: str
        TOO API shared secret (default 'anonymous')
    entries : list
        List of observations (`SwiftAFSTEntry`)
    status : TOOStatus
        Status of API request
    afstmax: datetime
        When is the AFST valid up to
    """

    # Define API name
    api_name: str = "Swift_AFST"

    # Define API endpoint
    _endpoint = "/swift/obsquery"

    # Define API schema
    _schema = SwiftAFSTSchema
    _get_schema = SwiftAFSTGetSchema

    # Observations
    _observations = SwiftObservations()

    # Local variables
    _local = ["obsid", "name", "skycoord", "length", "target_id", "shared_secret"]

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

    def append(self, value):
        self.entries.append(value)


# Alias names for class for better PEP8 and future compat
Swift_ObsQuery = SwiftAFST
ObsQuery = SwiftAFST
AFST = SwiftAFST
Swift_AFST = SwiftAFST
Swift_AFST_Entry = SwiftAFSTEntrySchema
ObsEntry = SwiftAFSTEntrySchema
Swift_ObsEntry = SwiftAFSTEntrySchema
AFSTEntry = SwiftAFSTEntrySchema
Swift_AFSTEntry = SwiftAFSTEntrySchema
Swift_Observation = SwiftObservation
Swift_Observations = SwiftObservations

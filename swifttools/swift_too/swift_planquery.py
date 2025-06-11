from datetime import datetime
from typing import Optional, Union

from pydantic import Field, model_validator

from .api_common import TOOAPIBaseclass
from .api_resolve import TOOAPIAutoResolve
from .swift_clock import TOOAPIClockCorrect
from .swift_data import TOOAPIDownloadData
from .swift_obsquery import SwiftObservation
from .swift_schemas import AstropyAngle, BaseSchema, ObsIDSDC, OptionalBeginEndLengthSchema, OptionalCoordinateSchema


class SwiftPPSTGetSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    radius: Optional[AstropyAngle] = None
    target_id: Union[int, list[int], None] = None
    obs_id: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def validate_exactly_one_field(cls, values):
        params = cls.model_fields.keys()
        values = values.__dict__ if not isinstance(values, dict) else values
        provided_fields = [field for field in params if values.get(field) is not None]
        if not provided_fields:
            raise ValueError(
                "At least one of 'begin', 'end', 'length', 'ra', 'dec', 'radius', 'target_id', or 'obs_id' must be provided"
            )

        return values


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
    target_id : int
        target ID  of the observation
    segment : int
        segment number of the observation
    xrt_mode : str
        XRT mode of the observation
    uvot_mode : str
        Hex string UVOT mode of the observation
    bat_mode : int
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

    targname: Optional[str] = Field(default=None, alias="target_name")
    ra: Optional[float] = None
    dec: Optional[float] = None
    roll: Optional[float] = None
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    target_id: Optional[int] = None
    segment: Optional[int] = None
    obs_id: Optional[ObsIDSDC] = None
    bat_mode: Optional[int] = None
    xrt_mode: Optional[int] = None
    uvot_mode: Optional[int] = None
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
        "target_id": "Target ID",
        "segment": "Segment",
        "xrt_mode": "XRT Mode",
        "uvot_mode": "UVOT Mode",
        "bat_mode": "BAT Mode",
        "fom": "Figure of Merit",
        "obs_id": "Observation Number",
        "exposure": "Exposure (s)",
        "slewtime": "Slewtime (s)",
    }

    @property
    def exposure(self):
        return self.end - self.begin

    @property
    def _table(self):
        _parameters = ["begin", "end", "targname", "obs_id", "exposure"]
        header = [self._header_title(row) for row in _parameters]
        return header, [[self.begin, self.end, self.targname, self.obs_id, self.exposure.seconds]]


class SwiftPPSTSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    """Schema for Swift Pre-Planned Science Timeline (PPST) API."""

    radius: Optional[AstropyAngle] = None
    target_id: Union[int, list[int], None] = None
    obs_id: Optional[int] = None
    ppstmax: Optional[datetime] = None
    entries: list[SwiftPPSTEntry] = []


class SwiftPPST(TOOAPIBaseclass, TOOAPIDownloadData, TOOAPIAutoResolve, TOOAPIClockCorrect, SwiftPPSTSchema):
    """Class to fetch Swift Pre-Planned Science Timeline (PPST) for given
    constraints. Essentially this will return what Swift was planned to observe
    and when, for given constraints. Constraints can be for give coordinate
    (SkyCoord or J2000 RA/Dec) and radius (in degrees), a given date range, or a
    given target ID (target_id) or Observation ID (obs_id).

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
    _isutc = False
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
                self._observations[q.obs_id] = SwiftObservation()
            _ = [self._observations[q.obs_id].append(q) for q in self.entries]
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

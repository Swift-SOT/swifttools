from datetime import datetime, timedelta
from typing import Any, Generator, Optional, Union

from pydantic import ConfigDict, computed_field, model_validator

from ..base.back_compat import TOOAPIBackCompat
from ..base.common import TOOAPIBaseclass
from ..base.schemas import (
    AstropyAngle,
    BaseSchema,
    CoordinateSchema,
    OptionalBeginEndLengthSchema,
    OptionalCoordinateSchema,
)
from ..base.status import TOOStatus
from .clock import TOOAPIClockCorrect
from .data import TOOAPIDownloadData
from .resolve import TOOAPIAutoResolve
from .schemas import ObsIDSDC


class SwiftAFSTEntry(CoordinateSchema, TOOAPIClockCorrect, TOOAPIBaseclass, TOOAPIDownloadData, TOOAPIBackCompat):
    """Class that defines an individual entry in the Swift As-Flown Timeline

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
    ra_object : float
        RA of the object that is the target of the pointing
    dec_object : float
        dec of the object that is the target of the pointing
    target_name : str
        Target name of the primary target of the observation
    """

    begin: Optional[datetime] = None
    settle: Optional[datetime] = None
    end: Optional[datetime] = None
    obstype: Optional[str] = None
    target_name: Optional[str] = None
    roll: Optional[float] = None
    target_id: Optional[int] = None
    segment: Optional[int] = None
    obs_id: Optional[ObsIDSDC] = None
    bat_mode: Optional[int] = None
    xrt_mode: Optional[int] = None
    uvot_mode: Optional[int] = None
    fom: Optional[int] = None
    comment: Optional[str] = None
    timetarget: Optional[int] = None
    timeobs: Optional[int] = None
    flag: Optional[int] = None
    mvdfwpos: Optional[int] = None
    targettype: Optional[str] = None
    sunha: Optional[float] = None
    ra_object: Optional[float] = None
    dec_object: Optional[float] = None

    _varnames = {
        "begin": "Begin Time",
        "settle": "Settle Time",
        "end": "End Time",
        "ra": "RA(J2000)",
        "dec": "Dec(J200)",
        "roll": "Roll (deg)",
        "target_name": "Target Name",
        "target_id": "Target ID",
        "segment": "Segment",
        "ra_object": "Object RA(J2000)",
        "dec_object": "Object Dec(J2000)",
        "xrt_mode": "XRT Mode",
        "uvot_mode": "UVOT Mode",
        "bat_mode": "BAT Mode",
        "fom": "Figure of Merit",
        "obstype": "Observation Type",
        "obs_id": "Observation Number",
        "exposure": "Exposure (s)",
        "slewtime": "Slewtime (s)",
    }

    @property
    def exposure(self) -> timedelta:
        if self.settle is None or self.end is None:
            raise TypeError("Settle and end times must be set to calculate exposure")
        return self.end - self.settle

    @property
    def slewtime(self) -> timedelta:
        if self.settle is None or self.begin is None:
            raise TypeError("Begin and settle times must be set to calculate slewtime")
        return self.settle - self.begin

    @property
    def _table(self) -> tuple[list[str], list[list[Any]]]:
        parameters = ["begin", "end", "target_name", "obs_id", "exposure", "slewtime"]
        header = [self._header_title(row) for row in parameters]
        return header, [
            [
                self.begin,
                self.end,
                self.target_name,
                self.obs_id,
                self.exposure.seconds,
                self.slewtime.seconds,
            ]
        ]


class SwiftAFSTGetSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    radius: AstropyAngle = 0.19666666666666668
    target_id: Union[int, list[int], None] = None
    obs_id: Union[ObsIDSDC, list[ObsIDSDC], None] = None

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def validate_exactly_one_field(cls, values: Any) -> dict[str, Any]:
        values = values.__dict__ if not isinstance(values, dict) else values
        params = cls.model_fields.keys()
        provided_fields = [field for field in params if values.get(field) is not None]

        if provided_fields == ["radius"]:
            raise ValueError(
                "At least one of 'begin', 'end', 'length', 'ra', 'dec',  'target_id', or 'obs_id' must be provided"
            )

        return values


class SwiftAFSTSchema(OptionalCoordinateSchema, OptionalBeginEndLengthSchema):
    radius: AstropyAngle = 0.19666666666666668
    target_id: Union[int, list[int], None] = None
    obs_id: Union[ObsIDSDC, list[ObsIDSDC], None] = None
    afstmax: Optional[datetime] = None
    entries: list[SwiftAFSTEntry] = []
    status: TOOStatus = TOOStatus()


class SwiftObservation(TOOAPIBaseclass, TOOAPIDownloadData, TOOAPIBackCompat, BaseSchema):
    """Class to summarize observations taken for given observation ID (obs_id).
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
    ra_object : float
        RA of the object that is the target of the pointing
    dec_object : float
        dec of the object that is the target of the pointing
    target_name : str
        Target name of the primary target of the observation
    """

    # Core API definitions
    entries: list[SwiftAFSTEntry] = []
    status: TOOStatus = TOOStatus()

    def __getitem__(self, index: int) -> SwiftAFSTEntry:
        return self.entries[index]

    def __len__(self) -> int:
        return len(self.entries)

    def append(self, value: SwiftAFSTEntry) -> None:
        self.entries.append(value)

    def extend(self, value: list[SwiftAFSTEntry]) -> None:
        self.entries.extend(value)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def target_id(self) -> Optional[int]:
        if len(self.entries) == 0:
            return None
        return self.entries[0].target_id

    @computed_field  # type: ignore[prop-decorator]
    @property
    def segment(self) -> Optional[int]:
        if len(self.entries) == 0:
            return None
        return self.entries[0].segment

    @computed_field  # type: ignore[prop-decorator]
    @property
    def obs_id(self) -> Optional[ObsIDSDC]:
        if len(self.entries) == 0:
            return None
        return self.entries[0].obs_id

    @computed_field  # type: ignore[prop-decorator]
    @property
    def target_name(self) -> Optional[str]:  # Updated return type to Optional[str]
        if len(self.entries) == 0:
            return None
        return self.entries[0].target_name

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
        if len(self.entries) == 0 or not hasattr(self.entries[0], "slewtime"):
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
    def xrt_mode(self) -> Optional[int]:  # Updated return type to Optional[int]
        if len(self.entries) == 0:
            return None
        return self.entries[0].xrt_mode

    @computed_field  # type: ignore[prop-decorator]
    @property
    def uvot_mode(self) -> Optional[int]:  # Updated return type to Optional[int]
        if len(self.entries) == 0:
            return None
        return self.entries[0].uvot_mode

    @computed_field  # type: ignore[prop-decorator]
    @property
    def bat_mode(self) -> Optional[int]:  # Updated return type to Optional[int]
        if len(self.entries) == 0:
            return None
        return self.entries[0].bat_mode

    @computed_field  # type: ignore[prop-decorator]
    @property
    def snapshots(self) -> list[SwiftAFSTEntry]:
        return self.entries

    # Compat end

    @property
    def _table(self) -> tuple[list[str], list[list[Any]]]:
        if len(self.entries) > 0:
            header = self.entries[0]._table[0]
        else:
            header = []

        return header, [
            [
                self.begin,
                self.end,
                self.target_name,
                self.obs_id,
                self.exposure.seconds if self.exposure else None,
                self.slewtime.seconds if self.slewtime else None,
            ]
        ]


class SwiftObservations(dict, TOOAPIBaseclass):
    """Adapted dictionary class for containing observations that mostly is just
    to ensure that data can be displayed in a consistent format. Key is
    typically the Swift Observation ID in SDC format (e.g. '00012345012')."""

    @property
    def _table(self) -> tuple[list[str], list[list[Any]]]:
        if len(self.values()) > 0:
            header = list(self.values())[0]._table[0]
        else:
            header = []
        return header, [self[obsid]._table[1][0] for obsid in self.keys()]


class SwiftAFST(
    TOOAPIBaseclass,
    TOOAPIAutoResolve,
    TOOAPIClockCorrect,
    SwiftAFSTSchema,
    TOOAPIBackCompat,
):
    """Class to fetch Swift As-Flown Science Timeline (AFST) for given
    constraints. Essentially this will return what Swift observed and when, for
    given constraints. Constraints can be for give coordinate (SkyCoord or J2000
    RA/Dec) and radius (in degrees), a given date range, or a given target ID
    (target_id) or Observation ID (obs_id).

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

    # Define API endpoint
    _endpoint = "/swift/obsquery"

    # Define API schema
    _schema = SwiftAFSTSchema
    _get_schema = SwiftAFSTGetSchema

    # Observations
    _observations = SwiftObservations()

    # Local variables
    _local = ["obsid", "name", "skycoord", "length", "target_id", "shared_secret"]

    # Default times are Swift spacecraft times, not UTC
    _isutc = False

    @property
    def _table(self) -> tuple[list[str], list[list[Any]]]:
        if len(self.entries) > 0:
            header = self.entries[0]._table[0]
        else:
            header = []
        return header, [ppt._table[1][0] for ppt in self.entries]

    @property
    def api_name(self) -> str:
        """API name for the class."""
        return "Swift_AFST"

    @property
    def observations(self) -> SwiftObservations:
        if len(self.entries) > 0 and len(self._observations.keys()) == 0:
            for q in self.entries:
                self._observations[q.obs_id] = SwiftObservation()
            _ = [self._observations[q.obs_id].append(q) for q in self.entries]
        return self._observations

    def __getitem__(self, index: int) -> SwiftAFSTEntry:
        return self.entries[index]

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Generator:
        for entry in self.entries:
            yield entry

    def append(self, value: SwiftAFSTEntry) -> None:
        self.entries.append(value)


# Alias names for class for better PEP8 and future compat
Swift_ObsQuery = SwiftAFST
ObsQuery = SwiftAFST
AFST = SwiftAFST
Swift_AFST = SwiftAFST
Swift_AFST_Entry = SwiftAFSTEntry
ObsEntry = SwiftAFSTEntry
Swift_ObsEntry = SwiftAFSTEntry
AFSTEntry = SwiftAFSTEntry
Swift_AFSTEntry = SwiftAFSTEntry
Swift_Observation = SwiftObservation
Swift_Observations = SwiftObservations

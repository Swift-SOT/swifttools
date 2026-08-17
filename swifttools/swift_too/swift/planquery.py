from collections.abc import Generator
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from ..base.back_compat import TOOAPIBackCompat
from ..base.common import TOOAPIBaseclass
from ..base.repr import TOOAPIReprMixin
from ..base.schemas import (
    AstropyAngle,
    AstropyDateTime,
    AstropyDayLength,
    BaseSchema,
    OptionalBeginEndLengthSchema,
    OptionalCoordinateSchema,
)
from ..base.status import TOOStatus
from .clock import SwiftDateTimeSchema, TOOAPIClockCorrect
from .data import TOOAPIDownloadData
from .resolve import TOOAPIAutoResolve
from .schemas import ObsIDSDC


class SwiftPPSTEntry(
    OptionalCoordinateSchema, TOOAPIClockCorrect, TOOAPIBaseclass, TOOAPIDownloadData, TOOAPIBackCompat, TOOAPIReprMixin
):
    """Class that defines an individual entry in the Swift Pre-Planned Science Timeline

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
    target_name : str
        Target name of the primary target of the observation
    """

    begin: datetime | None = None
    end: datetime | None = None
    target_name: str | None = None
    roll: float | None = None
    target_id: int | None = None
    segment: int | None = None
    obs_id: ObsIDSDC | None = None
    bat_mode: int | None = None
    xrt_mode: int | None = None
    uvot_mode: int | None = None
    fom: float | None = None
    comment: str | None = None
    timetarg: int | None = None
    takodb: str | None = None

    _varnames = {
        "begin": "Begin Time",
        "end": "End Time",
        "target_name": "Target Name",
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
    }

    @property
    def exposure(self) -> timedelta | None:
        if self.end is None or self.begin is None:
            return None
        return self.end - self.begin

    @property
    def _table(self) -> tuple[list[str], list[list[Any]]]:
        parameters = ["begin", "end", "target_name", "obs_id", "exposure"]
        header = [self._header_title(row) for row in parameters]
        exposure_seconds = self.exposure.seconds if self.exposure is not None else None
        return header, [
            [
                self.begin,
                self.end,
                self.target_name,
                self.obs_id,
                exposure_seconds,
            ]
        ]


class SwiftPPSTGetSchema(BaseModel):
    ra: AstropyAngle | None = None
    dec: AstropyAngle | None = None
    begin: AstropyDateTime | None = None
    end: AstropyDateTime | None = None
    length: AstropyDayLength | None = None
    radius: AstropyAngle | None = None
    target_id: int | list[int] | None = None
    obs_id: ObsIDSDC | list[ObsIDSDC] | None = None

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def validate_exactly_one_field(cls, values: Any) -> dict[str, Any]:
        values = values.__dict__ if not isinstance(values, dict) else values
        params = cls.model_fields.keys()
        provided_fields = [field for field in params if values.get(field) is not None]

        if provided_fields == []:
            raise ValueError(
                "At least one of 'begin', 'end', 'length', 'ra', 'dec',  'target_id', or 'obs_id' must be provided"
            )

        return values


class SwiftPPSTSchema(OptionalCoordinateSchema, OptionalBeginEndLengthSchema):
    radius: AstropyAngle | None = None
    target_id: int | list[int] | None = None
    obs_id: ObsIDSDC | list[ObsIDSDC] | None = None
    ppstmax: datetime | SwiftDateTimeSchema | None = None
    entries: list[SwiftPPSTEntry] = []
    status: TOOStatus = TOOStatus()

    @model_validator(mode="before")
    @classmethod
    def validate_radius(cls, values: Any) -> dict[str, Any]:
        """Validator to set a default radius if ra and dec are provided but radius is not."""
        values = values.__dict__ if not isinstance(values, dict) else values

        # If ra and dec are provided, but not radius, set a default radius
        if values.get("ra") is not None and values.get("dec") is not None and values.get("radius") is None:
            values["radius"] = 12 / 60  # Default radius of 12 arcmin
        return values


class SwiftObservation(TOOAPIBaseclass, TOOAPIDownloadData, TOOAPIBackCompat, BaseSchema):
    """Class to summarize observations taken for given observation ID (obs_id).
    Whereas observations are typically one or more individual snapshot, in PPST
    API speak a `SwiftPPSTEntry`, this class summarizes all snapshots into a
    single begin time, end time. Note that as ra/dec may vary between each
    snapshot, only coordinates from first are given.

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
    target_name : str
        Target name of the primary target of the observation
    """

    # Core API definitions
    entries: list[SwiftPPSTEntry] = []
    status: TOOStatus = TOOStatus()

    def __getitem__(self, index: int) -> SwiftPPSTEntry:
        return self.entries[index]

    def __len__(self) -> int:
        return len(self.entries)

    def append(self, value: SwiftPPSTEntry) -> None:
        self.entries.append(value)

    def extend(self, value: list[SwiftPPSTEntry]) -> None:
        self.entries.extend(value)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def target_id(self) -> int | None:
        if len(self.entries) == 0:
            return None
        return self.entries[0].target_id

    @computed_field  # type: ignore[prop-decorator]
    @property
    def segment(self) -> int | None:
        if len(self.entries) == 0:
            return None
        return self.entries[0].segment

    @computed_field  # type: ignore[prop-decorator]
    @property
    def obs_id(self) -> ObsIDSDC | None:
        if len(self.entries) == 0:
            return None
        return self.entries[0].obs_id

    @computed_field  # type: ignore[prop-decorator]
    @property
    def target_name(self) -> str | None:
        if len(self.entries) == 0:
            return None
        return self.entries[0].target_name

    @computed_field  # type: ignore[prop-decorator]
    @property
    def exposure(self) -> timedelta | None:
        if len(self.entries) == 0:
            return None
        total_seconds = sum(
            [int((e.end - e.begin).total_seconds()) for e in self.entries if e.end is not None and e.begin is not None]
        )
        return timedelta(seconds=total_seconds) if total_seconds > 0 else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def begin(self) -> datetime | None:
        if len(self.entries) == 0:
            return None
        return min([q.begin for q in self.entries if q.begin is not None])

    @computed_field  # type: ignore[prop-decorator]
    @property
    def end(self) -> datetime | None:
        if len(self.entries) == 0:
            return None
        return max([q.end for q in self.entries if q.end is not None])

    @computed_field  # type: ignore[prop-decorator]
    @property
    def xrt_mode(self) -> int | None:
        if len(self.entries) == 0:
            return None
        return self.entries[0].xrt_mode

    @computed_field  # type: ignore[prop-decorator]
    @property
    def uvot_mode(self) -> int | None:
        if len(self.entries) == 0:
            return None
        return self.entries[0].uvot_mode

    @computed_field  # type: ignore[prop-decorator]
    @property
    def bat_mode(self) -> int | None:
        if len(self.entries) == 0:
            return None
        return self.entries[0].bat_mode

    @computed_field  # type: ignore[prop-decorator]
    @property
    def snapshots(self) -> list[SwiftPPSTEntry]:
        return self.entries

    # Compat end

    @property
    def _table(self) -> tuple[list[str], list[list[Any]]]:
        if len(self.entries) == 0:
            return [], []

        header = self.entries[0]._table[0]

        row = [
            self.begin,
            self.end,
            self.target_name,
            self.obs_id,
            self.exposure.seconds if self.exposure else None,
        ]

        return header, [row]


class SwiftObservations(dict, TOOAPIBaseclass):  # type: ignore[misc]
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


class SwiftPPST(
    TOOAPIBaseclass,
    TOOAPIAutoResolve,
    TOOAPIClockCorrect,
    SwiftPPSTSchema,
    TOOAPIBackCompat,
):
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
        List of observations (`SwiftPPSTEntry`)
    status : TOOStatus
        Status of API request
    ppstmax: datetime
        When is the PPST valid up to
    """

    # Define API endpoint
    _endpoint = "/swift/planquery"

    # Define API schema
    _schema = SwiftPPSTSchema
    _get_schema = SwiftPPSTGetSchema

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
        return "Swift_PPST"

    @property
    def observations(self) -> SwiftObservations:
        if len(self.entries) > 0 and len(self._observations.keys()) == 0:
            for q in self.entries:
                self._observations[q.obs_id] = SwiftObservation()
            _ = [self._observations[q.obs_id].append(q) for q in self.entries]
        return self._observations

    def __getitem__(self, index: int) -> SwiftPPSTEntry:
        return self.entries[index]

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Generator:
        yield from self.entries

    def append(self, value: SwiftPPSTEntry) -> None:
        self.entries.append(value)


# Class aliases for better PEP8 compliant and future compat
Swift_PlanQuery = SwiftPPST
PlanQuery = SwiftPPST
PPST = SwiftPPST
PPSTEntry = SwiftPPSTEntry
Swift_PPST_Entry = SwiftPPSTEntry
Swift_PPST = SwiftPPST

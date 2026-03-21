from datetime import datetime

from pydantic import ConfigDict, Field, model_validator

from ..base.common import TOOAPIBaseclass
from ..base.constants import XRTMODES
from ..base.schemas import AstropyAngle, BaseSchema, OptionalBeginEndLengthSchema, OptionalCoordinateSchema
from ..base.status import TOOStatus
from .resolve import TOOAPIAutoResolve
from .toorequest import SwiftTOORequestSchema


class SwiftTOORequestsGetSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    username: str | None = None
    limit: int | None = None
    offset: int | None = None
    sort_by: str | None = None
    order: str | None = None
    page: int | None = None
    year: int | None = None
    detail: bool = False
    too_id: int | None = None
    radius: float | None = None
    debug: bool = False

    @model_validator(mode="before")
    @classmethod
    def validate_at_least_one_param(cls, data):
        """Validate that at least one parameter is set."""
        if not isinstance(data, dict):
            data = data.__dict__
        if isinstance(data, dict):
            # Exclude model_config and other class attributes
            params = [
                "begin",
                "end",
                "length",
                "ra",
                "dec",
                "limit",
                "year",
                "too_id",
            ]
            if not any(data.get(param) is not None for param in params):
                raise ValueError("At least one parameter must be set")
        return data

    model_config = ConfigDict(extra="ignore")


class SwiftTOORequestsSchema(BaseSchema):
    begin: datetime | None = None
    length: float | None = None
    limit: int | None = None
    offset: int | None = None
    sort_by: str | None = None
    order: str | None = None
    year: int | None = None
    detail: bool = False
    too_id: int | None = None
    ra: AstropyAngle | None = None
    dec: AstropyAngle | None = None
    radius: AstropyAngle | None = None
    debug: bool = False
    entries: list[SwiftTOORequestSchema] = Field(default_factory=list)
    status: TOOStatus = Field(default_factory=TOOStatus)


class SwiftTOORequests(TOOAPIBaseclass, TOOAPIAutoResolve, SwiftTOORequestsSchema):
    """Class used to obtain details about previous TOO requests.

    Attributes
    ----------
    username: str
        Swift TOO API username (default 'anonymous')
    shared_secret: str
        TOO API shared secret (default 'anonymous')
    entries : list[SwiftTOORequestSchema]
        List of TOOs (`SwiftTOORequest`)
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

    _schema = SwiftTOORequestsSchema
    _get_schema = SwiftTOORequestsGetSchema
    _endpoint = "/swift/too"

    def __getitem__(self, index):
        if len(self.entries) == 0:
            return SwiftTOORequestSchema()
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

    @staticmethod
    def _format_uvot_mode(mode):
        if mode is None:
            return None
        if isinstance(mode, int):
            return f"0x{mode:04X}"
        if isinstance(mode, str):
            try:
                parsed = int(mode, 0)
                return f"0x{parsed:04X}"
            except ValueError:
                return mode
        return mode

    @staticmethod
    def _format_xrt_mode(mode):
        if mode is None:
            return XRTMODES.get(None)
        if isinstance(mode, str):
            try:
                mode = int(mode, 0)
            except ValueError:
                return mode
        if isinstance(mode, int):
            return XRTMODES.get(mode, str(mode))
        return mode

    @property
    def _table(self):
        table_cols = [
            "too_id",
            "target_name",
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
            header = [self.entries[0]._varnames[col] for col in table_cols]
        else:
            header = []
        t = list()
        for e in self.entries:
            row = [getattr(e, col) for col in table_cols]
            row[5] = self._format_uvot_mode(row[5])
            row[6] = self._format_xrt_mode(row[6])
            t.append(row)
        return header, t


# PEP8 compliant shorthand alias
TOORequests = SwiftTOORequests
# API compat
Swift_TOORequests = SwiftTOORequests
Swift_TOO_Requests = SwiftTOORequests

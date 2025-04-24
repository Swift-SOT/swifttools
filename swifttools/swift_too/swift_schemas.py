from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional, Union

from astropy.coordinates import SkyCoord  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from pytz import utc

from .swift_datetime import swiftdatetime


class ObsType(str, Enum):
    SPECTROSCOPY = "Spectroscopy"
    LIGHT_CURVE = "Light Curve"
    POSITION = "Position"
    TIMING = "Timing"
    BLANK = ""


class BaseSchema(BaseModel):
    """Just define from_attributes for every Schema"""

    model_config = ConfigDict(
        from_attributes=True,
    )
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )


class SwiftTOOStatusSchema(BaseSchema):
    status: str = "Pending"
    too_id: Optional[int] = None
    jobnumber: Optional[int] = None
    errors: list = []
    warnings: list = []


class BeginEndLengthSchema(BaseSchema):
    """
    A schema to validate the begin, end, and length of an observation.
    Only one of 'end' or 'length' should be provided.
    """

    begin: Optional[datetime] = Field(default=None, description="Start time (UTC)")
    end: Optional[datetime] = Field(default=None, description="End time (UTC)")
    length: Optional[timedelta] = Field(
        default=None,
        description="Length of requested time period (days)",
        exclude=True,  # We don't want to include length in the output
    )

    @model_validator(mode="after")
    def check_begin_end_length(self) -> "BeginEndLengthSchema":
        begin = self.begin
        end = self.end
        length = self.length
        if isinstance(length, (int, float)):
            length = timedelta(days=length)
        if not begin:
            raise ValueError("Begin time must be provided.")
        if end and length:
            if end != begin + length:
                raise ValueError("Only one of 'end', or 'length' should be provided.")
        if not (begin or end or length):
            raise ValueError("At least 'begin' and 'end' or 'length' must be provided.")
        if begin and length:
            end = begin + length
        if end and begin:
            if end < begin:
                raise ValueError("End time cannot be before begin time.")
            else:
                length = end - begin
        self.length = length
        self.end = end
        return self


class OptionalBeginEndLengthSchema(BaseSchema):
    """
    A schema to validate the begin, end, and length of an observation.
    Only one of 'end' or 'length' should be provided.
    """

    begin: Optional[datetime] = Field(default=None, description="Start time (UTC)")
    end: Optional[datetime] = Field(default=None, description="End time (UTC)")
    length: Optional[float] = Field(
        default=None,
        description="Length of requested time period (days)",
        exclude=True,  # We don't want to include length in the output
    )

    @model_validator(mode="after")
    def check_begin_end_length(self) -> "OptionalBeginEndLengthSchema":
        begin = self.begin
        end = self.end
        length = self.length

        if not begin:
            return self
        if end and length:
            if end != begin + timedelta(days=length):
                print(begin, end, length, begin + timedelta(days=length))
                raise ValueError("Only one of 'end', or 'length' should be provided.")
        if not (begin or end or length):
            raise ValueError("At least 'begin' and 'end' or 'length' must be provided.")
        if begin and length:
            end = begin + timedelta(days=length)
        if end and begin:
            if end < begin:
                raise ValueError("End time cannot be before begin time.")
            else:
                length = (end - begin).total_seconds() / 86400.0
        self.length = length
        self.end = end
        return self


class OptionalCoordinateSchema(BaseSchema):
    ra: Optional[float] = Field(default=None, description="Right Ascension (degrees)", ge=0, lt=360)
    dec: Optional[float] = Field(default=None, description="Declination (degrees)", ge=-90, le=90)
    skycoord: Optional[SkyCoord] = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def check_coordinates(self) -> "OptionalCoordinateSchema":
        # Check that RA and Dec are both the same type
        if (self.ra is None) != (self.dec is None):
            raise ValueError("Both RA and Dec must be provided or neither.")
        if self.ra is not None and self.dec is not None and self.skycoord is None:
            try:
                self.skycoord = SkyCoord(ra=self.ra, dec=self.dec, unit="deg").fk5
            except Exception as e:
                raise ValueError(f"Invalid coordinates: {e}")
        if self.skycoord is not None:
            self.ra = self.skycoord.fk5.ra.deg
            self.dec = self.skycoord.fk5.dec.deg

        return self


class CoordinateSchema(BaseSchema):
    ra: float = Field(description="Right Ascension (degrees)", ge=0, lt=360)
    dec: float = Field(description="Declination (degrees)", ge=-90, le=90)
    skycoord: Optional[SkyCoord] = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def check_coordinates(cls, values: dict[str, Union[float, SkyCoord]]) -> dict[str, float]:
        if not isinstance(values, dict):
            values = values.__dict__
        ra = values.get("ra")
        dec = values.get("dec")
        skycoord = values.get("skycoord")
        if ra is None or dec is None and skycoord is None:
            raise ValueError("Both RA and Dec must be provided.")
        if skycoord is not None and isinstance(skycoord, SkyCoord):
            values["ra"] = skycoord.fk5.ra.deg
            values["dec"] = skycoord.fk5.dec.deg
        try:
            values["skycoord"] = SkyCoord(ra=ra, dec=dec, unit="deg").fk5
        except Exception as e:
            raise ValueError(f"Invalid coordinates: {e}")
        return values


class SwiftCalendarGetSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    too_id: Optional[int] = None
    radius: Optional[float] = 12 / 60.0
    targetid: Optional[int] = None


class SwiftCalendarSchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    too_id: Optional[int] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    radius: Optional[float] = None
    targetid: Optional[int] = None
    entries: list[SwiftCalendarEntrySchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftCalendarEntrySchema(BaseSchema):
    start: Optional[datetime] = None
    stop: Optional[datetime] = None
    type: str = "TOO"
    pi_name: str = ""
    co_point: Optional[str] = None
    seg_comment: Optional[str] = None
    sip_target_ID: int = 0
    sun_constrained: Optional[bool] = None
    enter_sun_constraint: Optional[datetime] = None
    exit_sun_constraint: Optional[datetime] = None
    moon_constrained: Optional[bool] = None
    enter_moon_constraint: Optional[datetime] = None
    exit_moon_constraint: Optional[datetime] = None
    pole_constrained: Optional[bool] = None
    enter_pole_constraint: Optional[datetime] = None
    exit_pole_constraint: Optional[datetime] = None
    roll_constrained: Optional[bool] = None
    visibility_time: Optional[float] = None
    extended_ephem: Optional[str] = None
    typeID: Optional[int]
    duration: Optional[float]
    roll: Optional[float]
    target_ID: Optional[int]
    target_name: Optional[str]
    ra: Optional[float]
    dec: Optional[float]
    sip: Optional[int]
    sip_uvot_mode: int = 39321
    sip_SSmin: int = 300
    xrt_mode: int = 7
    bat_mode: int = 0
    uvot_mode: int = 39321

    # Variable names
    _varnames: dict[str, str] = {
        "start": "Start",
        "stop": "Stop",
        "xrt_mode": "XRT Mode",
        "bat_mode": "BAT Mode",
        "uvot_mode": "UVOT Mode",
        "duration": "Exposure (s)",
        "asflown": "AFST (s)",
        "merit": "Merit",
        "ra": "Right Ascension (deg)",
        "dec": "Declination (deg)",
        "targetid": "Target ID",
    }

    def __getitem__(self, key):
        if key in self._varnames:
            return getattr(self, key)

    @property
    def _table(self):
        parameters = ["start", "stop", "xrt_mode", "uvot_mode", "duration", "asflown"]
        header = [self._varnames[row] for row in parameters]
        return header, [[getattr(self, row) for row in parameters]]


class SwiftTOOStatusGetSchema(BaseSchema):
    jobnumber: Optional[int] = None


class SwiftResolveGetSchema(BaseSchema):
    name: str


class SwiftResolveSchema(OptionalCoordinateSchema):
    name: Optional[str] = None
    resolver: Optional[str] = None
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftVisQueryGetSchema(BeginEndLengthSchema, CoordinateSchema):
    hires: bool = False


class SwiftVisQuerySchema(BeginEndLengthSchema, CoordinateSchema):
    hires: bool = False
    windows: list[SwiftVisWindowSchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftVisWindowSchema(BeginEndLengthSchema):
    @property
    def _table(self):
        header = [row for row in self.__class__.model_fields]
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


class SwiftAFSTGetSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    radius: float = 0.19666666666666668
    targetid: Union[int, list[int], None] = None
    obsnum: Optional[int] = None


class SwiftAFSTSchema(OptionalCoordinateSchema, OptionalBeginEndLengthSchema):
    radius: float = 0.19666666666666668
    targetid: Union[int, list[int], None] = None
    obsnum: Optional[int] = None
    afstmax: Optional[datetime] = None
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()
    entries: list[SwiftAFSTEntrySchema] = []


class SwiftAFSTEntrySchema(CoordinateSchema):
    begin: Optional[datetime] = None
    settle: Optional[datetime] = None
    end: Optional[datetime] = None
    obstype: Optional[str] = None
    targname: Optional[str] = None
    roll: Optional[float] = None
    targetid: Optional[int] = None
    seg: Optional[int] = None
    obsnum: Optional[int] = None
    bat: Optional[int] = None
    xrt: Optional[int] = None
    uvot: Optional[int] = None
    fom: Optional[int] = None
    comment: Optional[str] = None
    timetarget: Optional[int] = None
    timeobs: Optional[int] = None
    flag: Optional[int] = None
    mvdfwpos: Optional[int] = None
    targettype: Optional[str] = None
    sunha: Optional[float] = None
    ra_point: Optional[float] = None
    dec_point: Optional[float] = None

    @property
    def exposure(self):
        return self.end - self.settle

    @property
    def slewtime(self):
        return self.settle - self.begin

    @property
    def _table(self):
        parameters = ["begin", "end", "targname", "obsnum", "exposure", "slewtime"]
        header = [row for row in parameters]
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


class SwiftObservationSchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    obstype: Optional[str] = None
    targname: Optional[str] = None
    roll: Optional[float] = None
    targetid: Optional[int] = None
    seg: Optional[int] = None
    obsnum: Optional[int] = None
    bat: Optional[int] = None
    xrt: Optional[int] = None
    uvot: Optional[int] = None
    fom: Optional[int] = None
    comment: Optional[str] = None
    timetarget: Optional[int] = None
    timeobs: Optional[int] = None
    flag: Optional[int] = None
    mvdfwpos: Optional[int] = None
    targettype: Optional[str] = None
    sunha: Optional[float] = None
    ra_point: Optional[float] = None
    dec_point: Optional[float] = None

    @property
    def exposure(self):
        return self.end - self.settle

    @property
    def slewtime(self):
        return self.settle - self.begin

    @property
    def _table(self):
        parameters = ["begin", "end", "targname", "obsnum", "exposure", "slewtime"]
        header = [row for row in parameters]
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


class SwiftPPSTGetSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    radius: Optional[float] = None
    targetid: Union[int, list[int], None] = None
    obsnum: Optional[int] = None


class SwiftPPSTSchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    radius: Optional[float] = None
    targetid: Union[int, list[int], None] = None
    obsnum: Optional[int] = None
    ppstmax: Optional[datetime] = None
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()
    entries: list[SwiftPPSTEntrySchema] = []


class SwiftPPSTEntrySchema(BaseSchema):
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

    @property
    def exposure(self):
        return self.end - self.begin

    @property
    def _table(self):
        _parameters = ["begin", "end", "targname", "obsnum", "exposure"]
        header = [row for row in _parameters]
        return header, [[self.begin, self.end, self.targname, self.obsnum, self.exposure.seconds]]


class SwiftGUANOGetSchema(OptionalBeginEndLengthSchema):
    subthreshold: bool = False
    successful: bool = True
    triggertime: Optional[datetime] = None
    limit: Optional[int] = None
    page: Optional[int] = None
    triggertype: Optional[str] = None


class SwiftGUANOSchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    subthreshold: bool = False
    successful: bool = True
    triggertime: Optional[datetime] = None
    limit: Optional[int] = None
    triggertype: Optional[str] = None
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()
    lastcommand: Optional[datetime] = None
    guanostatus: Optional[bool] = None
    entries: list[SwiftGUANOEntrySchema] = []


class SwiftGUANODataSchema(BaseSchema):
    obsid: Optional[str] = None
    triggertime: Optional[datetime] = None
    all_gtis: list[SwiftGUANOGTISchema]
    filenames: Union[list[str], None] = None
    acs: Optional[str] = None
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    gti: Optional[SwiftGUANOGTISchema] = None
    exposure: Optional[float] = None

    @property
    def utcf(self):
        if self.gti is not None:
            return self.gti.utcf

    @property
    def subthresh(self):
        """Is this data subthreshold? I.e. located in the 'BAT Data for
        Subthreshold Triggers' directory of SDC, as opposed to being associated
        with the target ID."""
        if self.filenames is None:
            return None
        if len(self.filenames) == 1 and "ms" in self.filenames[0]:
            return True
        else:
            return False


class SwiftGUANOGTISchema(BaseSchema):
    filename: Union[str, list[str], None] = None
    acs: Optional[str] = None
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    utcf: Optional[float] = None
    exposure: timedelta = timedelta(0)

    def __str__(self):
        return f"{self.begin} - {self.end} ({self.exposure})"


class SwiftGUANOEntrySchema(BaseSchema):
    triggertype: Optional[str] = None
    triggertime: Optional[datetime] = None
    offset: Optional[float] = None
    duration: Optional[float] = None
    obsnum: Optional[str] = None
    exectime: Optional[datetime] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    data: Optional[SwiftGUANODataSchema] = None
    quadsaway: Optional[int] = None

    @property
    def executed(self):
        """Has the GUANO command been executed on board Swift?"""
        if self.quadsaway == 2 or self.quadsaway == 3:
            return False
        return True

    @property
    def _table(self):
        table = []
        for row in self._parameters + self._attributes:
            value = getattr(self, row)
            if row == "data" and self.data.exposure is not None:
                table += [[row, f"{value.exposure:.1f}s of BAT event data"]]
            elif row == "data" and self.data.exposure is None:
                table += [[row, "No BAT event data found"]]
            elif value is not None:
                table += [[row, f"{value}"]]
        return ["Parameter", "Value"], table

    def _calc_begin_end(self):
        self.begin = self.triggertime + timedelta(seconds=self.offset - self.duration / 2)
        self.end = self.triggertime + timedelta(seconds=self.offset + self.duration / 2)


class SwiftUVOTModeGetSchema(OptionalCoordinateSchema):
    uvotmode: int


class SwiftUVOTModeSchema(BaseSchema):
    uvotmode: Optional[int] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    entries: list[SwiftUVOTModeEntrySchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftUVOTModeEntrySchema(BaseSchema):
    uvotmode: int = 0
    filter_num: Optional[int] = None
    min_exposure: Optional[int] = None
    filter_pos: Optional[int] = None
    filter_seqid: Optional[int] = None
    eventmode: Optional[int] = None
    field_of_view: Optional[int] = None
    binning: Optional[int] = None
    max_exposure: Optional[int] = None
    weight: Optional[int] = None
    special: Optional[int] = None
    comment: Optional[str] = None
    filter_name: str


class SwiftTOOCommandGetSchema(BaseSchema):
    filename: str


class SwiftTOOCommandSchema(BaseSchema):
    filename: Optional[str] = None
    type: Optional[str] = None
    command: Optional[str] = None
    currentat: Optional[int] = None
    obsid: Optional[int] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    roll: Optional[float] = None
    batmode: Optional[int] = None
    xrtmode: Optional[int] = None
    uvotmode: Optional[int] = None
    exposure: Optional[float] = None
    grbmet: Optional[datetime] = None
    merit: Optional[int] = None
    passtime: Optional[datetime] = None
    auto: Optional[bool] = False
    uplink: Optional[datetime] = None
    transferred: Optional[bool] = False
    groupname: Optional[str] = None
    sc_slew: Optional[datetime] = None
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()
    source_name: Optional[str]


class SwiftTOOCommandsGetSchema(OptionalBeginEndLengthSchema, BaseSchema):
    limit: Optional[int] = None


class SwiftTOOCommandsSchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: Optional[int] = None
    entries: list[SwiftTOOCommandSchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftManyPointSchema(BaseSchema):
    filename: Optional[str] = None
    year: Optional[int] = None
    day: Optional[int] = None
    passtime: Optional[datetime] = None
    uplink: Optional[datetime] = None
    number: Optional[int] = None
    transferred: Optional[bool] = False
    entries: list[SwiftManyPointCommandSchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftManyPointCommandSchema(BaseSchema):
    filename: Optional[str] = None
    entry: Optional[int] = None
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    command: Optional[str] = None
    obsid: Optional[int] = None
    grbmet: Optional[int] = None
    merit: Optional[int] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    roll: Optional[float] = None
    batmode: Optional[str] = None
    xrtmode: Optional[str] = None
    uvotmode: Optional[str] = None
    executed: Optional[datetime] = None
    source_name: Optional[str]


class SwiftCommandsGetSchema(OptionalBeginEndLengthSchema):
    limit: Optional[int] = None


class SwiftCommandsSchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: Optional[int] = None
    entries: list[SwiftTOOCommandSchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftTOOGroupSchema(BaseSchema):
    groupname: Optional[str] = None
    entries: list[SwiftTOOCommandSchema] = []


class SwiftTOOGroupsGetSchema(OptionalBeginEndLengthSchema):
    limit: Optional[int] = None


class SwiftTOOGroupsSchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: Optional[int] = None
    entries: list[SwiftTOOGroupSchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftManyPointsGetSchema(OptionalBeginEndLengthSchema):
    limit: Optional[int] = None


class SwiftManyPointsSchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: Optional[int] = None
    entries: list[SwiftManyPointSchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftTOORequestsGetSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    limit: Optional[int] = None
    page: Optional[int] = None
    year: Optional[int] = None
    detail: bool = False
    too_id: Optional[int] = None
    radius: Optional[float] = None
    debug: bool = False


class SwiftTOORequestsSchema(BaseSchema):
    begin: Optional[datetime] = None
    length: Optional[float] = None
    limit: Optional[int] = None
    year: Optional[int] = None
    detail: bool = False
    too_id: Optional[int] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    radius: Optional[float] = None
    debug: bool = False
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()
    entries: list[SwiftTOORequestSchema] = []


class SwiftTOORequestSchema(BaseSchema):
    too_id: Optional[int]
    timestamp: Optional[datetime]
    username: Optional[str]
    source_name: Optional[str]
    source_type: Optional[str]
    ra: Optional[float]
    dec: Optional[float]
    poserr: Union[float, str, None]
    instrument: Optional[str]
    urgency: Optional[int]
    opt_mag: Union[float, str, None]
    opt_filt: Optional[str]
    xrt_countrate: Union[float, str, None]
    bat_countrate: Union[float, str, None]
    other_brightness: Optional[str]
    grb_detector: Optional[str]
    immediate_objective: Optional[str]
    science_just: Optional[str]
    total_exp_time_approved: Optional[int]
    exp_time_just: Optional[str]
    exp_time_per_visit_approved: Optional[int]
    num_of_visits_approved: Optional[int]
    monitoring_freq: Optional[str]
    proposal: Optional[bool]
    proposal_id: Optional[str]
    proposal_trigger_just: Optional[str]
    proposal_pi: Optional[str]
    xrt_mode: Optional[int]
    uvot_mode: Optional[str]
    uvot_just: Optional[str]
    tiling: Optional[bool]
    number_of_tiles: Optional[str]
    exposure_time_per_tile: Optional[int]
    tiling_justification: Optional[str]
    obs_n: Union[int, str, None]
    obs_type: Union[ObsType, str, None]
    calendar: Optional[SwiftCalendarSchema]
    grb_triggertime: Optional[datetime]
    done: Optional[int]
    decision: Optional[str]
    target_id: Optional[int]
    uvot_mode_approved: Optional[str]
    xrt_mode_approved: Optional[int]
    date_begin: Union[str, date, None]
    date_end: Union[str, date, None]
    l_name: Optional[str]


class SwiftSOTStatsSchema(BaseSchema):
    statstring: Optional[str] = None
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftClockGetSchema(BaseSchema):
    met: Union[float, list[float], None] = None
    utctime: Union[datetime, list[datetime], None] = None
    swifttime: Union[datetime, list[datetime], None] = None


class SwiftDateTimeSchema(BaseSchema):
    met: float
    utcf: float
    isutc: bool

    @computed_field  # type: ignore[prop-decorator]
    @property
    def swifttime(self) -> swiftdatetime:
        return swiftdatetime.frommet(self.met, utcf=self.utcf, isutc=self.isutc).swifttime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def utctime(self) -> swiftdatetime:
        return swiftdatetime.frommet(self.met, utcf=self.utcf, isutc=self.isutc).utctime


class SwiftClockSchema(BaseSchema):
    met: Union[float, list[float], None] = None
    utctime: Union[datetime, list[datetime], None] = None
    swifttime: Union[datetime, list[datetime], None] = None
    entries: list[SwiftDateTimeSchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftGIPIGetSchema(BaseSchema):
    pinb: Optional[int] = None


class SwiftGIPISchema(BaseSchema):
    pinb: Optional[int] = None
    name: str = "None None None"
    institution: Optional[str]
    country: Optional[str]


class SwiftGIProgramGetSchema(BaseSchema):
    gi_id: Optional[int] = None


class SwiftGIProgramSchema(BaseSchema):
    gi_id: Optional[int] = None
    title: Optional[str] = None
    proposal_type: Optional[str] = None
    pi: Optional[SwiftGIPISchema] = None
    targets: Optional[SwiftGITargetsSchema] = None
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()
    exposure: Optional[int]
    too: Optional[bool] = False
    number_targets: Optional[int]


class SwiftGIProgramsGetSchema(BaseSchema):
    cycle: Optional[int] = None


class SwiftGIProgramsSchema(BaseSchema):
    cycle: Optional[int] = None
    entries: list[SwiftGIProgramSchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftGITargetGetSchema(BaseSchema):
    gi_id: Optional[int] = None
    target_no: Optional[int] = None


class SwiftGITargetSchema(BaseSchema):
    gi_id: Optional[int] = None
    target_no: Optional[int] = None
    source_type: Optional[str] = None
    trigger_criteria: Optional[str] = None
    monitor_criteria: Optional[str] = None
    constraints_desc: Optional[str] = None
    target_id: Optional[int] = None
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()
    too: Optional[bool]
    fill_in: Optional[bool]
    large_program: Optional[bool]
    constrained: Optional[bool]
    xrt_mode: Optional[int]
    urgency: Optional[int]
    instrument: Optional[str]
    obs_type: Optional[str]
    source_name: Optional[str]
    monitoring_freq: Optional[str]
    num_of_visits: Optional[int]
    exposure: Optional[float]
    exp_time_per_visit: Optional[int]
    ra: Optional[float]
    dec: Optional[float]


class SwiftGITargetsGetSchema(OptionalCoordinateSchema):
    gi_id: Optional[int] = None
    targetid: Optional[int] = None


class SwiftGITargetsSchema(BaseSchema):
    entries: list = []
    gi_id: Optional[int] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    targetid: Optional[int] = None
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftSAAGetSchema(BeginEndLengthSchema):
    bat: bool = False


class SwiftSAASchema(BaseSchema):
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    bat: bool = False
    entries: list[SwiftSAAEntrySchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftSAAEntrySchema(BaseSchema):
    begin: datetime
    end: datetime


class SwiftDataSchema(BaseSchema):
    obsid: Optional[str] = None
    auxil: bool = True
    bat: Optional[bool] = None
    xrt: Optional[bool] = None
    uvot: Optional[bool] = None
    log: Optional[bool] = None
    tdrss: Optional[bool] = None
    quicklook: bool = False
    uksdc: Optional[bool] = None
    itsdc: Optional[bool] = None
    subthresh: Optional[bool] = None
    entries: list[SwiftDataFileSchema] = []
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()


class SwiftDataFileGetSchema(BaseSchema):
    filename: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    quicklook: bool = False
    type: Optional[str]


class SwiftDataFileSchema(BaseSchema):
    filename: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    quicklook: bool = False
    type: Optional[str]

from datetime import date, datetime
from typing import Any, Literal, Optional, Union

from pydantic import Field, computed_field, field_validator, model_validator

from ..base.back_compat import TOOAPIBackCompat
from ..base.common import TOOAPIBaseclass
from ..base.repr import TOOAPIReprMixin
from ..base.schemas import AstropyAngle, BaseSchema, StrIntFloat, TextLength, UVOTModeType, XRTModeType
from ..base.status import TOOStatus
from .calendar import SwiftCalendar
from .enums import UrgencyEnum, XRTModeEnum
from .resolve import TOOAPIAutoResolve
from .schemas import ObsType


class SwiftTOORequestSchema(BaseSchema, TOOAPIReprMixin, TOOAPIBackCompat):
    too_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    # target_name: Optional[str] = None
    target_type: Optional[str] = None
    ra: Optional[AstropyAngle] = None
    dec: Optional[AstropyAngle] = None
    poserr: Union[float, str, None] = None
    instrument: Optional[str] = None
    urgency: Optional[int] = UrgencyEnum.MEDIUM
    opt_mag: Union[float, str, None] = None
    opt_filt: Optional[str] = None
    xrt_countrate: Union[StrIntFloat, None] = None
    bat_countrate: Union[float, str, None] = None
    other_brightness: Optional[str] = None
    grb_detector: Optional[str] = None
    immediate_objective: Optional[str] = None
    science_just: Optional[str] = None
    total_exp_time_approved: Optional[int] = None
    exp_time_just: Optional[str] = None
    exp_time_per_visit_approved: Optional[int] = None
    num_of_visits_approved: Optional[int] = None
    monitoring_freq: Optional[TextLength] = None
    proposal: bool = False
    proposal_id: Optional[str] = None
    proposal_trigger_just: Optional[str] = None
    proposal_pi: Optional[str] = None
    xrt_mode: XRTModeType = XRTModeEnum.PHOTON_COUNTING
    uvot_mode: Optional[UVOTModeType] = 0x9999
    uvot_just: Optional[str] = None
    tiling: bool = False
    number_of_tiles: Optional[str] = None
    exposure_time_per_tile: Optional[int] = None
    tiling_justification: Optional[str] = None
    obs_n: Union[int, str, None] = None
    obs_type: Optional[ObsType] = None
    calendar: Optional[SwiftCalendar] = None
    grb_triggertime: Optional[datetime] = None
    done: Optional[int] = None
    decision: Optional[str] = None
    target_id: Optional[int] = None
    uvot_mode_approved: Optional[int] = None
    xrt_mode_approved: Optional[int] = None
    date_begin: Union[str, date, None] = None
    date_end: Union[str, date, None] = None
    l_name: Optional[str] = None
    num_of_visits: int = 1
    exp_time_per_visit: Optional[int] = None
    status: TOOStatus = TOOStatus()

    # Internal storage for computed exposure
    _exposure: Optional[int] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def exposure(self) -> Optional[int]:
        if self._exposure is None:
            if self.exp_time_per_visit is not None and self.num_of_visits is not None:
                self._exposure = self.exp_time_per_visit * self.num_of_visits
        return self._exposure

    @exposure.setter
    def exposure(self, v: Union[int, float]) -> None:
        self._exposure = int(v)

    # English Descriptions of all the variables
    _varnames: dict[str, str] = {
        "decision": "Decision",
        "done": "Done",
        "date_begin": "Begin date",
        "date_end": "End date",
        "calendar": "Calendar",
        "slew_in_place": "Slew in Place",
        "grb_triggertime": "GRB Trigger Time (UT)",
        "exp_time_per_visit_approved": "Exposure Time per Visit (s)",
        "total_exp_time_approved": "Total Exposure (s)",
        "num_of_visits_approved": "Number of Visits",
        "l_name": "Requester",
        "username": "Requester",
        "too_id": "ToO ID",
        "timestamp": "Time Submitted",
        "target_id": "Primary Target ID",
        "sourceinfo": "Object Information",
        "ra": "Right Ascenscion (J2000)",
        "dec": "Declination (J2000)",
        "target_name": "Object Name",
        "resolve": "Resolve coordinates",
        "position_err": "Position Error",
        "poserr": "Position Error (90% confidence - arcminutes)",
        "obs_type": "What is Driving the Exposure Time?",
        "target_type": "Type or Classification",
        "tiling": "Tiling",
        "immediate_objective": "Immediate Objective",
        "proposal": "GI Program",
        "proposal_details": "GI Proposal Details",
        "instrument": "Instrument",
        "tiling_type": "Tiling Type",
        "number_of_tiles": "Number of Tiles",
        "exposure_time_per_tile": "Exposure Time per Tile",
        "tiling_justification": "Tiling Justification",
        "instruments": "Instrument Most Critical to your Science Goals",
        "urgency": "Urgency",
        "proposal_id": "GI Proposal ID",
        "proposal_pi": "GI Proposal PI",
        "proposal_trigger_just": "GI Trigger Justification",
        "source_brightness": "Object Brightness",
        "opt_mag": "Optical Magnitude",
        "opt_filt": "Optical Filter",
        "xrt_countrate": "XRT Estimated Rate (c/s)",
        "bat_countrate": "BAT Countrate (c/s)",
        "other_brightness": "Other Brightness",
        "science_just": "Science Justification",
        "monitoring": "Observation Campaign",
        "obs_n": "Observation Strategy",
        "num_of_visits": "Number of Visits",
        "exp_time_per_visit": "Exposure Time per Visit (seconds)",
        "monitoring_freq": "Monitoring Cadence",
        "monitoring_freq_approved": "Monitoring Cadence",
        "monitoring_details": "Monitoring Details",
        "exposure": "Exposure Time (seconds)",
        "exp_time_just": "Exposure Time Justification",
        "xrt_mode": "XRT Mode",
        "xrt_mode_approved": "XRT Mode (Approved)",
        "uvot_mode": "UVOT Mode",
        "uvot_mode_approved": "UVOT Mode (Approved)",
        "uvot_just": "UVOT Mode Justification",
        "trigger_date": "GRB Trigger Date (YYYY/MM/DD)",
        "trigger_time": "GRB Trigger Time (HH:MM:SS)",
        "grb_detector": "GRB Discovery Instrument",
        "grbinfo": "GRB Details",
        "debug": "Debug mode",
        "validate_only": "Validate only",
        "quiet": "Quiet mode",
    }

    @field_validator("exposure", mode="after")
    def validate_exposure(cls, value, info):
        if value is None and cls.exp_time_per_visit is not None and cls.num_of_visits is not None:
            return cls.exp_time_per_visit * cls.num_of_visits

        return value


class SwiftTOOFormSchema(BaseSchema):
    target_name: str = Field(description="Source Name")
    target_type: str = Field(description="Source Type")
    ra: float = Field(description="Right Ascension (degrees)", ge=0, le=360)
    dec: float = Field(description="Declination (degrees)", ge=-90, le=90)
    poserr: Optional[float] = Field(None, description="Positional Error")
    instrument: Literal["XRT", "UVOT", "BAT"] = Field("XRT", description="Primary Instrument")
    obs_type: ObsType = Field(..., description="Observation Type")
    urgency: UrgencyEnum = Field(UrgencyEnum.MEDIUM, description="TOO Urgency")
    opt_mag: Union[float, str, None] = Field(None, description="Optical Magnitude")
    opt_filt: Optional[str] = Field(None, description="Optical Filter")
    xrt_countrate: Optional[StrIntFloat] = Field(None, description="XRT Count Rate")
    bat_countrate: Optional[str] = Field(None, description="BAT Count Rate")
    other_brightness: Optional[str] = Field(None, description="Other Brightness")
    grb_detector: Optional[str] = Field(None, description="GRB Detector")
    grb_triggertime: Optional[datetime] = Field(None, description="GRB Trigger Time")
    # redshift_val: Optional[str] = Field(None, description="Redshift Value")
    # redshift_status: Optional[str] = Field(None, description="Redshift Status")
    uvot_mode: UVOTModeType = Field(0x9999, description="UVOT Mode")
    science_just: str = Field(description="Science Justification")
    immediate_objective: str = Field(..., description="Immediate Objective")
    exposure: int = Field(description="Exposure Time")
    # GI Proposal
    proposal: bool = Field(False, description="GI Proposal")
    proposal_id: Optional[str] = Field(None, description="Proposal ID")
    proposal_trigger_just: Optional[str] = Field(None, description="GI Program Trigger Criteria Justification")
    proposal_pi: Optional[str] = Field(None, description="GI Proposal PI")
    uvot_just: str = Field("", description="UVOT Filter Justification")
    xrt_mode: XRTModeType = Field(XRTModeEnum.PHOTON_COUNTING, description="XRT Mode")
    tiling: bool = Field(False, description="Tiling")
    number_of_tiles: Optional[Literal["4", "7", "19", "37", "Other"]] = Field(None, description="Number of Tiles")
    exposure_time_per_tile: Optional[float] = Field(None, description="Exposure Time per Tile")
    tiling_justification: Optional[str] = Field(None, description="Tiling Justification")
    exp_time_just: str = Field(..., description="Exposure Time Justification")
    exp_time_per_visit: Optional[float] = Field(None, description="Exposure Time per Visit")
    num_of_visits: Optional[int] = Field(None, description="Number of Visits")
    monitoring_freq: Optional[TextLength] = Field(None, description="Monitoring Frequency")

    @model_validator(mode="after")
    def check_proposal(self) -> "SwiftTOOFormSchema":
        if self.exposure is None and self.exp_time_per_visit is not None and self.num_of_visits is not None:
            self.exposure = self.exp_time_per_visit * self.num_of_visits

        if self.proposal is True and (self.proposal_id is None or self.proposal_pi is None):
            raise ValueError("Must specify proposal ID and PI if GI proposal.")

        if self.proposal is True and self.proposal_trigger_just is None:
            raise ValueError("Must specify proposal trigger justification if GI TOO.")

        if self.tiling_justification is None and self.tiling is True:
            raise ValueError("Must specify tiling justification if tiling is True.")

        if (
            (self.opt_mag is None or self.opt_filt is None)
            and self.xrt_countrate is None
            and self.bat_countrate is None
            and self.other_brightness is None
        ):
            raise ValueError(
                "Must specify at least one brightness value. If specifying optical brightness, ensure filter is set."
            )

        if self.target_type == "GRB" and (self.grb_triggertime is None or self.grb_detector is None):
            raise ValueError("Must specify GRB trigger time and detector if source type is GRB.")

        if self.uvot_just == "" and "0x9999" not in str(self.uvot_mode):
            raise ValueError("Must specify UVOT justification if UVOT mode is not filter of the day (0x9999).")

        if self.num_of_visits is not None and self.monitoring_freq is None:
            raise ValueError("Must specify monitoring frequency if number of visits is specified.")

        if self.exp_time_just is None and self.num_of_visits is not None:
            raise ValueError("Must specify exposure time justification if exposure time per visit is specified.")

        if self.exp_time_per_visit is None and self.num_of_visits is not None:
            raise ValueError("Must specify exposure time per visit if number of visits is specified.")

        if self.num_of_visits is not None and self.num_of_visits > 1 and self.monitoring_freq is None:
            raise ValueError("Must specify monitoring frequency if number of visits is greater than 1.")
        return self


class SwiftTOOPostSchema(SwiftTOOFormSchema):
    username: str = Field(description="Requester username")
    debug: bool = False
    quiet: bool = True
    validate_only: bool = False

    @model_validator(mode="before")
    @classmethod
    def check_requirements(cls, data: Any) -> Any:
        requirements = [
            "ra",
            "dec",
            "num_of_visits",
            "exp_time_just",
            "target_type",
            "target_name",
            "science_just",
            "username",
            "obs_type",
        ]
        for req in requirements:
            # Handle both dict and object inputs
            value = data.get(req) if isinstance(data, dict) else getattr(data, req, None)
            if value is None:
                raise ValueError(f"Missing required field: {req}")
        return data


class SwiftTOORequest(TOOAPIBaseclass, TOOAPIAutoResolve, SwiftTOORequestSchema):
    _schema = SwiftTOOFormSchema
    _post_schema = SwiftTOOPostSchema
    _endpoint = "/swift/too"

    validate_only: bool = False
    debug: bool = False

    @property
    def obs_types(self) -> list[ObsType]:
        return [obs for obs in ObsType]

    @property
    def _table(self) -> tuple[list[str], list[list[Any]]]:
        tab = list()
        if self.decision is not None:
            _parameters = [
                "too_id",
                "l_name",
                "timestamp",
                "urgency",
                "target_name",
                "target_type",
                "grb_triggertime",
                "grb_detector",
                "ra",
                "dec",
                "proposal_pi",
                "proposal_id",
                "proposal_trigger_just",
                "poserr",
                "science_just",
                "opt_mag",
                "opt_filt",
                "xrt_countrate",
                "other_brightness",
                "bat_countrate",
                "exp_time_per_visit_approved",
                "num_of_visits_approved",
                "total_exp_time_approved",
                "monitoring_freq",
                "immediate_objective",
                "exp_time_just",
                "instrument",
                "obs_type",
                "xrt_mode_approved",
                "uvot_mode_approved",
                "uvot_just",
                "target_id",
            ]
        else:
            _parameters = [
                p for p in self.__class__.model_fields.keys() if p in self._varnames and p not in ["status", "skycoord"]
            ]
        # Use __dict__ as fallback for cases where properties may shadow
        # underlying fields (e.g., computed properties named 'target_name').
        raw_data = getattr(self, "__dict__", {})
        for row in _parameters:
            val = getattr(self, row, None)
            if val is None:
                # Try to get the raw field value directly from model_dump for
                # the specific field only. This avoids serializing unrelated
                # fields (e.g., mocked objects) which can raise errors.
                if hasattr(self, "model_dump"):
                    try:
                        val = self.model_dump(include={row}, exclude_none=True).get(row)
                    except Exception:
                        # Fall back to raw __dict__ lookup if present
                        if isinstance(raw_data, dict) and row in raw_data:
                            val = raw_data.get(row)
            if val is not None and val != "":
                tab.append([self._varnames.get(row, row), val])
        if len(tab) > 0:
            header = ["Parameter", "Value"]
        else:
            header = []
        return header, tab

    def validate(self) -> bool:  # type: ignore[override]
        """Validate the TOO request locally."""
        self.status.clear()
        return super().validate_post()

    def server_validate(self) -> bool:
        """Validate the TOO request with the TOO API server."""

        # Do a server side validation
        if self.validate_post():
            # Preserve existing warnings
            warnings = self.status.warnings
            self.validate_only = True
            self.submit()
            self.validate_only = False
            if len(self.status.errors) == 0:
                self.status.clear()
                self.status.warnings = warnings
                return True
            else:
                self.status.warnings += warnings
                return False
        else:
            return False


# Aliases for class
Swift_TOO = SwiftTOORequest
TOO = SwiftTOORequest
TOORequest = SwiftTOORequest
Swift_TOO_Request = SwiftTOORequest
Swift_TOORequest = SwiftTOORequest
SwiftTOO = SwiftTOORequest

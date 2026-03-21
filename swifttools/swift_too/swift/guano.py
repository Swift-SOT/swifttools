from datetime import datetime, timedelta

from pydantic import ConfigDict, Field, model_validator

from ..base.common import TOOAPIBaseclass, TOOAPIReprMixin
from ..base.schemas import (
    BaseSchema,
    OptionalBeginEndLengthSchema,
)
from ..base.status import TOOStatus
from .clock import TOOAPIClockCorrect
from .data import TOOAPIDownloadData


class SwiftGUANOGTI(BaseSchema, TOOAPIReprMixin):  # TOOAPIBaseclass, TOOAPIClockCorrect):
    """
    Define GUANO event data Good Time Intervals (GTI)

    Attributes
    ----------
    filename : str
        filename of BAT event data associated with GTI
    acs : str
        What was the status of the Swift Attitude Control System during this
        GTI. Options are 'slewing', 'pointing' and 'mixed'.
    began : datetime
        time request began processing
    completed : datetime
        time request finished processing
    exposure : float
        exposure time of GTI
    utcf : float
        UT Correction Factor - this encompasses correction for both the
        inaccuracies in the Swift clock and also any leap seconds
    """

    filename: str | list[str] | None = None
    acs: str | None = None
    begin: datetime | None = None
    end: datetime | None = None
    utcf: float | None = None
    exposure: timedelta = timedelta(0)

    def __str__(self):
        return f"{self.begin} - {self.end} ({self.exposure})"


class SwiftGUANOData(BaseSchema, TOOAPIReprMixin):  # , TOOAPIBaseclass, TOOAPIClockCorrect):
    """Class to hold information about GUANO data based on analysis of the BAT
    event files that are downlinked.

    Attributes
    ----------
    filenames : list
        filenames of BAT event data associated with GUANO dump
    acs : str
        What was the status of the Swift Attitude Control System during this
        GTI. Options are 'slewing', 'pointing' and 'mixed'.
    begin : datetime
        start time of GUANO dump
    end : datetime
        end time of GUANO dump
    triggertime : datetime
        trigger time of event that generated GUANO dump
    gti : SwiftGUANOGTI
        Good Time Interval (GTI) for the combined event data
    all_gtis : list
        list of individual GTIs. More than one GTI can exist if data is split
        between multiple files, or if significant gaps appear in the event data
    obs_id : str
        Observation ID associated with the GUANO data
    completed : datetime
        time request finished processing
    exposure : float
        exposure time of GTI
    utcf : float
        UT Correction Factor - this encompasses correction for both the
        inaccuracies in the Swift clock and also any leap seconds
    subthresh : boolean
        Indicates if the BAT event data associated with this trigger is
        located in the subthreshold triggers section of the SDC, rather
        than being associated with normal observation data. If this is
        true, the data can be fetched utilizing the 'subthresh = True'
        option of Swift_Data (AKA Data)
    """

    obs_id: str | None = None
    triggertime: datetime | None = None
    all_gtis: list[SwiftGUANOGTI]
    filenames: list[str] | None = None
    acs: str | None = None
    begin: datetime | None = None
    end: datetime | None = None
    gti: SwiftGUANOGTI | None = None
    exposure: float | None = None

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


class SwiftGUANOEntry(BaseSchema, TOOAPIReprMixin, TOOAPIDownloadData):  # , TOOAPIClockCorrect, ):
    """
    Entry for an individual BAT ring buffer dump (AKA GUANO) event.

    Attributes
    ----------
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    triggertime : datetime
        triggertime associated with GUANO dump
    triggertype : str
        trigger type (typically what mission triggered the GUANO dump)
    offset : int
        Number of seconds the GUANO dump is offset from triggertime
    duration : int
        Number of seconds dumped
    status : str
        status of API request
    """

    triggertype: str | None = None
    triggertime: datetime | None = None
    offset: float | None = None
    duration: float | None = None
    obs_id: str | None = None
    exectime: datetime | None = None
    ra: float | None = None
    dec: float | None = None
    data: SwiftGUANOData | None = None
    quadsaway: int | None = None
    begin: datetime | None = None
    end: datetime | None = None

    @property
    def executed(self):
        """Has the GUANO command been executed on board Swift?"""
        if self.quadsaway == 2 or self.quadsaway == 3:
            return False
        return True

    @property
    def _table(self):
        table = []
        for row in self.__class__.model_fields.keys():
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

    #     # Next part handles the use of "quadsaway" to determine if a GUANO command has been uplinked to the spacecraft,
    #     # and if it has been executed onboard.
    #     @property
    #     def quadsaway(self):
    #         if self._quadsaway > 0 and self._quadsaway < 4:
    #             return 0
    #         return self._quadsaway

    #     @quadsaway.setter
    #     def quadsaway(self, qa):
    #         self._quadsaway = qa

    @property
    def uplinked(self):
        """Has the GUANO command been uplinked to Swift?"""
        if self.quadsaway == 1 or self.quadsaway == 3:
            return False
        return True


class SwiftGUANOGetSchema(OptionalBeginEndLengthSchema):
    subthreshold: bool = False
    successful: bool = True
    triggertime: datetime | None = None
    limit: int | None = None
    page: int | None = None
    offset: int | None = None
    sort_by: str | None = None
    order: str | None = None
    triggertype: str | None = None
    queue_num: int | None = None

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def validate_parameters(cls, values):
        good = False
        if values is None:
            return
        if not isinstance(values, dict):
            values = values.__dict__
        for key in cls.model_fields.keys():
            if key in values:
                good = True
        if not good:
            raise ValueError("At least one of the parameters must be provided")
        return values


class SwiftGUANOSchema(BaseSchema):
    begin: datetime | None = None
    end: datetime | None = None
    username: str = Field(default="anonymous")
    subthreshold: bool = False
    successful: bool = True
    triggertime: datetime | None = None
    limit: int | None = None
    offset: int | None = None
    sort_by: str | None = None
    order: str | None = None
    queue_num: int | None = None
    triggertype: str | None = None
    lastcommand: datetime | None = None
    guanostatus: bool | None = None
    entries: list[SwiftGUANOEntry] = Field(default_factory=list)
    status: TOOStatus = Field(default_factory=TOOStatus)


class SwiftGUANO(
    TOOAPIBaseclass,
    TOOAPIClockCorrect,
    SwiftGUANOSchema,
):
    """Query BAT ring buffer dumps of event data associated with the Gamma-Ray
    Burst Urgent Archiver for Novel Opportunities (GUANO).

    Attributes
    ----------
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    triggertime : datetime
        triggertime to search around
    triggertype : str
        trigger type (typically what mission triggered the GUANO dump)
    begin : datetime
        start of time period to search
    end : datetime
        end of time period to search
    length : float
        length of time to search after `begin`
    limit : int
        limit number of results fetched
    entries : list
        list of GUANO dumps found given query parameters
    status : str
        status of API request
    guanostatus : boolean
        current status of guano system
    lastcommand : datetime
        when was the last GUANO command executed
    """

    # API Name
    _schema = SwiftGUANOSchema
    _get_schema = SwiftGUANOGetSchema
    _endpoint = "/swift/guano"
    _isutc: bool = True

    # Core API definitions

    _local = ["length", "shared_secret"]

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def validate(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        if (
            self.limit is not None
            or self.begin is not None
            or self.end is not None
            or getattr(self, "length", None) is not None
            or self.triggertime is not None
            or self.triggertype is not None
            or self.subthreshold is True
        ):
            if self.subthreshold is True and self.username == "anonymous":
                self.status.error("For subthreshold triggers, username cannot be anonymous.")
                return False
            return True
        # If there are no query parameters and subthreshold wasn't set, validation fails
        return False

    @property
    def _table(self):
        header = [
            "Trigger Type",
            "Trigger Time",
            "Offset (s)",
            "Window Duration (s)",
            "Observation ID",
        ]
        table = []
        for ent in self.entries:
            if ent.data.exposure is not None:
                if round(ent.duration) != round(ent.data.exposure):
                    exposure = f"{ent.duration} ({ent.data.exposure:.0f})"
                else:
                    exposure = f"{ent.duration}"
                if ent.data.gti is None:
                    exposure += "*"
            else:
                exposure = ent.duration
            if ent.obs_id is not None:
                obs_id = ent.obs_id
            else:
                if ent.executed:
                    obs_id = "Pending Data"
                elif ent.uplinked:
                    obs_id = "Pending Execution"
                else:
                    obs_id = "Unknown Status"
            table.append([ent.triggertype, ent.triggertime, ent.offset, exposure, obs_id])

        return header, table

    def _post_process(self):
        """Things to do after data are fetched from the API."""
        # Calculate begin and end times for all GUANO entries
        [e._calc_begin_end() for e in self.entries]
        # Perform clock correction by default for all dates retrieved
        self.clock_correct()


# Shorthand alias names
GUANO = SwiftGUANO
GUANOData = SwiftGUANOData
GUANOEntry = SwiftGUANOEntry
GUANOGTI = SwiftGUANOGTI
# Backwards API compat
Swift_GUANO = GUANO
Swift_GUANO_Data = GUANOData
Swift_GUANO_GTI = GUANOGTI
Swift_GUANO_Entry = GUANOEntry

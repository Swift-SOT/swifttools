from datetime import datetime, timedelta
from typing import Optional, Union

from swifttools.swift_too.swift_data import TOOAPIDownloadData

from .api_common import TOOAPIBaseclass
from .swift_clock import TOOAPIClockCorrect
from .swift_schemas import (
    BaseSchema,
    OptionalBeginEndLengthSchema,
)


class SwiftGUANOGTI(BaseSchema, TOOAPIClockCorrect):
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

    filename: Union[str, list[str], None] = None
    acs: Optional[str] = None
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    utcf: Optional[float] = None
    exposure: timedelta = timedelta(0)

    def __str__(self):
        return f"{self.begin} - {self.end} ({self.exposure})"


class SwiftGUANOData(BaseSchema, TOOAPIClockCorrect):
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
    obsid : str
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

    obsid: Optional[str] = None
    triggertime: Optional[datetime] = None
    all_gtis: list[SwiftGUANOGTI]
    filenames: Union[list[str], None] = None
    acs: Optional[str] = None
    begin: Optional[datetime] = None
    end: Optional[datetime] = None
    gti: Optional[SwiftGUANOGTI] = None
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


class SwiftGUANOEntry(BaseSchema, TOOAPIClockCorrect, TOOAPIDownloadData):
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

    triggertype: Optional[str] = None
    triggertime: Optional[datetime] = None
    offset: Optional[float] = None
    duration: Optional[float] = None
    obsnum: Optional[str] = None
    exectime: Optional[datetime] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    data: Optional[SwiftGUANOData] = None
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
    lastcommand: Optional[datetime] = None
    guanostatus: Optional[bool] = None
    entries: list[SwiftGUANOEntry] = []


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
    api_name: str = "Swift_GUANO"
    _schema = SwiftGUANOSchema
    _get_schema = SwiftGUANOGetSchema
    _endpoint = "/guano"
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
            or self.length is not None
            or self.triggertime is not None
            or self.triggertype is not None
        ):
            if self.subthreshold is True and self.username == "anonymous":
                self.status.error("For subthreshold triggers, username cannot be anonymous.")
                return False
            return True

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
            if ent.obsnum is not None:
                obsnum = ent.obsnum
            else:
                if ent.executed:
                    obsnum = "Pending Data"
                elif ent.uplinked:
                    obsnum = "Pending Execution"
            table.append([ent.triggertype, ent.triggertime, ent.offset, exposure, obsnum])

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

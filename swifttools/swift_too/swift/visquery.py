from datetime import datetime, timedelta

from pydantic import computed_field

from ..base.common import TOOAPIBaseclass
from ..base.schemas import (
    BaseSchema,
    OptionalBeginEndLengthSchema,
    OptionalCoordinateSchema,
)
from ..base.status import TOOStatus
from .clock import TOOAPIClockCorrect
from .resolve import TOOAPIAutoResolve


class SwiftVisWindow(BaseSchema, TOOAPIClockCorrect):
    """
    Simple class to define a Visibility window. Begin and End of window can
    either be accessed as self.begin or self.end, or as self[0] or self[1].

    Attributes
    ----------
    begin : datetime
        begin time of window
    end : datetime
        end time of window
    length : timedelta
        length of window
    """

    begin: datetime
    end: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def length(self) -> timedelta:
        """Length of visibility window as timedelta"""
        return self.end - self.begin

    _varnames = {"begin": "Begin Time", "end": "End Time", "length": "Window length"}

    @property
    def _table(self):
        header = [self._header_title(row) for row in ["begin", "end", "length"]]
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


class SwiftVisQuerySchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    hires: bool = False
    windows: list[SwiftVisWindow] = []
    status: TOOStatus = TOOStatus()


class SwiftVisQueryGetSchema(OptionalBeginEndLengthSchema, OptionalCoordinateSchema):
    hires: bool = False


class SwiftVisQuery(TOOAPIBaseclass, TOOAPIClockCorrect, TOOAPIAutoResolve, SwiftVisQuerySchema):
    """Request Swift Target visibility windows. These results are low-fidelity,
    so do not give orbit-to-orbit visibility, but instead long term windows
    indicates when a target is observable by Swift and not in a Sun/Moon/Pole
    constraint.

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
    hires : boolean
        Calculate visibility with high resolution, including Earth
        constraints
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    entries : list
        List of visibility windows (`Swift_VisWindow`)
    status : TOOStatus
        Status of API request
    """

    # Core API definitions
    _schema = SwiftVisQuerySchema
    _get_schema = SwiftVisQueryGetSchema
    _endpoint = "/swift/visquery"

    @property
    def _table(self):
        if len(self.windows) != 0:
            header = self.windows[0]._table[0]
        else:
            header = []
        return header, [win._table[1][0] for win in self.windows]

    # For compatibility / consistency with other classes.
    @property
    def entries(self):
        return self.windows

    def __getitem__(self, index):
        return self.windows[index]

    def __len__(self):
        return len(self.windows)


# Shorthand alias for class
VisQuery = SwiftVisQuery
VisWindow = SwiftVisWindow
Swift_VisQuery = SwiftVisQuery
Swift_VisWindow = SwiftVisWindow

from datetime import datetime

from ..base.status import TOOStatus

from ..base.common import TOOAPIBaseclass
from ..base.schemas import BaseSchema, BeginEndLengthSchema, OptionalBeginEndLengthSchema
from .clock import TOOAPIClockCorrect


class SwiftSAAGetSchema(BeginEndLengthSchema):
    bat: bool = False


class SwiftSAAEntry(BaseSchema, TOOAPIClockCorrect, TOOAPIBaseclass):
    begin: datetime
    end: datetime
    _varnames = {"begin": "Begin Time", "end": "End Time"}

    # FIXME: Clock correcting assumes begin/end are SwiftTime, they're UTC.

    @property
    def _table(self):
        header = [self._header_title("begin"), self._header_title("end")]
        data = [[self.begin, self.end]]
        return header, data


class SwiftSAASchema(OptionalBeginEndLengthSchema):
    bat: bool = False
    entries: list[SwiftSAAEntry] = []
    status: TOOStatus = TOOStatus()


class SwiftSAA(TOOAPIBaseclass, TOOAPIClockCorrect, SwiftSAASchema):
    """Class to obtain Swift SAA passage times. Two versions are available: The
    Spacecraft definition (default) or an estimate of when the BAT SAA flag is
    up. Note that the BAT SAA flag is dynamically set based on count rate, so
    this result only returns an estimate based on when that is likely to happen.

    Attributes
    ----------
    entries : list
        Array of SwiftSAAEntry classes containing the windows.
    status : TOOStatus
        Status of API request
    """

    # API details
    api_name: str = "Swift_SAA"
    _schema = SwiftSAASchema
    _get_schema = SwiftSAAGetSchema
    _endpoint: str = "/swift/saa"
    _isutc: bool = True

    def __getitem__(self, index: int) -> SwiftSAAEntry:
        return self.entries[index]

    def __len__(self) -> int:
        return len(self.entries)

    @property
    def _table(self) -> tuple[list[str], list[list[datetime]]]:
        if not self.entries:
            return [], []
        else:
            vals = list()
            for i in range(len(self.entries)):
                header, values = self.entries[i]._table
                vals.append([i] + values[0])
            return ["#"] + header, vals


# Alias
SAA = SwiftSAA
SwiftSAAEntry = SwiftSAAEntry
Swift_SAA_Entry = SwiftSAAEntry
SAAEntry = SwiftSAAEntry
Swift_SAA = SwiftSAA

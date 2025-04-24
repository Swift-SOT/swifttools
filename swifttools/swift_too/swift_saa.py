from datetime import datetime

from .api_common import TOOAPIBaseclass
from .swift_clock import TOOAPIClockCorrect
from .swift_schemas import BaseSchema, BeginEndLengthSchema, OptionalBeginEndLengthSchema


class SwiftSAAGetSchema(BeginEndLengthSchema):
    bat: bool = False


class SwiftSAAEntry(BaseSchema, TOOAPIClockCorrect):
    begin: datetime
    end: datetime

    @property
    def _table(self):
        header = [self._header_title("begin"), self._header_title("end")]
        data = [[self.begin, self.end]]
        return header, data

    @property
    def table(self):
        return ["begin", "end"], [[self.begin, self.end]]


class SwiftSAASchema(OptionalBeginEndLengthSchema):
    bat: bool = False
    entries: list[SwiftSAAEntry] = []


class SwiftSAA(TOOAPIBaseclass, TOOAPIClockCorrect, SwiftSAASchema):
    """Class to obtain Swift SAA passage times. Two versions are available: The
    Spacecraft definition (default) or an estimate of when the BAT SAA flag is
    up. Note that the BAT SAA flag is dynamically set based on count rate, so
    this result only returns an estimate based on when that is likely to happen.

    Attributes
    ----------
    entries : list
        Array of Swift_SAAEntry classes containing the windows.
    status : TOOStatus
        Status of API request
    """

    # API details
    api_name: str = "Swift_SAA"
    _schema = SwiftSAASchema
    _get_schema = SwiftSAAGetSchema
    _endpoint = "/swift/saa"

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    @property
    def _table(self):
        if self.entries is None:
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

from swifttools.swift_too.swift_schemas import SwiftSAAGetSchema, SwiftSAASchema

from .api_common import TOOAPI_Baseclass
from .swift_clock import TOOAPI_ClockCorrect


class SwiftSAAEntry(TOOAPI_Baseclass, TOOAPI_ClockCorrect):
    """Simple class describing the start and end time of a Swift SAA passage.
     Attributes
    ----------
    begin : datetime
        Start time of the SAA passage
    end : datetime
        End time of the SAA passages
    """

    # API details
    api_name: str = "Swift_SAA_Entry"
    # Returned values
    _attributes = ["begin", "end"]
    # Display names of columns
    _varnames = {"begin": "Begin", "end": "End"}

    def __init__(self):
        # Attributes
        self.begin = None
        self.end = None
        # Internal values
        self._isutc = True

    @property
    def _table(self):
        header = [self._header_title("begin"), self._header_title("end")]
        data = [[self.begin, self.end]]
        return header, data

    @property
    def table(self):
        return ["begin", "end"], [[self.begin, self.end]]


class SwiftSAA(TOOAPI_Baseclass, TOOAPI_ClockCorrect, SwiftSAASchema):
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
Swift_SAA_Entry = SwiftSAAEntry
SAAEntry = SwiftSAAEntry
Swift_SAA = SwiftSAA

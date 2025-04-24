from .api_common import TOOAPI_Baseclass
from .api_resolve import TOOAPIAutoResolve
from .swift_clock import TOOAPI_ClockCorrect
from .swift_schemas import SwiftVisQueryGetSchema, SwiftVisQuerySchema, SwiftVisWindowSchema

# class SwiftVisWindow(TOOAPI_Baseclass, TOOAPI_ClockCorrect):
#     """Simple class to define a Visibility window. Begin and End of window can
#     either be accessed as self.begin or self.end, or as self[0] or self[1].

#     Attributes
#     ----------
#     begin : datetime
#         begin time of window
#     end : datetime
#         end time of window
#     length : timedelta
#         length of window
#     """

#     api_name: str = "Swift_VisWindow"

#     def __init__(self):
#         # Set all times in this class to UTC
#         self._isutc = True
#         # Attributes
#         self.begin = None
#         self.end = None

#     @property
#     def length(self):
#         if self.end is None or self.begin is None:
#             return None
#         return self.end - self.begin

#     @property
#     def _table(self):
#         header = [self._header_title(row) for row in self._parameters + self._attributes]
#         return header, [[self.begin, self.end, self.length]]

#     def __str__(self):
#         return f"{self.begin} - {self.end} ({self.length})"

#     def __getitem__(self, index):
#         if index == 0:
#             return self.begin
#         elif index == 1:
#             return self.end
#         else:
#             raise IndexError("list index out of range")


class SwiftVisQuery(TOOAPI_Baseclass, TOOAPI_ClockCorrect, TOOAPIAutoResolve, SwiftVisQuerySchema):
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

    # API Name
    api_name: str = "Swift_VisQuery"
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
VisWindow = SwiftVisWindowSchema
Swift_VisQuery = SwiftVisQuery
Swift_VisWindow = SwiftVisWindowSchema

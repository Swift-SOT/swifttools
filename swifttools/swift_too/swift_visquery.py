from .too_status import Swift_TOO_Status
from .common import TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_SkyCoord
from .swift_resolve import TOOAPI_AutoResolve


class Swift_VisWindow(TOOAPI_Baseclass):
    '''Simple class to define a Visibility window. Begin and End of window can
    either be accessed as self.begin or self.end, or as self[0] or self[1].

    Attributes
    ----------
    begin : datetime
        begin time of window
    end : datetime
        end time of window
    length : timedelta
        length of window
    '''
    # API parameter definition
    _parameters = ['begin', 'end', 'length']
    # Names for parameters
    varnames = {'begin': 'Begin Time',
                'end': 'End Time', 'length': 'Window length'}
    # API name
    api_name = "Swift_VisWindow"
    # Attributes
    begin = None
    end = None

    @property
    def length(self):
        if self.end is None or self.begin is None:
            return None
        return self.end - self.begin

    @property
    def _table(self):
        header = [self.varnames[row] for row in self._parameters]
        return header, [[self.begin, self.end, self.length]]

    def __str__(self):
        return f"{self.begin} - {self.end} ({self.length})"

    def __getitem__(self, index):
        if index == 0:
            return self.begin
        elif index == 1:
            return self.end
        else:
            raise IndexError('list index out of range')


class Swift_VisQuery(TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_SkyCoord, TOOAPI_AutoResolve):
    '''Request Swift Target visibility windows. These results are low-fidelity,
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
    status : Swift_TOO_Status
        Status of API request
    '''

    # Parameters that are passed to the API for this request
    _parameters = ['username', 'ra', 'dec', 'length', 'begin', 'hires']
    # Local and alias parameter names
    _local = ['name', 'skycoord', 'end']
    # Attributes returned by API Server
    _attributes = ['status', 'windows']
    # Subclasses
    _subclasses = [Swift_TOO_Status, Swift_VisWindow]
    # API Name
    api_name = "Swift_VisQuery"
    # Returned data
    windows = list()

    def __init__(self, *args, **kwargs):
        '''
        Parameters
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
        '''
        # User arguments
        self.username = 'anonymous'
        self.ra = None
        self.dec = None
        self.hires = None
        self.length = None
        # Visibility windows go here
        self.windows = list()
        # Status of request
        self.status = Swift_TOO_Status()
        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        if self.validate():
            self.submit()
        else:
            self.status.clear()

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

    def validate(self):
        '''Validate all parameters are given before submission'''
        # If length is not set, set to default of 7 days, or 1 day for hires
        if self.length is None:
            if self.hires:
                self.length = 1
            else:
                self.length = 7
        # Check RA/Dec are set correctly
        if self.ra is not None and self.dec is not None:
            if self.ra >= 0 and self.ra <= 360 and self.dec >= -90 and self.dec <= 90:
                return True
            else:
                self.status.error("RA/Dec not in valid range.")
                return False
        else:
            self.status.error("RA/Dec not set.")
            return False


# Shorthand alias for class
VisQuery = Swift_VisQuery

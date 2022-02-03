from .common import TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_Instruments, TOOAPI_SkyCoord, TOOAPI_ObsID
from .too_status import Swift_TOO_Status
from .swift_obsquery import Swift_Observation, Swift_Observations
from datetime import timedelta
from .swift_resolve import TOOAPI_AutoResolve


class Swift_PPST_Entry(TOOAPI_Baseclass, TOOAPI_SkyCoord, TOOAPI_ObsID, TOOAPI_Instruments):
    '''Class that defines an individual entry in the Swift Pre-Planned Science
    Timeline

    Attributes
    ----------
    begin : datetime
        begin time of observation
    end : datetime
        end time of observation
    targetid : int
        target ID  of the observation
    seg : int
        segment number of the observation
    xrt : str
        XRT mode of the observation
    uvot : str
        Hex string UVOT mode of the observation
    bat : int
        BAT mode of the observation
    exposure : timedelta
        exposure time of the observation
    ra : float
        Right Ascension of pointing in J2000 (decimal degrees)
    dec : float
        Declination of pointing in J2000 (decimal degrees)
    roll : float
        roll angle of the observation (decimal degrees)
    skycoord : SkyCoord
        SkyCoord version of RA/Dec if astropy is installed
    targname : str
        Target name of the primary target of the observation
    '''
    # Core API defs
    _parameters = ['begin', 'end', 'targname', 'ra', 'dec', 'roll',
                   'targetid', 'seg', 'xrt', 'uvot', 'bat', 'fom']
    names = ['Begin Time', 'End Time', 'Target Name',
             'RA(J2000)', 'Dec(J200)', 'Roll (deg)', 'Target ID', 'Segment',
             'XRT Mode', 'UVOT Mode', 'BAT Mode', 'Figure of Merit']
    _attributes = []
    _subclasses = [Swift_TOO_Status]
    # API name
    api_name = "Swift_PPST_Entry"

    def __init__(self):
        # Set up naming of variables
        self.varnames = dict()
        for i in range(len(self._parameters)):
            self.varnames[self._parameters[i]] = self.names[i]
        self.varnames['obsnum'] = 'Observation Number'
        self.varnames['exposure'] = 'Exposure (s)'
        self.varnames['slewtime'] = 'Slewtime (s)'

        # Parameters
        self.begin = None
        self.end = None
        self.ra = None
        self.dec = None
        self.roll = None
        self.targname = None
        self.targetid = None
        self.seg = None
        self.slewtime = timedelta(0)  # Slewtime isn't reported in plans

        # Swift_PPST returns a bunch of stuff we don't care about, so just take the things we do
        self.ignorekeys = True

    @property
    def exposure(self):
        return self.end - self.begin

    @property
    def _table(self):
        _parameters = ['begin', 'end', 'targname', 'obsnum', 'exposure']
        header = [self.varnames[row] for row in _parameters]
        return header, [[self.begin, self.end, self.targname, self.obsnum, self.exposure.seconds]]


class Swift_PPST(TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_SkyCoord, TOOAPI_ObsID, TOOAPI_AutoResolve):
    '''Class to fetch Swift Pre-Planned Science Timeline (PPST) for given
    constraints. Essentially this will return what Swift was planned to observe
    and when, for given constraints. Constraints can be for give coordinate
    (SkyCoord or J2000 RA/Dec) and radius (in degrees), a given date range, or a
    given target ID (targetid) or Observation ID (obsnum).

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
    username: str
        Swift TOO API username (default 'anonymous')
    shared_secret: str
        TOO API shared secret (default 'anonymous')
    entries : list
        List of observations (`Swift_AFST_Entry`)
    status : Swift_TOO_Status
        Status of API request
    ppstmax: datetime
        When is the PPST valid up to
    '''

    # Core API definitions
    _parameters = ['username', 'begin', 'end', 'ra',
                   'dec', 'radius', 'targetid', 'obsnum']
    _attributes = ['status', 'ppstmax', 'entries']
    _local = ['obsid', 'name', 'skycoord', 'length', 'target_id']
    _subclasses = [Swift_PPST_Entry, Swift_TOO_Status]
    api_name = "Swift_PPST"

    def __init__(self, *args, **kwargs):
        '''
        Parameters
        ----------
        begin : datetime
            begin time of window
        end : datetime
            end time of window
        ra : float
            Right Ascension of target in J2000 (decimal degrees)
        dec : float
            Declination of target in J2000 (decimal degrees)
        radius : float
            radius in degrees to search around (default 0.197)
        targetid : int
            target ID of target
        obsid : int / str
            Observation ID of target, either in spacecraft (int) or SDC (str)
            formats
        skycoord : SkyCoord
            SkyCoord version of RA/Dec if astropy is installed
        username : str
            username for TOO API (default 'anonymous')
        length : timedelta
            length of window
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        '''
        # Coordinate search
        self.ra = None
        self.dec = None
        self.radius = 11.8/60  # Default 11.8 arcmin - XRT FOV
        # begin and end boundaries
        self.begin = None
        self.end = None
        self.length = None
        # Search on targetid/obsnum
        self.targetid = None
        self.obsnum = None
        # Login
        self.username = 'anonymous'
        # PPST entries go here
        self.entries = list()
        # Status of request
        self.status = Swift_TOO_Status()
        # Latest PPST
        self.ppstmax = None
        # Observations
        self._observations = Swift_Observations()

        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        # See if we pass validation from the constructor, but don't record
        # errors if we don't
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    @property
    def _table(self):
        if len(self.entries) > 0:
            header = self.entries[0]._table[0]
        else:
            header = []
        return header, [ppt._table[1][0] for ppt in self]

    @property
    def observations(self):
        if len(self.entries) > 0 and len(self._observations.keys()) == 0:
            for q in self.entries:
                self._observations[q.obsnum] = Swift_Observation()
            _ = [self._observations[q.obsnum].append(q) for q in self.entries]
        return self._observations

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def validate(self):
        '''Make sure that all parameters required for a valid request are
        passed'''
        # How many search keys? Require at least one
        keys = self.api_data.keys()

        # We need at least one of these keys to be submitted
        req_keys = ['begin',
                    'ra',
                    'dec',
                    'targetid',
                    'obsnum']

        # Check how many of them are in the request
        total_keys = 0
        for key in keys:
            if key in req_keys:
                if self.api_data[key]:
                    total_keys += 1

        # We need at least one key to be set
        if total_keys == 0:
            self.status.error("ERROR: Please supply search parameters to narrow search.")
            return False

        # Check if ra or dec are in keys, we have both.
        if 'ra' in keys or 'dec' in keys:
            if not ('ra' in keys and 'dec' in keys):
                self.status.error("ERROR: Must supply both RA and Dec.")
                return False

        return True


# Class aliases
Swift_PlanQuery = Swift_PPST
PlanQuery = Swift_PPST
PPST = Swift_PPST

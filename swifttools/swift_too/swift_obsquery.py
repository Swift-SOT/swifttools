from .common import TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_SkyCoord, TOOAPI_ObsID, TOOAPI_Instruments
from .too_status import Swift_TOO_Status
from datetime import timedelta
from .swift_resolve import TOOAPI_AutoResolve


class Swift_AFST_Entry(TOOAPI_Baseclass, TOOAPI_SkyCoord, TOOAPI_ObsID, TOOAPI_Instruments):
    '''Class that defines an individual entry in the Swift As-Flown Timeline

    Attributes
    ----------
    begin : datetime
        begin time of observation
    settle : datetime
        settle time of the observation
    end : datetime
        end time of observation
    slewtime : timedelta
        slew time of the observation
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
    ra_object : float
        RA of the object that is the target of the pointing
    dec_object : float
        dec of the object that is the target of the pointing
    targname : str
        Target name of the primary target of the observation
    '''
    # API core definition
    _parameters = ['begin', 'settle', 'end', 'ra', 'dec', 'roll', 'targname', 'targetid',
                   'seg', 'ra_point', 'dec_point', 'xrt', 'uvot', 'bat', 'fom', 'obstype']
    _attributes = []
    # Variable names
    names = ['Begin Time', 'Settle Time', 'End Time', 'RA(J2000)', 'Dec(J200)',
             'Roll (deg)', 'Target Name', 'Target ID', 'Segment', 'Object RA(J2000)',
             'Object Dec(J2000)', 'XRT Mode', 'UVOT Mode', 'BAT Mode', 'Figure of Merit',
             'Observation Type']
    # API name
    api_name = "Swift_AFST_Entry"

    def __init__(self):
        # Attributes of the class and their descriptions
        self.varnames = dict()
        for i in range(len(self._parameters)):
            self.varnames[self._parameters[i]] = self.names[i]
        self.varnames['obsnum'] = 'Observation Number'
        self.varnames['exposure'] = 'Exposure (s)'
        self.varnames['slewtime'] = 'Slewtime (s)'
        self.varnames['ra_object'] = self.varnames['ra_point']
        self.varnames['dec_object'] = self.varnames['dec_point']

        # Attributes
        self.begin = None
        self.settle = None
        self.end = None
        self.ra = None
        self.dec = None
        self.ra_object = None
        self.dec_object = None
        self.roll = None
        self.targname = None
        self.targetid = None
        self.seg = None
        self.status = Swift_TOO_Status()
        self._subclasses = [Swift_TOO_Status]
        # Instrument config
        self._xrt = None
        self._uvot = None
        # Swift_AFST returns a bunch of stuff we don't care about, so just take the things we do
        self.ignorekeys = True

    @property
    def exposure(self):
        return self.end - self.settle

    @property
    def slewtime(self):
        return self.settle - self.begin

    # The following provides compatibility as we changed ra/dec_point to
    # ra/dec_object. These will go away with a future API update.
    @property
    def ra_point(self):
        return self.ra_object

    @ra_point.setter
    def ra_point(self, ra):
        self.ra_object = ra

    @property
    def dec_point(self):
        return self.dec_object

    @dec_point.setter
    def dec_point(self, dec):
        self.dec_object = dec
    # Compat end

    @property
    def _table(self):
        _parameters = ['begin', 'end', 'targname', 'obsnum', 'exposure', 'slewtime']
        header = [self.varnames[row] for row in _parameters]
        return header, [[self.begin, self.end, self.targname, self.obsnum, self.exposure.seconds, self.slewtime.seconds]]


class Swift_Observation(TOOAPI_Baseclass):
    '''Class to summarize observations taken for given observation ID (obsnum).
    Whereas observations are typically one or more individual snapshot, in TOO
    API speak a `Swift_AFST_Entry`, this class summarizes all snapshots into a
    single begin time, end time. Note that as ra/dec varies between each
    snapshot, only `ra_object`, `dec_object` are given as coordinates.

    Attributes
    ----------
    begin : datetime
        begin time of observation
    settle : datetime
        settle time of the observation
    end : datetime
        end time of observation
    slewtime : timedelta
        slew time of the observation
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
    ra_object : float
        RA of the object that is the target of the pointing
    dec_object : float
        dec of the object that is the target of the pointing
    targname : str
        Target name of the primary target of the observation
    '''
    # Core API definitions
    api_name = "Swift_Observation"
    _parameters = ['begin', 'end', 'targname', 'targetid', 'seg',
                   'ra_object', 'dec_object', 'xrt', 'uvot', 'bat', 'entries']

    def __init__(self):
        # All the Swift_AFST_Entries for this observation
        self.entries = Swift_AFST()

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def append(self, value):
        self.entries.append(value)

    def extend(self, value):
        self.entries.extend(value)

    @property
    def targetid(self):
        return self.entries[0].targetid

    @property
    def seg(self):
        return self.entries[0].seg

    @property
    def obsnum(self):
        return self.entries[0].obsnum

    @property
    def targname(self):
        return self.entries[0].targname

    @property
    def ra_object(self):
        if hasattr(self.entries[0], 'ra_object'):
            return self.entries[0].ra_object

    @property
    def dec_object(self):
        if hasattr(self.entries[0], 'dec_object'):
            return self.entries[0].dec_object

    @property
    def exposure(self):
        return timedelta(seconds=sum([e.exposure.seconds for e in self.entries]))

    @property
    def slewtime(self):
        return timedelta(seconds=sum([e.slewtime.seconds for e in self.entries]))

    @property
    def begin(self):
        return min([q.begin for q in self.entries])

    @property
    def end(self):
        return max([q.end for q in self.entries])

    @property
    def xrt(self):
        return self.entries[0].xrt

    @property
    def uvot(self):
        return self.entries[0].uvot

    @property
    def bat(self):
        return self.entries[0].bat

    @property
    def snapshots(self):
        return self.entries

    # The following provides compatibility as we changed ra/dec_point to
    # ra/dec_object. These will go away in the next version of the API (1.3).
    @property
    def ra_point(self):
        return self.ra_object

    @ra_point.setter
    def ra_point(self, ra):
        self.ra_object = ra

    @property
    def dec_point(self):
        return self.dec_object

    @dec_point.setter
    def dec_point(self, dec):
        self.dec_object = dec
    # Compat end

    @property
    def _table(self):
        if len(self.entries) > 0:
            header = self.entries[0]._table[0]
        else:
            header = []
        return header, [[self.begin, self.end, self.targname, self.obsnum, self.exposure.seconds, self.slewtime.seconds]]


class Swift_Observations(dict, TOOAPI_Baseclass):
    '''Adapted dictionary class for containing observations that mostly is just
    to ensure that data can be displayed in a consistent format. Key is
    typically the Swift Observation ID in SDC format (e.g. '00012345012').'''

    @property
    def _table(self):
        if len(self.values()) > 0:
            header = list(self.values())[0]._table[0]
        else:
            header = []
        return header, [self[obsid]._table[1][0] for obsid in self.keys()]


class Swift_AFST(TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_SkyCoord, TOOAPI_ObsID, TOOAPI_AutoResolve):
    '''Class to fetch Swift As-Flown Science Timeline (AFST) for given
    constraints. Essentially this will return what Swift observed and when, for
    given constraints. Constraints can be for give coordinate (SkyCoord or J2000
    RA/Dec) and radius (in degrees), a given date range, or a given target ID
    (targetid) or Observation ID (obsnum).

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
    afstmax: datetime
        When is the AFST valid up to
    '''
    # Define API name
    api_name = "Swift_AFST"
    # Contents of the _parameters
    _parameters = ['username', 'begin', 'end', 'ra',
                   'dec', 'radius', 'targetid', 'obsnum']
    _local = ['obsid', 'name', 'skycoord', 'length', 'target_id']
    _attributes = ['status', 'afstmax', 'entries']
    # Acceptable classes that be part of this class
    _subclasses = [Swift_AFST_Entry, Swift_TOO_Status]

    def __init__(self, *args, **kwargs):
        '''
        Parameters
        ----------
        begin : datetime
            begin time of window
        end : datetime
            end time of window
        length : timedelta
            length of window
        ra : float
            Right Ascension of target in J2000 (decimal degrees)
        dec : float
            Declination of target in J2000 (decimal degrees)
        skycoord : SkyCoord
            SkyCoord version of RA/Dec if astropy is installed
        radius : float
            radius in degrees to search around (default 0.197)
        targetid : int
            target ID of target
        obsid : int / str
            Observation ID of target, either in spacecraft (int) or SDC (str)
            formats
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        '''

        # Coordinate search
        self.ra = None
        self.dec = None
        self.radius = 11.8/60  # Default 11.8 arcmin - XRT FOV

        # Search on targetid/obsnum
        self.targetid = None
        self.obsnum = None

        # Login
        self.username = 'anonymous'
        # AFST entries go here
        self.entries = list()
        # Status of request
        self.status = Swift_TOO_Status()

        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        # AFST maximum date
        self.afstmax = None

        # Observations
        self._observations = Swift_Observations()

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

    def append(self, value):
        self.entries.append(value)

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


# Alias names for class
Swift_ObsQuery = Swift_AFST
ObsQuery = Swift_AFST
AFST = Swift_AFST

from .common import TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_SkyCoord, TOOAPI_ObsID, xrtmodes
from .too_status import Swift_TOO_Status
from .swift_obsquery import Swift_Observation,Swift_Observations
from datetime import timedelta

class Swift_PPST_Entry(TOOAPI_Baseclass,TOOAPI_SkyCoord,TOOAPI_ObsID):
    '''Class that defines an individual entry in the Swift Pre-Planned Science
    Timeline'''
    def __init__(self):
        TOOAPI_Baseclass.__init__(self)
        TOOAPI_SkyCoord.__init__(self)
        TOOAPI_ObsID.__init__(self)
        self.api_name = "Swift_PPST_Entry"
        # Entries
        self.rows = ['begin', 'end', 'targname', 'ra', 'dec', 'roll', 'targetid', 'seg', 'xrt', 'uvot', 'bat', 'fom']
        self.names =['Begin Time','End Time','Target Name','RA(J2000)','Dec(J200)','Roll (deg)','Target ID','Segment','XRT Mode','UVOT Mode','BAT Mode','Figure of Merit']
        self.varnames = dict()
        for i in range(len(self.rows)):
            self.varnames[self.rows[i]] = self.names[i]
        self.varnames['obsnum'] = 'Observation Number'
        self.varnames['exposure'] = 'Exposure (s)'
        self.varnames['slewtime'] = 'Slewtime (s)'
        self.extrarows = []
        self.begin = None
        #self.settle = None
        self.end = None
        self.ra = None
        self.dec = None
        self.roll = None
        self.targname = None
        self.targetid = None
        self.seg = None
        self.slewtime = timedelta(0) # Slewtime isn't reported in plans
        self.status = Swift_TOO_Status()
        self.subclasses = [Swift_TOO_Status]
        # Instrument config
        self._xrt = None
        self._uvot = None
        # Swift_PPST returns a bunch of stuff we don't care about, so just take the things we do
        self.ignorekeys = True

    # Instrument modes
    @property
    def xrt(self):
        '''Given a XRT mode number returns a string containing the name of the
        mode'''
        return xrtmodes[self._xrt]

    @xrt.setter
    def xrt(self,mode):
        self._xrt = mode

    @property
    def uvot(self):
        '''Given a XRT mode number returns a string containing the name of the
        mode'''
        return f"0x{self._uvot:04x}"

    @uvot.setter
    def uvot(self,mode):
        self._uvot = mode

    @property
    def exposure(self):
        return self.end - self.begin

    @property
    def table(self):
        rows = ['begin','end','targname','obsnum','exposure']
        header = [self.varnames[row] for row in rows]
        return header,[[self.begin,self.end, self.targname, self.obsnum, self.exposure.seconds]]



class Swift_PPST(TOOAPI_Baseclass,TOOAPI_Daterange,TOOAPI_SkyCoord,TOOAPI_ObsID):
    '''Class to fetch Swift Pre-Planned Science Timeline (PPST) for given
    constraints. Essentially this will return what Swift was planned to observe
    and when, for given constraints. Constraints can be for give coordinate
    (SkyCoord or J2000 RA/Dec) and radius (in degrees), a given date range, or a
    given target ID (targetid) or Observation ID (obsnum).'''
    def __init__(self,username='anonymous',shared_secret=None,ra=None,dec=None,begin=None,end=None,targetid=None,obsnum=None,radius=0.1967,length=None):
        TOOAPI_Baseclass.__init__(self)
        TOOAPI_Daterange.__init__(self)
        TOOAPI_SkyCoord.__init__(self)
        # Define API name
        self.api_name = "Swift_PPST"
        # Coordinate search
        self.ra = ra
        self.dec = dec
        self.radius = radius # Default 11.8 arcmin - XRT FOV
        # begin and end boundaries        
        self.begin = begin
        self.end = end
        self.length = length
        # Search on targetid/obsnum
        self.targetid = targetid
        self.obsnum = obsnum
        # Login
        self.username = username
        if shared_secret != None:
            self.shared_secret = shared_secret
        # PPST entries go here
        self.entries = list()
        # Status of request
        self.status = Swift_TOO_Status()
        # Contents of the rows
        self.rows = ['username','begin','end','ra','dec','radius','targetid','obsnum']
        self.extrarows = ['status','ppstmax','entries']
        self.trans_name = dict()
        # Acceptable classes that be part of this class
        self.subclasses = [Swift_PPST_Entry,Swift_TOO_Status]
        # Latest PPST
        self.ppstmax = None
        # Observations
        self._observations = Swift_Observations()
        if self.ra != None or self.begin != None or targetid != None or obsnum != None:
            self.submit()

    @property
    def table(self):
        header = self.entries[0].table[0]
        return header,[ppt.table[1][0] for ppt in self]

    @property
    def observations(self):
        if len(self.entries) > 0 and len(self._observations.keys()) == 0:
            for q in self.entries:
                self._observations[q.obsnum] = Swift_Observation()
            _ = [self._observations[q.obsnum].append(q) for q in self.entries]
        return self._observations

    def __getitem__(self,index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def validate(self):
        # Check username and shared_secret are set
        if not self.username or not self.shared_secret:
            print(f"{self.__class__.__name__} ERROR: username and shared_secret parameters need to be supplied.")
            return None
        
        # How many search keys? Require at least one
        keys = self.api_data.keys()
        
        # We need one of these keys to be submitted
        req_keys = ['begin','end','ra','dec','radius','targetid','obsnum']
        
        # Check how many of them are in the request
        total_keys = 0
        for key in keys:
            if key in req_keys:
                if self.api_data[key]:
                    total_keys += 1

        # We need at least one key to be set
        if total_keys == 0:
            print("ERROR: Please supply search parameters to narrow search.")
            return None

        # Check if ra or dec are in keys, we have both.
        if 'ra' in keys or 'dec' in keys:
            if not ('ra' in keys and 'dec' in keys):
                print("ERROR: Must supply both RA and Dec.")
                return None

        return True

Swift_PlanQuery = Swift_PPST

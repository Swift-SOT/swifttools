from .common import TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_SkyCoord, TOOAPI_ObsID, xrtmodes
from .too_status import Swift_TOO_Status
from datetime import timedelta


class Swift_AFST_Entry(TOOAPI_Baseclass,TOOAPI_SkyCoord,TOOAPI_ObsID):
    '''Class that defines an individual entry in the Swift As-Flown Timeline'''
    def __init__(self):
        TOOAPI_Baseclass.__init__(self)
        TOOAPI_SkyCoord.__init__(self)
        TOOAPI_ObsID.__init__(self)
        self.api_name = "Swift_AFST_Entry"
        # Attributes of the class and their descriptions
        self.rows = ['begin','settle','end','ra','dec','roll','targname','targetid','seg','ra_point','dec_point','xrt','uvot','bat','fom','obstype']
        self.names =['Begin Time','Settle Time','End Time','RA(J2000)','Dec(J200)','Roll (deg)','Target Name','Target ID','Segment','Object RA(J2000)','Object Dec(J2000)','XRT Mode','UVOT Mode','BAT Mode','Figure of Merit','Observation Type']
        self.varnames = dict()
        for i in range(len(self.rows)):
            self.varnames[self.rows[i]] = self.names[i]
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
        self.subclasses = [Swift_TOO_Status]
        # Instrument config
        self._xrt = None
        self._uvot = None
        # Swift_AFST returns a bunch of stuff we don't care about, so just take the things we do
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
        return self.end - self.settle

    @property
    def slewtime(self):
        return self.settle - self.begin

    ## The following provides compatibility as we changed ra/dec_point to ra/dec_object. These will go away with a future API update.
    @property
    def ra_point(self):
        return self.ra_object
    
    @ra_point.setter
    def ra_point(self,ra):
        self.ra_object = ra

    @property
    def dec_point(self):
        return self.dec_object

    @dec_point.setter
    def dec_point(self,dec):
        self.dec_object = dec
    ## Compat end 

    @property
    def table(self):
        rows = ['begin','end','targname','obsnum','exposure','slewtime']
        header = [self.varnames[row] for row in rows]
        return header,[[self.begin,self.end, self.targname, self.obsnum, self.exposure.seconds, self.slewtime.seconds]]



class Swift_Observation(TOOAPI_Baseclass):
    '''Class to summarize observations taken for given observation ID (obsnum).
    Whereas observations are typically one or more individual snapshot, in TOO
    API speak a `Swift_AFST_Entry`, this class summarizes all snapshots into a
    single begin time, end time. Note that as ra/dec varies between each
    snapshot, only `ra_object`, `dec_object` are given as coordinates. '''
    def __init__(self):
        TOOAPI_Baseclass.__init__(self)
        self.api_name = "Swift_Observation"
        # All the Swift_AFST_Entries for this observation
        self.entries = Swift_AFST()
        self.rows = ['begin','end','targname','targetid','seg','ra_object','dec_object','xrt','uvot','entries']
        self.extrarows = []

    def __getitem__(self,index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)        

    def append(self,value):
        self.entries.append(value)

    def extend(self,value):
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
    def snapshots(self):
        return self.entries

    ## The following provides compatibility as we changed ra/dec_point to ra/dec_object. These will go away in the next version of the API (1.3).
    @property
    def ra_point(self):
        return self.ra_object
    
    @ra_point.setter
    def ra_point(self,ra):
        self.ra_object = ra

    @property
    def dec_point(self):
        return self.dec_object

    @dec_point.setter
    def dec_point(self,dec):
        self.dec_object = dec
    ## Compat end

    @property
    def table(self):
        if len(self.entries) > 0:
            header = self.entries[0].table[0]
        else:
            header = []
        return header,[[self.begin, self.end, self.targname, self.obsnum, self.exposure.seconds, self.slewtime.seconds]]


class Swift_Observations(dict,TOOAPI_Baseclass):
    '''Adapted dictionary class for containing observations that mostly is just
    to ensure that data can be displayed in a consistent format. Key is
    typically the Swift Observation ID in SDC format (e.g. '00012345012').'''

    @property
    def table(self):
        if len(self.values()) > 0:
            header = list(self.values())[0].table[0]
        else:
            header = []
        return header,[self[obsid].table[1][0] for obsid in self.keys()]


class Swift_AFST(TOOAPI_Baseclass,TOOAPI_Daterange,TOOAPI_SkyCoord,TOOAPI_ObsID):
    '''Class to fetch Swift As-Flown Science Timeline (AFST) for given
    constraints. Essentially this will return what Swift observed and when, for
    given constraints. Constraints can be for give coordinate (SkyCoord or J2000
    RA/Dec) and radius (in degrees), a given date range, or a given target ID
    (targetid) or Observation ID (obsnum).'''
    def __init__(self,username='anonymous',shared_secret=None,ra=None,dec=None,begin=None,end=None,targetid=None,obsnum=None,radius=0.1967,length=None):
        TOOAPI_Baseclass.__init__(self)
        TOOAPI_Daterange.__init__(self)
        TOOAPI_ObsID.__init__(self)
        self.api_name = "Swift_AFST"
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
        # AFST entries go here
        self.entries = list()
        # Status of request
        self.status = Swift_TOO_Status()
        # AFST maximum date
        self.afstmax = None
        # Contents of the rows
        self.rows = ['username','begin','end','ra','dec','radius','targetid','obsnum']
        self.extrarows = ['status','afstmax','entries']
        self.trans_name = dict()
        # Acceptable classes that be part of this class
        self.subclasses = [Swift_AFST_Entry,Swift_TOO_Status]
        # Observations
        self._observations = Swift_Observations()
        if self.ra != None or self.begin != None or targetid != None or obsnum != None:
            self.submit()

    @property
    def table(self):
        if len(self.entries) > 0:
            header = self.entries[0].table[0]
        else:
            header = []
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

    def append(self,value):
        self.entries.append(value)

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


# Alias name for class
Swift_ObsQuery = Swift_AFST

from .common import TOOAPI_Baseclass,xrtmodes
from .too_status import Swift_TOO_Status
from .swift_obsquery import Swift_Observation,Swift_Observations
from datetime import timedelta
from tabulate import tabulate
import re

xrtmodes = {0: "Auto", 1: "Null", 2: "ShortIM", 3: "LongIM", 4: "PUPD", 5: "LRPD", 6: "WT", 7: "PC", 8: "Raw", 9: "Bias"}
modesxrt = {"Auto": 0, "Null": 1, "ShortIM": 2, "LongIM": 3, "PUPD":4, "LRPD": 5 , "WT": 6, "PC": 7, "Raw": 8, "Bias": 9}


class Swift_PPST_Entry(TOOAPI_Baseclass):
    '''Class that defines an individual entry in the Swift Pre-Planned Science Timeline'''
    def __init__(self):
        TOOAPI_Baseclass.__init__(self)
        self.api_name = "Swift_PPST_Entry"
        # Entries
        self.rows = ['begin', 'end', 'targname', 'ra', 'dec', 'roll', 'targetid', 'seg', 'bat', 'xrt', 'uvot', 'fom']
        self.extrarows = []
        self.begin = None
        #self.settle = None
        self.end = None
        self.ra = None
        self.dec = None
        self.ra_point = None
        self.dec_point = None
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
        """Given a XRT mode number returns a string containing the name of the
        mode"""
        return xrtmodes[self._xrt]

    @xrt.setter
    def xrt(self,mode):
        self._xrt = mode

    @property
    def uvot(self):
        """Given a XRT mode number returns a string containing the name of the
        mode"""
        return f"0x{self._uvot:04x}"

    @uvot.setter
    def uvot(self,mode):
        self._uvot = mode

    # Handle the two different ways of reporting Observation number. Default to the SDC style of a string with leading zeros
    @property
    def obsnum(self):
        '''Return the obsnum in SDC format'''
        return f"{self.targetid:08d}{self.seg:03d}"
    
    @property 
    def obsnumsc(self):
        '''Return the obsnum in spacecraft format'''
        return self.targetid + (self.seg<<24)
    
    @obsnum.setter
    def obsnum(self,obsnum):
        '''Set the obsnum value, by figuring out what the two formats are.'''
        # Is this Spacecraft format?
        if type(obsnum) == int:
            self.targetid = obsnum & 0xffffff
            self.seg = obsnum >> 24
        # Is it SDC format?
        elif type(obsnum) == str:
            print("obsnum:",obsnum)
            self.targetid = int(obsnum[0:8])
            self.seg = int(obsnum[8:11])
        else:
            raise Exception("Observation number not in recognised format")

    @property
    def exposure(self):
        return self.end - self.begin

    @property
    def table(self):
        return [self.begin,self.end, self.targname, self.obsnum, self.exposure.seconds]

    def _repr_html_(self):
        if self.table == []:
            return "No data"
        else:
            return tabulate([self.table],['Begin','End','Name','Obs Number','Exposure (s)'],tablefmt='html',stralign='right').replace('right','left')
    
    def __str__(self):
        if self.table == []:
            return "No data"
        else:
            return tabulate([self.table],['Begin','End','Name','Obs Number','Exposure (s)'],tablefmt='pretty',stralign='right')


class Swift_PPST(TOOAPI_Baseclass):
    '''Class to fetch Swift Pre-Planned Science Timeline (PPST) for given constraints. Essentially this will
    return what Swift was planned to observe and when, for given constraints. Constraints can be for give coordinate
    (SkyCoord or J2000 RA/Dec) and radius (in degrees), a given date range, or a given target ID (targetid) 
    or Observation ID (obsnum).'''
    def __init__(self,username=None,shared_secret=None,ra=None,dec=None,begin=None,end=None,targetid=None,obsnum=None,radius=0.1967):
        TOOAPI_Baseclass.__init__(self)
        self.api_name = "Swift_PPST"
        # Coordinate search
        self._skycoord = None
        self.ra = ra
        self.dec = dec
        self.radius = radius # Default 11.8 arcmin - XRT FOV
        # begin and end boundaries        
        self.begin = begin
        self.end = end
        # Search on targetid/obsnum
        self.targetid = targetid
        self._obsnum = None
        self.obsnum = obsnum
        # Login
        self.username = username
        self.shared_secret = shared_secret
        # PPST entries go here
        self.entries = list()
        # Status of request
        self.status = Swift_TOO_Status()
        # Contents of the rows
        self.rows = ['username','begin','end','ra','dec','radius','targetid','obsnum','ppstmax','entries']
        self.extrarows = ['status']
        self.trans_name = dict()
        # Acceptable classes that be part of this class
        self.subclasses = [Swift_PPST_Entry,Swift_TOO_Status]
        # Latest PPST
        self.ppstmax = None
        # Observations
        self._observations = Swift_Observations()
        if self.username != None:
            self.submit()

    def __str__(self):
        values = [f"{row}={getattr(self,row)}" for row in self.rows if row != "entries"]
        return f"{[val for val in values if 'None' not in val]}"
    
    def __repr__(self):
        return f"<{self.__str__()}>"

    @property
    def obsnum(self):
        return self._obsnum

    @obsnum.setter
    def obsnum(self,obsnum):
        '''Allow obsnum to be specified in Spacecraft (int) or SDC format (string)'''
        if type(obsnum) == str:
            if re.match("^[0-9]{11}?$",obsnum) == None:
                print("ERROR: Obsnum string format incorrect")
            else:
                targetid = int(obsnum[0:8])
                segment = int(obsnum[8:12])
                self._obsnum = targetid + (segment<<24)
        elif type(obsnum) == int:
            self._obsnum = obsnum
        elif obsnum == None:
            self._obsnum = None
        else:
            print(f"ERROR: Obsnum format wrong")
    
    @property
    def table(self):
        return [ppt.table for ppt in self]

    def _repr_html_(self):
        if self.table == []:
            return "No data"
        else:
            return tabulate(self.table,['Begin','End','Name','Obs Number','Exposure (s)'],tablefmt='html',stralign='right').replace('right','left')
    
    def __str__(self):
        if self.table == []:
            return "No data"
        else:
            return tabulate(self.table,['Begin','End','Name','Obs Number','Exposure (s)'],tablefmt='pretty',stralign='right')


    @property
    def observations(self):
        if len(self.entries) > 0 and len(self._observations.keys()) == 0:
            for q in self.entries:
                self._observations[q.obsnum] = Swift_Observation()
            _ = [self._observations[q.obsnum].append(q) for q in self.entries]
        return self._observations

    @property 
    def skycoord(self): 
        # Check if the RA/Dec match the SkyCoord, and if they don't modify the skycoord
        if type(self._skycoord).__module__ == 'astropy.coordinates.sky_coordinate':
            if self.ra != self._skycoord.fk5.ra.deg or self.dec != self._skycoord.fk5.dec.deg:
                self._skycoord = self._skycoord.__class__(self.ra,self.dec,unit="deg",frame="fk5")
        return self._skycoord

    @skycoord.setter
    def skycoord(self,sc):
        if type(sc).__module__ == 'astropy.coordinates.sky_coordinate':
            self._skycoord = sc
            self.ra = sc.fk5.ra.deg
            self.dec = sc.fk5.dec.deg
        else:
            raise Exception("Needs to be assigned an astropy SkyCoord")

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

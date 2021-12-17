from .common import TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_SkyCoord
from .too_client import Swift_TOO_Request
from .too_status import Swift_TOO_Status
from .swift_calendar import Swift_Calendar,Swift_Calendar_Entry

class Swift_TOO_Requests(TOOAPI_Baseclass,TOOAPI_Daterange,TOOAPI_SkyCoord):
    '''Class used to obtain details about previous TOO requests.'''
    def __init__(self,username='anonymous',shared_secret=None,limit=10,year=None,detail=False,too_id=None,ra=None,dec=None,radius=11.6/60,skycoord=None,begin=None,end=None,length=None):
        TOOAPI_Baseclass.__init__(self)
        TOOAPI_Daterange.__init__(self)
        TOOAPI_SkyCoord.__init__(self)
        # Required Parameters
        self.rows = ['username','too_id','limit','year','detail','ra','dec','radius','begin','length']
        # Optional Parameters and things returned
        self.extrarows = ['entries','status']

        # Set up login values
        self.username = username
        if shared_secret != None:
            self.shared_secret = shared_secret

        # Parameter values
        self.year = year             # TOOs for a specific year
        self.detail = detail         # Return detailed information (only returns your TOOs)
        self.limit =  limit          # Limit the number of returned TOOs. Default limit is 10.
        self.too_id = too_id         # Request a TOO of a specific TOO ID number
        self.ra = ra                 # Search on RA / Dec
        self.dec = dec               # Default radius is 11.6 arc-minutes
        self.radius = radius         # which is the XRT FOV.
        self.skycoord  = skycoord    # SkyCoord support in place of RA/Dec
        self.begin = begin           # Date range parameters Begin
        self.end = end               # End
        self.length = length         # and length.
        # Request status      
        self.status = Swift_TOO_Status()     # 

        # Results
        self.entries = list()

        # Returned classes
        self.subclasses = [Swift_TOO_Request,Swift_TOO_Status,Swift_Calendar,Swift_Calendar_Entry]

        # Run if any argument given
        if (self.ra != None and self.dec != None) or self.year != None or self.too_id != None or self.begin != None or self.length != None:
            self.submit()

    def __getitem__(self,index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def by_id(self,too_id):
        return {t.too_id:t for t in self.entries}[too_id]

    def validate(self):
        if self.username != None and self.shared_secret != None and self.shared_secret != '':
            return True
        else:
            return False

    @property
    def table(self):
        table_cols = ['too_id','source_name','instrument','ra','dec','uvot_mode_approved','xrt_mode_approved','timestamp','l_name','urgency','date_begin','date_end','target_id']
        if len(self.entries) > 0:
            header = [self.entries[0].varnames[col] for col in table_cols]
        else:
            header = []
        t = list()
        for e in self.entries:
            t.append([getattr(e,col) for col in table_cols])
        return header,t
            
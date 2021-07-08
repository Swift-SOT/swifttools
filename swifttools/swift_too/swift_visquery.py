from .too_status import Swift_TOO_Status
from .common import TOOAPI_Baseclass
from datetime import datetime,timedelta
from tabulate import tabulate
import textwrap
class Swift_VisWindow(TOOAPI_Baseclass):
    '''Simple class to define a Visibility window. Begin and End of window can either be accessed as self.begin 
    or self.end, or as self[0] or self[1].'''
    def __init__(self):
        TOOAPI_Baseclass.__init__(self)
        self.api_name = "Swift_VisWindow"
        self.begin = None
        self.end = None
        self.status = Swift_TOO_Status()
        self.rows = ['begin','end']
        
    def __str__(self):
        return f"{self.begin} - {self.end} ({self.end - self.begin})"

    def __getitem__(self,index):
        if index == 0:
            return self.begin
        elif index == 1:
            return self.end
        else:
            raise IndexError('list index out of range')

class Swift_VisQuery(TOOAPI_Baseclass):
    '''Request Swift Target visibility windows. These results are low-fidelity, so do not give orbit-to-orbit 
    visibility, but instead long term windows indicates when a target is observable by Swift and not in a 
    Sun/Moon/Pole constraint.'''
    def __init__(self,username=None,shared_secret=None,ra=None,dec=None,begin=None,length=1,end=None,hires=False):
        TOOAPI_Baseclass.__init__(self)
        self.api_name = "Swift_VisQuery"
        # User arguments
        self.ra = ra
        self.dec = dec
        self.length = length
        self.hires = hires
        # Start and end boundaries        
        self.begin = begin
        if self.begin == None:
            self.begin = datetime.utcnow()
        if end != None:
            self.end = end
        self.username = username
        self.shared_secret = shared_secret
        # Internal variable
        self._skycoord = None
        # Visibility windows go here
        self.windows = list()
        # Status of request
        self.status = Swift_TOO_Status()
        # Contents of the rows
        self.rows = ['username','ra','dec','begin','length','hires','windows']
        self.extrarows = ['status']
        # Subclasses
        self.subclasses = [Swift_TOO_Status,Swift_VisWindow]
        if username != None and self.status == "Unknown":
            self.submit()

    # Alias start as begin
    @property
    def begin(self):
        return self.start

    @begin.setter
    def begin(self,begin):
        self.start = begin

    @property 
    def end(self):
        return self.begin + timedelta(days=self.length)

    @end.setter
    def end(self,enddt):
        self.length = (enddt - self.begin).days

    @property
    def table(self):
        return [[win.begin,win.end,win.end-win.begin] for win in self.windows]

    def __str__(self):
        return tabulate(self.table,['Begin','End','Length'],tablefmt='pretty')

    def _repr_html_(self):
        return tabulate(self.table,['Begin','End','Length'],tablefmt='html',stralign='right').replace('right','left')

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
            raise Exception("Needs to be assigned an Astropy SkyCoord")


    def __getitem__(self,index):
        return self.windows[index]
    
    def __len__(self):
        return len(self.windows)
    
    def validate(self):
        # Check username and shared_secret are set
        if not self.username or not self.shared_secret:
            print(f"{self.__class__.__name__} ERROR: username and shared_secret parameters need to be supplied.")
            return False

        # How many search keys? Require at least one
        keys = self.api_data.keys()

        # We need one of these keys to be submitted
        req_keys = ['begin','length']

        # Check how many of them are in the request
        total_keys = 0
        for key in keys:
            if key in req_keys:
                total_keys += 1

        if 'ra' not in keys or 'dec' not in keys:
            print("ERROR: Must supply RA and Dec of object.")
            return False

        if total_keys == 0:
            print("ERROR: Please supply search parameters to narrow search.")
            return False

        
        return True

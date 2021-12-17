from .too_status import Swift_TOO_Status
from .common import TOOAPI_Baseclass, TOOAPI_Daterange, TOOAPI_SkyCoord

class Swift_VisWindow(TOOAPI_Baseclass):
    '''Simple class to define a Visibility window. Begin and End of window can
    either be accessed as self.begin or self.end, or as self[0] or self[1].'''
    def __init__(self):
        TOOAPI_Baseclass.__init__(self)
        self.api_name = "Swift_VisWindow"
        self.begin = None
        self.end = None
        self.status = Swift_TOO_Status()
        self.rows = ['begin','end','length']
        self.varnames = {'begin':'Begin Time','end':'End Time','length':'Window length'}
        
    @property
    def length(self):
        if self.end == None or self.begin == None:
            return None
        return self.end - self.begin

    @property
    def table(self):
        header = [self.varnames[row] for row in self.rows]
        return header,[[self.begin,self.end, self.length]]

    def __str__(self):
        return f"{self.begin} - {self.end} ({self.length})"

    def __getitem__(self,index):
        if index == 0:
            return self.begin
        elif index == 1:
            return self.end
        else:
            raise IndexError('list index out of range')

class Swift_VisQuery(TOOAPI_Baseclass,TOOAPI_Daterange,TOOAPI_SkyCoord):
    '''Request Swift Target visibility windows. These results are low-fidelity,
    so do not give orbit-to-orbit visibility, but instead long term windows
    indicates when a target is observable by Swift and not in a Sun/Moon/Pole
    constraint.'''
    def __init__(self,username='anonymous',shared_secret=None,ra=None,dec=None,begin=None,length=1,end=None,hires=False):
        TOOAPI_Baseclass.__init__(self)
        TOOAPI_Daterange.__init__(self)
        TOOAPI_SkyCoord.__init__(self)
        self.api_name = "Swift_VisQuery"
        # User arguments
        self.ra = ra
        self.dec = dec
        self._length = None
        self.length = length
        self.hires = hires
        # Start and end boundaries        
        self.begin = begin
        self.end = end
        # Username/Secret stuff
        self.username = username
        if shared_secret != None:
            self.shared_secret = shared_secret
        # Visibility windows go here
        self.windows = list()
        # Status of request
        self.status = Swift_TOO_Status()
        # Contents of the rows
        self.rows = ['username','ra','dec','begin','length','hires']
        self.extrarows = ['status','windows']
        # Subclasses
        self.subclasses = [Swift_TOO_Status,Swift_VisWindow]
        if ra != None and self.status == "Unknown":
            self.submit()

    @property
    def table(self):
        if len(self.windows) != 0:
            header = self.windows[0].table[0]
        else:
            header = []
        return header,[win.table[1][0] for win in self.windows]

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

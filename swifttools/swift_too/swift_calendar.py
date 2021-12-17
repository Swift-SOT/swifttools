from .common import TOOAPI_Baseclass, xrtmodes
from .too_status import Swift_TOO_Status

class Swift_Calendar_Entry(TOOAPI_Baseclass):
    '''Class for a single entry in the Swift TOO calendar'''
    def __init__(self):
        TOOAPI_Baseclass.__init__(self)
        self.api_name = "Swift_Calendar_Entry"
        self.start = None     # Start and end times of the observing window. Use datetime for coordinated window
        self.stop = None      # and timedelta for relative offsets, where the start time can be variable, but the monitoring cadence isn't even.
        self._xrt_mode = None  # Only set instrument modes if they differ from the mode
        self.bat_mode = None  # ditto
        self._uvot_mode = None # ditto
        self.duration = None  # Exposure time in seconds
        self.asflown = None   # Amount of exposure taken
        self.ignorekeys = True
        # Define the names of the database rows
        self.rows = ['start', 'stop', 'xrt_mode', 'bat_mode', 'uvot_mode','duration','asflown']
        self.names = ['Start','Stop','XRT Mode','BAT Mode','UVOT Mode','Exposure (s)','AFST (s)']
        self.varnames = dict()
        for i in range(len(self.rows)):
            self.varnames[self.rows[i]] = self.names[i]

    def __getitem__(self,key):
        if key in self.rows:
            return eval(f"self.{key}")
    
    @property
    def xrt_mode(self):
        '''Return XRT mode as acronym'''
        return xrtmodes[self._xrt_mode]

    @xrt_mode.setter
    def xrt_mode(self,mode):
        self._xrt_mode = mode

    @property
    def uvot_mode(self):
        '''Return UVOT as a hex string. Stored as a number internally'''
        if type(self._uvot_mode) == int:
            return f"0x{self._uvot_mode:04x}"
        else:
            return self._uvot_mode

    @uvot_mode.setter
    def uvot_mode(self,mode):
        self._uvot_mode = mode

    @property
    def table(self):
        rows = ['start', 'stop', 'xrt_mode', 'uvot_mode','duration','asflown']
        header = [self.varnames[row] for row in rows]
        return header,[[getattr(self,row) for row in rows]]



class Swift_Calendar(TOOAPI_Baseclass):
    '''Class that displayed observations scheduled as part of a TOO request.'''
    def __init__(self,username='anonymous',too_id=None):
        TOOAPI_Baseclass.__init__(self)
        self.api_name = self.api_name = "Swift_Calendar"
        self.entries = list()
        self.username = username
        self.too_id = too_id
        self.rows = ['username','too_id']
        self.extrarows = ['status','entries']
        self.status = Swift_TOO_Status()

        # Stuff for scheduling
        self.subclasses = [Swift_Calendar_Entry,Swift_TOO_Status]

        if self.too_id != None:
            self.submit()

    def __getitem__(self,number):
        return self.entries[number]
    
    def __len__(self):
        return len(self.entries)

    def validate(self):
        if self.too_id != None:
            return True
        else:
            self.status.error("TOO ID is not set.")
            return False

    @property
    def table(self):
        '''Table of Calendar details'''
        table = list()
        for i in range(len(self.entries)):
            table.append([i]+self.entries[i].table[-1][0])
        if len(self.entries) > 0:
            header = ["#"]+self.entries[0].table[0]
        else:
            header = []
        return header,table

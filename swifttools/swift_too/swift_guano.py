from .common import TOOAPI_Baseclass, TOOAPI_ObsID, TOOAPI_Daterange
from .too_status import Swift_TOO_Status
from datetime import timedelta


class Swift_GUANO_GTI(TOOAPI_Baseclass, TOOAPI_Daterange):
    '''Define GUANO event data Good Time Intervals (GTI)

    Attributes
    ----------
    filename : str
        filename of BAT event data associated with GTI
    acs : str
        What was the status of the Swift Attitude Control System during this
        GTI. Options are 'slewing', 'pointing' and 'mixed'.
    began : datetime
        time request began processing
    completed : datetime
        time request finished processing
    exposure : float
        exposure time of GTI
    utcf : float
        UT Correction Factor - this encompasses correction for both the
        inaccuracies in the Swift clock and also any leap seconds
    '''
    api_name = 'Swift_GUANO_GTI'
    filename = None
    acs = None
    utcf = None
    exposure = None
    _attributes = ['begin', 'end', 'exposure', 'utcf', 'acs', 'filename']

    def __str__(self):
        return f"{self.begin} - {self.end} ({self.exposure})"


class Swift_GUANO_Data(TOOAPI_Baseclass, TOOAPI_ObsID, TOOAPI_Daterange):
    '''Class to hold information about GUANO data based on analysis of the BAT
    event files that are downlinked.

    Attributes
    ----------
    filenames : list
        filenames of BAT event data associated with GUANO dump
    acs : str
        What was the status of the Swift Attitude Control System during this
        GTI. Options are 'slewing', 'pointing' and 'mixed'.
    begin : datetime
        start time of GUANO dump
    end : datetime
        end time of GUANO dump
    triggertime : datetime
        trigger time of event that generated GUANO dump
    gti : Swift_GUANO_GTI
        Good Time Interval (GTI) for the combined event data
    all_gtis : list
        list of individual GTIs. More than one GTI can exist if data is split
        between multiple files, or if significant gaps appear in the event data
    obsid : str
        Observation ID associated with the GUANO data
    completed : datetime
        time request finished processing
    exposure : float
        exposure time of GTI
    utcf : float
        UT Correction Factor - this encompasses correction for both the
        inaccuracies in the Swift clock and also any leap seconds
    '''

    # API Name
    api_name = 'Swift_GUANO_Data'
    # Attributes
    all_gtis = None
    gti = None
    utcf = None
    acs = None
    exposure = None
    filenames = None

    # Core API definitions
    _parameters = ['obsid', 'triggertime']
    _attributes = ['begin', 'end', 'exposure',
                   'filenames', 'gti', 'all_gtis', 'acs', 'utcf']
    _subclasses = [Swift_GUANO_GTI]

    @property
    def _table(self):
        table = []
        if self.exposure is None:
            return [], []
        for row in self._parameters + self._attributes:
            value = getattr(self, row)
            if type(value) == list and value != []:
                table += [[row, "\n".join([gti.__str__() for gti in value])]]
            elif value is not None and value != "" and value != []:
                table += [[row, f"{value}"]]
        return ['Parameter', 'Value'], table


class Swift_GUANO_Entry(TOOAPI_Baseclass, TOOAPI_ObsID, TOOAPI_Daterange):
    '''Entry for an individual BAT ring buffer dump (AKA GUANO) event.

    Attributes
    ----------
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    triggertime : datetime
        triggertime associated with GUANO dump
    triggertype : str
        trigger type (typically what mission triggered the GUANO dump)
    offset : int
        Number of seconds the GUANO dump is offset from triggertime
    duration : int
        Number of seconds dumped
    status : str
        status of API request
    '''

    # API name
    api_name = 'Swift_GUANO_Entry'
    # Attributes
    triggertype = None
    triggertime = None
    duration = None
    quadsaway = None
    offset = None
    ra = None
    dec = None
    data = None
    utcf = None
    # Core API definitions
    _subclasses = [Swift_GUANO_Data]
    _parameters = ['triggertime']
    _attributes = ['triggertype', 'offset', 'duration',
                   'quadsaway', 'obsnum', 'ra', 'dec', 'data', 'utcf']

    @property
    def _table(self):
        table = []
        for row in self._parameters + self._attributes:
            value = getattr(self, row)
            if row == 'data' and self.data.exposure is not None:
                table += [[row, f"{value.exposure:.1f}s of BAT event data"]]
            elif row == 'data' and self.data.exposure is None:
                table += [[row, "No BAT event data found"]]
            elif value is not None:
                table += [[row, f"{value}"]]
        return ['Parameter', 'Value'], table

    @property
    def begin(self):
        dt = self.triggertime + \
            timedelta(seconds=self.offset - self.duration / 2)
        return dt

    @property
    def end(self):
        return self.triggertime + timedelta(seconds=self.offset + self.duration / 2)


class Swift_GUANO(TOOAPI_Baseclass, TOOAPI_Daterange):
    '''Query BAT ring buffer dumps of event data associated with the Gamma-Ray
    Burst Urgent Archiver for Novel Opportunities (GUANO).

    Attributes
    ----------
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    triggertime : datetime
        triggertime to search around
    begin : datetime
        start of time period to search
    end : datetime
        end of time period to search
    length : float
        length of time to search after `begin`
    limit : int
        limit number of results fetched
    entries : list
        list of GUANO dumps found given query parameters
    status : str
        status of API request
    guanostatus : boolean
        current status of guano system
    lastcommand : datetime
        when was the last GUANO command executed
    '''

    # API Name
    api_name = 'Swift_GUANO'
    # Core API definitions
    _parameters = ['username', 'triggertime', 'begin',
                   'end', 'limit', 'subthreshold', 'successful']
    _local = ['length']
    _attributes = ['guanostatus', 'lastcommand', 'entries', 'status']
    _subclasses = [Swift_GUANO_Entry, Swift_TOO_Status]
    # Attributes
    guanostatus = None
    lastcommand = None

    def __init__(self, *args, **kwargs):
        '''
        Parameters
        ----------
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        triggertime : datetime
            triggertime to search around
        begin : datetime
            start of time period to search
        end : datetime
            end of time period to search
        length : float
            length of time to search after `begin`
        limit : int
            limit number of results fetched
        '''
        # Login user
        self.username = 'anonymous'

        # Parameters
        self.subthreshold = False
        self.successful = True
        self.triggertime = None
        self.begin = None
        self.end = None
        self.length = None
        self.limit = None
        # Results
        self.entries = []

        # Status of query
        self.status = Swift_TOO_Status()

        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        # See if we pass validation from the constructor, but don't record
        # errors if we don't
        if self.validate():
            self.submit()
        else:
            self.status.clear()

    def __getitem__(self, index):
        return self.entries[index]

    def __len__(self):
        return len(self.entries)

    def validate(self):
        if self.limit is not None or self.begin is not None or self.end is not None or self.length is not None or self.triggertime is not None:
            if self.subthreshold is True and self.username == 'anonymous':
                self.status.error("For subthreshold triggers, username cannot be anonymous.")
                return False
            return True

    @property
    def _table(self):
        header = ['Trigger Type', 'Trigger Time',
                  'Offset (s)', 'Window Duration (s)', 'Observation ID']
        table = []
        for ent in self.entries:
            if ent.data.exposure is not None:
                if round(ent.duration) != round(ent.data.exposure):
                    exposure = f"{ent.duration} ({ent.data.exposure:.0f})"
                else:
                    exposure = f"{ent.duration}"
                if ent.data.gti is None:
                    exposure += "*"
            else:
                exposure = 0
            table.append([ent.triggertype, ent.triggertime,
                         ent.offset, exposure, ent.obsnum])

        return header, table


# Shorthand alias names for class
GUANO = Swift_GUANO

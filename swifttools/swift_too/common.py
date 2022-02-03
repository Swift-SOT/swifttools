import json
from datetime import datetime, timedelta, date
import re
from jose import jwt
import requests
from time import sleep
from .version import api_version
from tabulate import tabulate
import textwrap
# Next imports are not dependancies, but if you have them installed, we'll use
# them
try:
    import keyring
    # Check that keyring actually is set up and working
    if keyring.get_keyring().name != 'fail Keyring':
        keyring_support = True
    else:
        keyring_support = False
except ImportError:
    keyring_support = False

HAS_ASTROPY = False
try:
    from astropy.coordinates import SkyCoord
    HAS_ASTROPY = True
except ImportError:
    pass


# Convert degrees to radians
dtor = 0.017453292519943295
# Lookup table for XRT modes
xrtmodes = {0: "Auto", 1: "Null", 2: "ShortIM", 3: "LongIM", 4: "PUPD",
            5: "LRPD", 6: "WT", 7: "PC", 8: "Raw", 9: "Bias", None: 'Unset'}
modesxrt = {"Auto": 0, "Null": 1, "ShortIM": 2, "LongIM": 3,
            "PUPD": 4, "LRPD": 5, "WT": 6, "PC": 7, "Raw": 8, "Bias": 9}

# Regex for matching date, time and datetime strings
_date_regex = r"^[0-2]\d{3}-(0?[1-9]|1[012])-([0][1-9]|[1-2][0-9]|3[0-1])?$"
_time_regex = r"^([0-9]:|[0-1][0-9]:|2[0-3]:)[0-5][0-9]:[0-5][0-9]+(\.\d+)?$"
_datetime_regex = r"^[0-2]\d{3}-(0?[1-9]|1[012])-([0][1-9]|[1-2][0-9]|3[0-1]) ([0-9]:|[0-1][0-9]:|2[0-3]:)[0-5][0-9]:[0-5][0-9]+(\.\d+)?$"
_float_regex = r"^[+-]?(?=\d*[.eE])(?=\.?\d)\d*\.?\d*(?:[eE][+-]?\d+)?$"

# Submission URL
API_URL = "https://www.swift.psu.edu/toop/submit_json.php"


def convert_to_dt(value):
    '''Convert various date formats to datetime'''
    if type(value) == str:
        if re.match(_datetime_regex, value):
            if "." in value:
                # Do this because "fromisoformat" is restricted to 0, 3 or 6 decimal plaaces
                dtvalue = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
            else:
                dtvalue = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        elif re.match(_date_regex, value):
            dtvalue = datetime.strptime(f"{value} 00:00:00", '%Y-%m-%d %H:%M:%S')
    elif type(value) == date:
        dtvalue = datetime.strptime(f"{value} 00:00:00", '%Y-%m-%d %H:%M:%S')
    elif type(value) == datetime:
        dtvalue = datetime.fromtimestamp(value.timestamp())
    elif value is None:
        dtvalue = None
    elif value.__module__ == 'astropy.time.core' and value.__class__.__name__ == 'Time':
        dtvalue = value.datetime
    else:
        raise TypeError(
            'Date should be given as a datetime, astropy Time, or as string of format "YYYY-MM-DD HH:MM:SS"')
    return dtvalue


def _tablefy(table, header=None):
    '''Simple HTML table generator.'''

    tab = "<table>"
    if header is not None:
        tab += "<thead>"
        tab += "".join(
            [f"<th style='text-align: left;'>{head}</th>" for head in header])
        tab += "</thead>"

    for row in table:
        tab += "<tr>"
        # Replace any carriage returns with <br>
        row = [f"{col}".replace("\n", "<br>") for col in row]
        tab += "".join(
            [f"<td style='text-align: left;'>{col}</td>" for col in row])
        tab += "</tr>"
    tab += "</table>"
    return tab


class TOOAPI_Baseclass:
    '''Mixin for TOO API Classes. Most of these are to do with reading and
    writing classes out as JSON/dicts.'''

    # Set api_version for all classes
    api_version = api_version
    # Ignore any keys you don't understand
    ignorekeys = False
    username = 'anonymous'
    _shared_secret = None
    # Submission timeout
    timeout = 120  # 2 mins

    # Parameters that are _local
    _local = []
    # Parameters that get sent in API submission
    _parameters = []
    # Attributes that get send back by API
    _attributes = []

    @property
    def shared_secret(self):
        if self._shared_secret is None and self.username != 'anonymous':
            # Try to fetch password using keyring, if available
            if keyring_support:
                self._shared_secret = keyring.get_password(
                    'swifttools.swift_too', self.username)
            else:
                raise Exception(
                    "Warning: keyring support not available. Please set shared_secret manually.")
        elif self.username == 'anonymous':
            return 'anonymous'
        return self._shared_secret

    @shared_secret.setter
    def shared_secret(self, secret):
        if self.username != "anonymous" and (self.username is not None or self.username == ''):
            # Try to remember the password using keyring if available
            if keyring_support:
                keyring.set_password(
                    'swifttools.swift_too', self.username, secret)
        if self.username != 'anonymous':
            self._shared_secret = secret

    @property
    def _table(self):
        '''Table of details of the class'''
        _parameters = self._parameters + self._attributes
        header = ['Parameter', 'Value']
        table = []
        for row in _parameters:
            value = getattr(self, row)
            if value is not None and value != [] and value != "":
                if type(value) == list:
                    table.append([row, "\n".join([f"{le}" for le in value])])
                else:
                    table.append([row, "\n".join(textwrap.wrap(f"{value}"))])
        return header, table

    def _repr_html_(self):
        header, table = self._table
        if len(table) > 0:
            return _tablefy(table, header)
        else:
            return "No data"

    def __str__(self):
        header, table = self._table
        if len(table) > 0:
            return tabulate(table, header, tablefmt='pretty', stralign='right')
        else:
            return "No data"

    def __repr__(self):
        name = self.__class__.__name__
        args = ",".join([f"{row}='{getattr(self,row)}'" for row in self._parameters if getattr(
            self, row) is not None and getattr(self, row) != []])
        return f"{name}({args})"

    def _parseargs(self, *args, **kwargs):
        '''Parse arguements given in __init__ to API classes'''
        # Parse arguments. Assume they're the same order as `_parameters` except not `username`
        for i in range(len(args)):
            setattr(self, self._parameters[i+1], args[i])
        # Parse argument keywords
        for key in kwargs.keys():
            if key in self._parameters+self._local:
                setattr(self, key, kwargs[key])
            else:
                raise TypeError(
                    f"{self.api_name} got an unexpected keyword argument '{key}'")

    @property
    def too_api_dict(self):
        '''Dictionary version of TOO API object'''
        too_api_dict = dict()
        too_api_dict["api_name"] = self.api_name
        too_api_dict["api_version"] = self.api_version
        too_api_dict['api_data'] = self.api_data
        return too_api_dict

    @property
    def api_data(self):
        '''Convert class parameters and data into a dictionary'''
        data = dict()
        for param in self._parameters:
            value = getattr(self, param)
            if value is not None:
                if 'api_data' in dir(value):
                    data[param] = value.too_api_dict
                elif type(value) == list or type(value) == tuple:
                    def conv(x): return x if not hasattr(
                        x, 'too_api_dict') else x.too_api_dict
                    data[param] = [conv(entry) for entry in value]
                elif type(value) == datetime or type(value) == date or type(value) == timedelta:
                    data[param] = f"{value}"
                # Detect and convert astropy Time
                elif type(value).__module__ == 'astropy.time.core':
                    data[param] = f"{value.datetime}"
                else:
                    data[param] = value
        return data

    @property
    def jwt(self):
        '''JWT version of TOO API Object'''
        return jwt.encode(self.too_api_dict, self.shared_secret, algorithm='HS256')

    def __convert_dict_entry(self, entry):
        '''Parse data entry from a dictionary (usualy originating as a JSON) to
        convert into Python data types. Danger! Danger Will Robinson! Recursion!
        Recursion!'''
        # Parse a JSON entry
        if type(entry) == dict and 'api_name' in entry.keys():
            index = [s.__name__ for s in self._subclasses].index(
                entry['api_name'])
            val = self._subclasses[index]()
            val.__read_dict(entry['api_data'])
        # Parse a list of items
        elif type(entry) == list:
            # Parse a list of jsons
            val = list()
            for subvalue in entry:
                # Hey, we must have some handy function for parsing values, right?
                val.append(self.__convert_dict_entry(subvalue))
        # Parse all other values
        else:
            val = False
            if entry:
                # Check if these are dates, datetimes or times by regex matching
                match = re.match(_time_regex, str(entry))
                if match is not None:
                    hours, mins, secs = match[0].split(":")
                    hours = int(hours)
                    mins = int(mins)
                    secs = int(float(secs))
                    millisecs = int(1000.0*secs % 1)
                    val = timedelta(hours=hours, minutes=mins,
                                    seconds=secs, milliseconds=millisecs)

                # Parse dates into a datetime.date
                match = re.match(_date_regex, str(entry))
                if match is not None:
                    val = datetime.strptime(match[0], '%Y-%m-%d').date()

                # Parse a date/time into a datetime.datetime
                match = re.match(_datetime_regex, str(entry))
                if match is not None:
                    val = convert_to_dt(match[0])

                # If it's a float, convert it
                if type(entry) == str:
                    match = re.match(_float_regex, entry)
                    if match is not None:
                        val = float(entry)

            # None of the above? It is what it is.
            if val is False:
                val = entry

        return val

    def __set_status(self, newstatus):
        if hasattr(self, 'status'):
            if type(self.status) == str:
                self.status = newstatus
            else:
                self.status.status = newstatus
        else:
            print(f"STATUS: {newstatus}")

    def __set_error(self, newerror):
        if hasattr(self, 'status'):
            if type(self.status) == str:
                self.error(newerror)
            else:
                self.status.error(newerror)
        else:
            print(f"ERROR: {newerror}")

    def __read_dict(self, data_dict):
        '''Read from a dictionary values for the class'''
        for key in data_dict.keys():
            if key in self._parameters or key in self._attributes:
                val = self.__convert_dict_entry(data_dict[key])
                if val is not None:  # If value is set to None, then don't change the value
                    setattr(self, key, val)
            else:
                if not self.ignorekeys:  # If keys exist in JSON we don't understand, fail out
                    self.__set_error(f"Unknown key in JSON file: {key}")
                    return False
        return True  # No errors

    @property
    def submit_url(self):
        '''Generate a URL that submits the TOO API request'''
        url = f"{API_URL}?jwt={self.jwt}"
        return url

    def queue(self, post=True):
        '''Validate and submit a TOO API job to the queue for processing.'''
        # Make sure a shared secret is set
        if self.shared_secret is None:
            self.__set_error("shared_secret not set, cannot submit job.")
            return False
        # Make sure it passes validation checks
        if not self.validate():
            self.__set_error(
                "Swift TOO API submission did not pass internal validation checks.")
            return False

        # For Swift_ObsQuery if end is set as the future, just set it to now as this can cause confusion with caching.
        if self.api_name == 'Swift_AFST' and self.end is not None and self.end > datetime.utcnow():
            self.end = datetime.utcnow()

        return self.__submit_jwt(post=post)

    @property
    def complete(self, post=True):
        '''Check if a queued job is completed'''
        # Send request to TOO API server
        self.__submit_jwt(post=post)
        # Check the status of the request
        if self.status != "Queued" and self.status != "Processing":
            return True
        return False

    def __submit_jwt(self, post=True):
        '''Submit JWT request to the TOO API server, read in the reply and parse it.'''
        # Don't submit an accepted or rejected request more than once
        if self.status == "Accepted":
            return True
        elif self.status == "Rejected":
            return False

        # Which way will we fetch the data?
        if post:
            r = self.__submit_post()
        else:
            r = self.__submit_get()

        # See how sucessful we were
        if r.status_code == 200:
            # True to decode the returned JSON. Return an error if it doesn't work.
            try:
                too_api_dict = json.loads(r.text)
            except json.decoder.JSONDecodeError:
                self.__set_error(
                    "Failed to decode JSON. Please check that your shared secret is correct.")
                self.__set_status('Rejected')
                return False

            # Determine that we are running the correct API version
            if too_api_dict['api_version'] != self.api_version:
                self.__set_error(
                    f"API version mismatch. Remote version {too_api_dict['api_version']} vs"
                    f"local version {self.api_version}. Ensure you're running the latest API code.")
                self.__set_status('Rejected')
                return False

            # Determine if the returned JSON is the full result or just a status message
            if too_api_dict['api_name'] == self.api_name:
                self.__read_dict(too_api_dict['api_data'])
            elif too_api_dict['api_name'] == "Swift_TOO_Status":
                self.status.__read_dict(too_api_dict['api_data'])
        else:
            self.__set_error(
                f"HTTP Submit failed with error code {r.status_code}")
            self.__set_status('Rejected')
            return False
        return True

    def submit(self, timeout=None, post=True):
        '''Queue up a TOO API job, then wait for it to complete. Default behaviour is to keep
        checking if the submission has been processed by the TOO_API server every 1 seconds
        until the timeout (default 120s) has been reached.'''
        # Update timeout value from default if passed
        if timeout is not None:
            self.timeout = timeout

        # Submit the job to the queue
        ustart = datetime.now().timestamp()
        if not self.queue(post=post):
            self.__set_error("Failed to queue job.")
            self.__set_status('Rejected')
            return False

        # Check if the Queued job is complete for up to *timeout* seconds (120s default)
        while(datetime.now().timestamp()-ustart < self.timeout and not self.complete):
            sleep(1)

        # If the job is still Queued, report that it has timed out as an error
        if self.status == 'Queued' or self.status == 'Processing':
            self.__set_error("Queued job timed out.")
            return False
        # Or else return True or False if it has been Accepted or Rejected
        else:
            if self.status == 'Accepted':
                return True
            else:
                return False

    def __submit_get(self):
        '''Submit the request through the web based API, as a JWT through GET (essentially a URL)'''
        return requests.get(self.submit_url)

    def __submit_post(self):
        '''Submit the request through the web based API, as a JWT through POST (recommended)'''
        return requests.post(url=API_URL, verify=True, data={'jwt': self.jwt})


class TOOAPI_Daterange:
    '''A Mixin for all classes that have begin, end and length for setting date
    ranges. These functions allow dates to be givin as strings,
    datetime.datetime or astropy Time objects, and length to be given in number
    of days, or as a datetime.timedelta object or an astropy TimeDelta
    object.'''

    _length = None
    _begin = None
    _end = None

    @property
    def begin(self):
        return self._begin

    @property
    def end(self):
        return self._end

    @property
    def length(self):
        if self._length is None and self._begin is not None and self._end is not None:
            return (self._end - self._begin).total_seconds() / 86400.0
        return self._length

    @begin.setter
    def begin(self, begin):
        self._begin = convert_to_dt(begin)

    @end.setter
    def end(self, end):
        self._end = convert_to_dt(end)
        # If we're changing the end, and begin is defined, then update length
        if self._begin is not None and self._end is not None:
            self._length = (self._end - self._begin).total_seconds() / 86400.0

    @length.setter
    def length(self, length):
        if type(length) == timedelta:
            self._length = length.total_seconds()/86400.0
        elif type(length).__module__ == 'astropy.time.core' and type(length).__name__ == 'TimeDelta':
            self._length = length.to_datetime().total_seconds()/86400.0
        elif length is None:
            self._length = None
        else:
            try:
                self._length = float(length)
            except ValueError:
                raise TypeError(
                    'Length should be given as a datetime.timedelta, astropy Time or as a number of days')

        # If we're changing length, make sure end is changed
        if self._begin is not None and self._length is not None:
            self._end = self._begin + timedelta(days=self._length)


class TOOAPI_SkyCoord:
    '''Mixin to support for using a SkyCoord in place of RA/Dec. Note that
    swift_too only support SkyCoords if astropy itself is installed. astropy is
    not a dependency for swift_too so will not get installed if you don't already
    have it.'''

    _skycoord = None
    _radius = None
    _ra = None
    _dec = None

    @property
    def skycoord(self):
        '''Allow TOO requesters to give an astropy SkyCoord object instead of
        RA/Dec. Handy if you want to do things like submit 1950 coordinates or
        Galactic Coordinates.'''
        # Check if the RA/Dec match the SkyCoord, and if they don't modify the skycoord
        if HAS_ASTROPY:
            if self.ra != self._ra or self.dec != self._dec:
                self._skycoord = SkyCoord(
                    self.ra, self.dec, unit="deg", frame="fk5")
                self._ra, self._dec = self.ra, self.dec
            return self._skycoord
        else:
            raise ImportError(
                "To use skycoord, astropy needs to be installed.")

    @skycoord.setter
    def skycoord(self, sc):
        '''Convert the SkyCoord into RA/Dec (J2000) when set.'''
        if HAS_ASTROPY:
            if sc is None:
                self._skycoord = None
            elif type(sc).__module__ == 'astropy.coordinates.sky_coordinate':
                self._skycoord = sc
                self.ra = sc.fk5.ra.deg
                self.dec = sc.fk5.dec.deg
            else:
                raise TypeError("Needs to be assigned an Astropy SkyCoord")
        else:
            raise ImportError(
                "To use skycoord, astropy needs to be installed.")


class TOOAPI_ObsID:
    '''Mixin for handling target ID / Observation ID with various aliases'''

    _target_id = None
    _seg = None

    def convert_obsnum(self, obsnum):
        '''Convert various formats for obsnum (SDC and Spacecraft) into one format (Spacecraft)'''
        if type(obsnum) == str:
            if re.match("^[0-9]{11}?$", obsnum) is None:
                raise ValueError("ERROR: Obsnum string format incorrect")
            else:
                targetid = int(obsnum[0:8])
                segment = int(obsnum[8:12])
                return targetid + (segment << 24)
        elif type(obsnum) == int:
            return obsnum
        elif obsnum is None:
            return None
        else:
            raise ValueError('`obsnum` in wrong format.')

    @property
    def target_id(self):
        return self._target_id

    @target_id.setter
    def target_id(self, tid):
        if type(tid) == str:
            self._target_id = int(tid)
        else:
            self._target_id = tid

    @property
    def seg(self):
        return self._seg

    @seg.setter
    def seg(self, segment):
        self._seg = segment

    @property
    def obsnum(self):
        '''Return the obsnum in SDC format'''
        if self._target_id is None or self._seg is None:
            return None
        elif type(self._target_id) == list:
            return [f"{self.target_id[i]:08d}{self.seg[i]:03d}" for i in range(len(self._target_id))]
        else:
            return f"{self.target_id:08d}{self.seg:03d}"

    @obsnum.setter
    def obsnum(self, obsnum):
        '''Set the obsnum value, by figuring out what the two formats are.'''
        # Deal with lists of obsnumbers
        if type(obsnum) == list and len(obsnum) > 0:
            self._target_id = list()
            self._seg = list()
            for on in obsnum:
                onsc = self.convert_obsnum(on)
                self._target_id.append(onsc & 0xffffff)
                self._seg.append(onsc >> 24)

        elif obsnum is not None and obsnum != []:
            obsnum = self.convert_obsnum(obsnum)
            self._target_id = obsnum & 0xffffff
            self._seg = obsnum >> 24

    @property
    def obsnumsc(self):
        '''Return the obsnum in spacecraft format'''
        if type(self._target_id) == list:
            return [self._target_id[i] + (self._seg[i] << 24) for i in range(len(self._target_id))]
        return self._target_id + (self._seg << 24)

    # Aliases
    targetid = target_id
    segment = seg
    obsid = obsnum
    obsidsc = obsnumsc


class TOOAPI_Instruments:
    '''Mixin for XRT / UVOT mode display and capture'''
    _uvot = None
    _xrt = None
    _bat = None  # For now, bat mode is just an integer

    def uvot_mode_setter(self, attr, mode):
        if type(mode) == str and '0x' in mode:
            '''Convert hex string to int'''
            setattr(self, f"_{attr}", int(mode.split(':')[0], 16))
        elif type(mode) == str:
            '''Convert decimal string to int'''
            try:
                setattr(self, f"_{attr}", int(mode))
            except (TypeError, ValueError):
                setattr(self, f"_{attr}", mode)
        else:
            '''Pass through anything else'''
            setattr(self, f"_{attr}", mode)

    def xrt_mode_setter(self, attr, mode):
        if type(mode) == str:
            if mode in modesxrt.keys():
                setattr(self, f"_{attr}", modesxrt[mode])
            else:
                raise NameError(
                    f"Unknown mode ({mode}), should be PC, WT or Auto")
        elif mode is None:
            setattr(self, f"_{attr}", mode)
        else:
            if mode in xrtmodes.keys():
                setattr(self, f"_{attr}", mode)
            else:
                raise ValueError(
                    f"Unknown mode ({mode}), should be PC (7), WT (6) or Auto (0)")

    @property
    def xrt(self):
        '''Given a XRT mode number returns a string containing the name of the
        mode'''
        return xrtmodes[self._xrt]

    @xrt.setter
    def xrt(self, mode):
        self.xrt_mode_setter('xrt', mode)

    @property
    def uvot(self):
        '''Given a UVOT mode number returns a string containing the name of the
        mode'''
        if type(self._uvot) == int:
            return f"0x{self._uvot:04x}"
        else:
            return self._uvot

    @uvot.setter
    def uvot(self, mode):
        self.uvot_mode_setter('uvot', mode)

    @property
    def bat(self):
        '''Given a BAT mode number returns a string containing the name of the
        mode'''
        if type(self._bat) == int:
            return f"0x{self._bat:04x}"
        else:
            return self._bat

    @bat.setter
    def bat(self, mode):
        self.uvot_mode_setter('bat', mode)

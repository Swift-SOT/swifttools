import json
from datetime import datetime, timedelta, date, timezone
import re
from jose import jwt
import requests
from time import sleep
from .version import version_tuple
from tabulate import tabulate
import textwrap
from dateutil import parser

# Configure for IPV4 only due to issue
requests.packages.urllib3.util.connection.HAS_IPV6 = False

# Define the API version
api_version = f"{version_tuple[0]}.{version_tuple[1]}"

# Next imports are not dependancies, but if you have them installed, we'll use
# them
try:
    import keyring

    # Check that keyring actually is set up and working
    if keyring.get_keyring().name != "fail Keyring":
        keyring_support = True
    else:
        keyring_support = False
except ImportError:
    keyring_support = False

# Check if we have astropy support
HAS_ASTROPY = False
try:
    from astropy.time import Time
    import astropy.units as u

    HAS_ASTROPY = True
except ImportError:
    pass


# Convert degrees to radians
dtor = 0.017453292519943295

# Regex for matching date, time and datetime strings
_date_regex = r"^[0-2]\d{3}-(0?[1-9]|1[012])-([0][1-9]|[1-2][0-9]|3[0-1])?$"
_time_regex = r"^([0-9]:|[0-1][0-9]:|2[0-3]:)[0-5][0-9]:[0-5][0-9]+(\.\d+)?$"
_iso8601_regex = r"^([\+-]?\d{4}(?!\d{2}\b))((-?)((0[1-9]|1[0-2])(\3([12]\d|0[1-9]|3[01]))?|W([0-4]\d|5[0-2])(-?[1-7])?|(00[1-9]|0[1-9]\d|[12]\d{2}|3([0-5]\d|6[1-6])))([T\s]((([01]\d|2[0-3])((:?)[0-5]\d)?|24\:?00)([\.,]\d+(?!:))?)?(\17[0-5]\d([\.,]\d+)?)?([zZ]|([\+-])([01]\d|2[0-3]):?([0-5]\d)?)?)?)?$"
_datetime_regex = r"^[0-2]\d{3}-(0?[1-9]|1[012])-([0][1-9]|[1-2][0-9]|3[0-1]) ([0-9]:|[0-1][0-9]:|2[0-3]:)[0-5][0-9]:[0-5][0-9]+(\.\d+)?$"
_float_regex = r"^[+-]?(?=\d*[.eE])(?=\.?\d)\d*\.?\d*(?:[eE][+-]?\d+)?$"
_int_regex = r"^(0|[1-9][0-9]+)$"

# Submission URL
API_URL = "https://www.swift.psu.edu/toop/submit_json.php"


def convert_to_dt(value, isutc=False, outfunc=datetime):
    """Convert various date formats to swiftdatetime or datetime

    Parameters
    ----------
    value : varies
        Value to be converted.
    isutc : bool, optional
        Is the value in UTC, by default False
    outfunc : datetime / swiftdatetime, optional
        What format should the output be? By default datetime, can be
        swiftdatetime

    Returns
    -------
    datetime / swiftdatetime
        Returned datetime / swiftdatetime object

    Raises
    ------
    TypeError
        Raised if incorrect format is given for conversion.
    """

    if type(value) == str:
        if re.match(_datetime_regex, value):
            if "." in value:
                # Do this because "fromisoformat" is restricted to 0, 3 or 6 decimal plaaces
                dtvalue = outfunc.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
            else:
                dtvalue = outfunc.strptime(value, "%Y-%m-%d %H:%M:%S")
        elif re.match(_date_regex, value):
            dtvalue = outfunc.strptime(f"{value} 00:00:00", "%Y-%m-%d %H:%M:%S")
        elif re.match(_iso8601_regex, value):
            dtvalue = parser.parse(value).astimezone(timezone.utc).replace(tzinfo=None)
        else:
            raise ValueError(
                "Date/time given as string should 'YYYY-MM-DD HH:MM:SS' or ISO8601 format."
            )
    elif type(value) == date:
        dtvalue = outfunc.strptime(f"{value} 00:00:00", "%Y-%m-%d %H:%M:%S")
    elif type(value) == outfunc:
        if value.tzinfo is not None:
            # Strip out timezone info and convert to UTC
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        dtvalue = value  # Just pass through un molested
    elif (
        type(value) == swiftdatetime
        and outfunc == datetime
        or type(value) == datetime
        and outfunc == swiftdatetime
    ):
        if type(value) == datetime and value.tzinfo is not None:
            # Strip out timezone info and convert to UTC
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        dtvalue = outfunc.fromtimestamp(value.timestamp())
    elif value is None:
        dtvalue = None
    elif HAS_ASTROPY and type(value) is Time:
        dtvalue = value.datetime
    else:
        raise TypeError(
            'Date should be given as a datetime, astropy Time, or as string of format "YYYY-MM-DD HH:MM:SS"'
        )
    if outfunc is swiftdatetime and dtvalue.isutc != isutc:
        dtvalue.isutc = isutc
    return dtvalue


def _tablefy(table, header=None):
    """Simple HTML table generator

    Parameters
    ----------
    table : list
        Data for table
    header : list
        Headers for table, by default None

    Returns
    -------
    str
        HTML formatted table.
    """

    tab = "<table>"
    if header is not None:
        tab += "<thead>"
        tab += "".join(
            [f"<th style='text-align: left;'>{head}</th>" for head in header]
        )
        tab += "</thead>"

    for row in table:
        tab += "<tr>"
        # Replace any carriage returns with <br>
        row = [f"{col}".replace("\n", "<br>") for col in row]
        tab += "".join([f"<td style='text-align: left;'>{col}</td>" for col in row])
        tab += "</tr>"
    tab += "</table>"
    return tab


class TOOAPI_Baseclass:
    """Mixin for TOO API Classes. Most of these are to do with reading and
    writing classes out as JSON/dicts."""

    # Set api_version for all classes
    api_version = api_version
    # Ignore any keys you don't understand
    ignorekeys = False
    username = "anonymous"
    _shared_secret = None
    # Submission timeout
    timeout = 120  # 2 mins
    # By default all API dates are in Swift Time
    _isutc = False

    # Parameters that are _local
    _local = []
    # Parameters that get sent in API submission
    _parameters = []
    # Attributes that get send back by API
    _attributes = []

    @property
    def shared_secret(self):
        if self._shared_secret is None and self.username != "anonymous":
            # Try to fetch password using keyring, if available
            if keyring_support:
                self._shared_secret = keyring.get_password(
                    "swifttools.swift_too", self.username
                )
            else:
                raise Exception(
                    "Warning: keyring support not available. Please set shared_secret manually."
                )
        elif self.username == "anonymous":
            return "anonymous"
        return self._shared_secret

    @shared_secret.setter
    def shared_secret(self, secret):
        if self.username != "anonymous" and (
            self.username is not None or self.username == ""
        ):
            # Try to remember the password using keyring if available
            if keyring_support:
                try:
                    keyring.set_password("swifttools.swift_too", self.username, secret)
                except keyring.errors.PasswordSetError:
                    # This error is raised in if keyring support is enabled on
                    # macOS, but the person isn't running the code interactively
                    # or if they're logged in via ssh. Just trap and move on to
                    # avoid code crashing.
                    pass

        if self.username != "anonymous":
            self._shared_secret = secret

    @property
    def _table(self):
        """Table of details of the class"""
        _parameters = self._parameters + self._attributes
        header = ["Parameter", "Value"]
        table = []
        for row in _parameters:
            value = getattr(self, row)
            if value is not None and value != [] and value != "":
                if row == "status" and type(value) != str:
                    table.append([row, value.status])
                elif type(value) == list:
                    table.append([row, "\n".join([f"{le}" for le in value])])
                else:
                    table.append([row, "\n".join(textwrap.wrap(f"{value}"))])
        return header, table

    def _repr_html_(self):
        if (
            hasattr(self, "status")
            and self.status == "Rejected"
            and self.status.__class__.__name__ == "Swift_TOO_Status"
        ):
            return "<b>Rejected with the following error(s): </b>" + " ".join(
                self.status.errors
            )
        else:
            header, table = self._table
            if len(table) > 0:
                return _tablefy(table, header)
            else:
                return "No data"

    def __str__(self):
        if (
            hasattr(self, "status")
            and self.status == "Rejected"
            and self.status.__class__.__name__ == "Swift_TOO_Status"
        ):
            return "Rejected with the following error(s): " + " ".join(
                self.status.errors
            )
        else:
            header, table = self._table
            if len(table) > 0:
                return tabulate(table, header, tablefmt="pretty", stralign="right")
            else:
                return "No data"

    def __repr__(self):
        name = self.__class__.__name__
        args = ",".join(
            [
                f"{row}='{getattr(self,row)}'"
                for row in self._parameters
                if getattr(self, row) is not None and getattr(self, row) != []
            ]
        )
        return f"{name}({args})"

    def _parseargs(self, *args, **kwargs):
        """Parse arguements given in __init__ to API classes"""
        # Parse arguments. Assume they're the same order as `_parameters` except not `username`
        for i in range(len(args)):
            setattr(self, self._parameters[i + 1], args[i])
        # Parse argument keywords
        for key in kwargs.keys():
            if key in self._parameters + self._local:
                setattr(self, key, kwargs[key])
            else:
                raise TypeError(
                    f"{self.api_name} got an unexpected keyword argument '{key}'"
                )

    @property
    def too_api_dict(self):
        """Dictionary version of TOO API object"""
        too_api_dict = dict()
        too_api_dict["api_name"] = self.api_name
        too_api_dict["api_version"] = self.api_version
        too_api_dict["api_data"] = self.api_data
        return too_api_dict

    @property
    def api_data(self):
        """Convert class parameters and data into a dictionary"""
        data = dict()
        for param in self._parameters:
            value = getattr(self, param)
            if value is not None:
                # Note just convert swiftdatetime into isoformat strings for now
                if "api_data" in dir(value) and value.api_name != "swiftdatetime":
                    data[param] = value.too_api_dict
                elif type(value) == list or type(value) == tuple:

                    def conv(x):
                        return (
                            f"{x}" if not hasattr(x, "too_api_dict") else x.too_api_dict
                        )

                    data[param] = [conv(entry) for entry in value]
                elif (
                    type(value) == datetime
                    or type(value) == date
                    or type(value) == timedelta
                    or type(value) == swiftdatetime
                ):
                    data[param] = f"{value}"
                # Detect and convert astropy Time
                elif HAS_ASTROPY and type(value) == Time:
                    data[param] = f"{value.datetime}"
                elif HAS_ASTROPY and type(value) == u.quantity.Quantity:
                    # For any astropy units not handled explicitly, pass as string
                    data[param] = f"{value}"
                else:
                    data[param] = value
        return data

    @property
    def jwt(self):
        """JWT version of TOO API Object"""
        return jwt.encode(self.too_api_dict, self.shared_secret, algorithm="HS256")

    def __convert_dict_entry(self, entry):
        """Parse data entry from a dictionary (usually originating as a JSON) to
        convert into Python data types. Danger! Danger Will Robinson! Recursion!
        Recursion!"""
        # Parse a JSON entry
        if type(entry) == dict and "api_name" in entry.keys():
            index = [s.api_name for s in self._subclasses].index(entry["api_name"])
            if self._subclasses[index] == swiftdatetime:
                # Handle swiftdatetime as it cannot be created with no arguments
                val = swiftdatetime.frommet(
                    entry["api_data"]["met"],
                    utcf=entry["api_data"]["utcf"],
                    isutc=entry["api_data"]["isutc"],
                )
            else:
                # Handle everything else
                val = self._subclasses[index]()
                val.__read_dict(entry["api_data"])
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
                    millisecs = int(1000.0 * secs % 1)
                    val = timedelta(
                        hours=hours, minutes=mins, seconds=secs, milliseconds=millisecs
                    )

                # Parse dates into a datetime.date
                match = re.match(_date_regex, str(entry))
                if match is not None:
                    val = datetime.strptime(match[0], "%Y-%m-%d").date()

                # Parse a date/time into a datetime.datetime
                match = re.match(_datetime_regex, str(entry))
                if match is not None:
                    val = convert_to_dt(match[0], self._isutc)

                # If it's a float, convert it
                if type(entry) == str:
                    match = re.match(_float_regex, entry)
                    if match is not None:
                        val = float(entry)

                # If it's an int, convert it
                if type(entry) == str:
                    match = re.match(_int_regex, entry)
                    if match is not None:
                        val = int(entry)

            # None of the above? It is what it is.
            if val is False:
                val = entry

        return val

    def __set_status(self, newstatus):
        if hasattr(self, "status"):
            if type(self.status) == str:
                self.status = newstatus
            else:
                self.status.status = newstatus
        else:
            print(f"STATUS: {newstatus}")

    def __set_error(self, newerror):
        if hasattr(self, "status"):
            if type(self.status) == str:
                self.error(newerror)
            else:
                self.status.error(newerror)
        else:
            print(f"ERROR: {newerror}")

    def __read_dict(self, data_dict):
        """Read from a dictionary values for the class"""
        for key in data_dict.keys():
            if key in self._parameters or key in self._attributes:
                val = self.__convert_dict_entry(data_dict[key])
                if (
                    val is not None
                ):  # If value is set to None, then don't change the value
                    if hasattr(self, f"_{key}"):
                        setattr(self, f"_{key}", val)
                    else:
                        setattr(self, key, val)
            else:
                if (
                    not self.ignorekeys
                ):  # If keys exist in JSON we don't understand, fail out
                    self.__set_error(f"Unknown key in JSON file: {key}")
                    return False
        return True  # No errors

    @property
    def submit_url(self):
        """Generate a URL that submits the TOO API request"""
        url = f"{API_URL}?jwt={self.jwt}"
        return url

    def queue(self, post=True):
        """Validate and submit a TOO API job to the queue for processing."""
        # Make sure a shared secret is set
        if self.shared_secret is None:
            self.__set_error("shared_secret not set, cannot submit job.")
            return False
        # Make sure it passes validation checks
        if not self.validate():
            self.__set_error(
                "Swift TOO API submission did not pass internal validation checks."
            )
            return False

        return self.__submit_jwt(post=post)

    @property
    def complete(self, post=True):
        """Check if a queued job is completed"""
        # Send request to TOO API server
        self.__submit_jwt(post=post)
        # Check the status of the request
        if self.status != "Queued" and self.status != "Processing":
            return True
        return False

    def __submit_jwt(self, post=True):
        """Submit JWT request to the TOO API server, read in the reply and parse it."""
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
                    "Failed to decode JSON. Please check that your shared secret is correct."
                )
                self.__set_status("Rejected")
                return False

            # Determine that we are running the correct API version
            if too_api_dict["api_version"] != self.api_version:
                self.__set_error(
                    f"API version mismatch. Remote version {too_api_dict['api_version']} vs"
                    f"local version {self.api_version}. Ensure you're running the latest API code."
                )
                self.__set_status("Rejected")
                return False

            # Determine if the returned JSON is the full result or just a status message
            if too_api_dict["api_name"] == self.api_name:
                self.__read_dict(too_api_dict["api_data"])
            elif too_api_dict["api_name"] == "Swift_TOO_Status":
                self.status.__read_dict(too_api_dict["api_data"])
        else:
            self.__set_error(f"HTTP Submit failed with error code {r.status_code}")
            self.__set_status("Rejected")
            return False
        return True

    def submit(self, timeout=None, post=True):
        """Queue up a TOO API job, then wait for it to complete. Default behaviour is to keep
        checking if the submission has been processed by the TOO_API server every 1 seconds
        until the timeout (default 120s) has been reached."""
        # Update timeout value from default if passed
        if timeout is not None:
            self.timeout = timeout

        # Submit the job to the queue
        ustart = datetime.now().timestamp()
        if not self.queue(post=post):
            self.__set_error("Failed to queue job.")
            self.__set_status("Rejected")
            return False

        # Check if the Queued job is complete for up to *timeout* seconds (120s default)
        while datetime.now().timestamp() - ustart < self.timeout and not self.complete:
            sleep(1)

        # If the job is still Queued, report that it has timed out as an error
        if self.status == "Queued" or self.status == "Processing":
            self.__set_error("Queued job timed out.")
            return False
        # Or else return True or False if it has been Accepted or Rejected
        else:
            if self.status == "Accepted":
                # Run post processing script to do things
                self._post_process()
                return True
            else:
                return False

    def _post_process(self):
        """Placeholder method. Things to do after values are returned from API."""
        pass

    def __submit_get(self):
        """Submit the request through the web based API, as a JWT through GET (essentially a URL)"""
        return requests.get(self.submit_url)

    def __submit_post(self):
        """Submit the request through the web based API, as a JWT through POST (recommended)"""
        return requests.post(url=API_URL, verify=True, data={"jwt": self.jwt})


class swiftdatetime(datetime, TOOAPI_Baseclass):
    """Extend datetime to store met, utcf and swifttime. Default value is UTC"""

    api_name = "swiftdatetime"
    _parameters = ["met", "utcf", "swifttime", "utctime", "isutc"]

    def __new__(self, *args, **kwargs):
        return super(swiftdatetime, self).__new__(self, *args)

    def __init__(self, *args, **kwargs):
        self._met = None
        self.utcf = None
        self._swifttime = None
        self._utctime = None
        self._isutc = False
        self._isutc_set = False
        if "tzinfo" in kwargs.keys():
            raise TypeError("swiftdatetime does not support timezone information.")
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

    def __repr__(self):
        return f"swiftdatetime({self.year}, {self.month}, {self.day}, {self.hour}, {self.minute}, {self.second}, {self.microsecond}, isutc={self.isutc}, utcf={self.utcf})"

    def __sub__(self, other):
        """Redefined __sub__ to handle mismatched time bases"""
        if isinstance(other, swiftdatetime):
            if self.isutc != other.isutc and (
                self.utctime is None or other.utctime is None
            ):
                raise ArithmeticError(
                    "Cannot subtract mismatched time zones with no UTCF"
                )  # FIXME - correct exception?

            if (
                self.isutc is True
                and other.isutc is True
                or self.isutc is False
                and other.isutc is False
            ):
                return super().__sub__(other)
            else:
                if self.isutc:
                    return super().__sub__(other.utctime)
                else:
                    return self.utctime.__sub__(other.utctime)
        else:
            value = super().__sub__(other)
            if hasattr(value, "isutc"):
                value.isutc = self.isutc
            return value

    def __add__(self, other):
        """Custom add for swiftdatetime. Note that UTCF is not preserved, on purpose."""
        value = super().__add__(other)
        if hasattr(value, "isutc"):
            value.isutc = self.isutc
        return value

    @property
    def isutc(self):
        return self._isutc

    @isutc.setter
    def isutc(self, utc):
        """Is this swiftdatetime based on UTC or Swift Time"""
        if self._isutc_set is not True:
            # If we change the time base for this, reset the values of swifttime and utctime
            self._isutc = utc
            self.swifttime = None
            self.utctime = None
            self._isutc_set = True
        else:
            raise AttributeError("Cannot set attribute isutc when previously set.")

    @property
    def met(self):
        if self.swifttime is not None:
            return (self.swifttime - datetime(2001, 1, 1)).total_seconds()

    @met.setter
    def met(self, met):
        self._met = met

    @property
    def utctime(self):
        if self._utctime is None:
            if self.isutc:
                self._utctime = datetime(
                    self.year,
                    self.month,
                    self.day,
                    self.hour,
                    self.minute,
                    self.second,
                    self.microsecond,
                )
            elif self.utcf is not None:
                self._utctime = self.swifttime + timedelta(seconds=self.utcf)
        return self._utctime

    @utctime.setter
    def utctime(self, utc):
        if isinstance(utc, datetime):
            # Ensure that utctime set to a pure datetime
            if utc.tzinfo is not None:
                utc = utc.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            self._utctime = utc

    @property
    def swifttime(self):
        if self._swifttime is None:
            if not self.isutc:
                self._swifttime = datetime(
                    self.year,
                    self.month,
                    self.day,
                    self.hour,
                    self.minute,
                    self.second,
                    self.microsecond,
                )
            elif self.utcf is not None:
                self._swifttime = self.utctime - timedelta(seconds=self.utcf)
        return self._swifttime

    @swifttime.setter
    def swifttime(self, st):
        if isinstance(st, datetime):
            # Ensure that swifttime set to a pure datetime
            if st.tzinfo is not None:
                st = st.astimezone(timezone.utc).replace(tzinfo=None)
            self._swifttime = st
        else:
            self._swifttime = convert_to_dt(st)

    @property
    def _table(self):
        if self._isutc:
            header = ["MET (s)", "Swift Time", "UTC Time (default)", "UTCF (s)"]
        else:
            header = ["MET (s)", "Swift Time (default)", "UTC Time", "UTCF (s)"]
        return header, [[self.met, self.swifttime, self.utctime, self.utcf]]

    @classmethod
    def frommet(cls, met, utcf=None, isutc=False):
        """Construct a swiftdatetime from a given MET and (optional) UTCF."""
        dt = datetime(2001, 1, 1) + timedelta(seconds=met)
        if isutc and utcf is not None:
            dt += timedelta(seconds=utcf)
        ret = cls(
            dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond
        )
        ret.utcf = utcf
        ret.isutc = isutc
        return ret

    # Attribute aliases
    swift = swifttime
    utc = utctime

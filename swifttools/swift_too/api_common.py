import json
import re
import textwrap

from typing import Any
import warnings
from datetime import date, datetime, timedelta, timezone


from pydantic import TypeAdapter
import requests
from dateutil import parser
from tabulate import tabulate

from swifttools.swift_too.swift_schemas import BaseSchema

from .version import version_tuple

# Make Warnings a little less weird
formatwarning_orig = warnings.formatwarning
warnings.formatwarning = lambda message, category, filename, lineno, line=None: formatwarning_orig(
    message, category, filename, lineno, line=""
)

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
    import astropy.units as u  # type: ignore[import-untyped]
    from astropy.time import Time  # type: ignore[import-untyped]

    HAS_ASTROPY = True
except ImportError:
    pass


# Convert degrees to radians
dtor = 0.017453292519943295

# Submission URL
API_URL = "https://www.swift.psu.edu/api/v1.2"
API_URL = "http://localhost:8000/api/v1.2"


def convert_to_dt(self, dt: Any) -> datetime:
    """Convert any datetime-like object to a datetime object."""
    tdt = TypeAdapter(datetime)
    return tdt.validate_python(dt).replace(tzinfo=None)


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
        tab += "".join([f"<th style='text-align: left;'>{head}</th>" for head in header])
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
    api_version: str = api_version
    username: str = "anonymous"
    _shared_secret: str = "anonymous"
    # Submission timeout
    _timeout: int = 120  # 2 mins
    # By default all API dates are in Swift Time
    _isutc: bool = False

    @property
    def shared_secret(self):
        if self._shared_secret is None and self.username != "anonymous":
            # Try to fetch password using keyring, if available
            if keyring_support:
                self._shared_secret = keyring.get_password("swifttools.swift_too", self.username)
            else:
                raise Exception("Warning: keyring support not available. Please set shared_secret manually.")
        elif self.username == "anonymous":
            return "anonymous"
        return self._shared_secret

    @shared_secret.setter
    def shared_secret(self, secret):
        if self.username != "anonymous" and (self.username is not None or self.username == ""):
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
            return "<b>Rejected with the following error(s): </b>" + " ".join(self.status.errors)
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
            return "Rejected with the following error(s): " + " ".join(self.status.errors)
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
                f"{row}='{getattr(self, row)}'"
                for row in self._parameters
                if getattr(self, row) is not None and getattr(self, row) != []
            ]
        )
        return f"{name}({args})"

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

    @property
    def submit_url(self):
        """Generate a URL that submits the TOO API request"""
        url = f"{API_URL}{self._endpoint}"
        return url

    @property
    def complete(self, post=True):
        """Check if a queued job is completed"""
        # Send request to TOO API server
        self.__submit_jwt(post=post)
        # Check the status of the request
        if self.status != "Queued" and self.status != "Processing":
            return True
        return False

    def _post_process(self):
        """Placeholder method. Things to do after values are returned from API."""
        pass

    def get(self):
        """Perform an API GET request to the server."""
        args = self._get_schema.model_validate(self).model_dump(exclude_none=True)
        response = requests.get(
            self.submit_url, params=args, timeout=self._timeout, auth=(self.username, self.shared_secret)
        )
        print(response.url)
        if response.status_code == 200:
            try:
                data = self._schema.model_validate(response.json())
                for key, value in data:
                    setattr(self, key, value)

            except Exception as e:
                self.__set_error(f"Error validating response: {e}")
                return False
        else:
            print("Sad trombone: ", response.status_code)
            return False
        return True


class swiftdatetime(datetime):
    """Extend datetime to store met, utcf and swifttime. Default value is UTC"""

    api_name: str = "swiftdatetime"
    _parameters: list[str] = ["met", "utcf", "swifttime", "utctime", "isutc"]

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
            if self.isutc != other.isutc and (self.utctime is None or other.utctime is None):
                raise ArithmeticError(
                    "Cannot subtract mismatched time zones with no UTCF"
                )  # FIXME - correct exception?

            if self.isutc is True and other.isutc is True or self.isutc is False and other.isutc is False:
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
        ret = cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
        ret.utcf = utcf
        ret.isutc = isutc
        return ret

    # Attribute aliases
    swift = swifttime
    utc = utctime

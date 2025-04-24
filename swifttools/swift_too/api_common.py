import textwrap
import warnings
from datetime import datetime
from typing import Any

import httpx
from pydantic import TypeAdapter
from tabulate import tabulate

from .swift_schemas import BaseSchema, SwiftTOOStatusSchema
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

    # Every request gets a status
    status: SwiftTOOStatusSchema = SwiftTOOStatusSchema()

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

    def _post_process(self):
        """Placeholder method. Things to do after values are returned from API."""
        pass

    def model_post_init(self, context: Any) -> None:
        if self.validate_get():
            self.submit()
        else:
            print("Error: Validation failed, please check parameters.")

    def submit(self):
        """Perform an API GET request to the server."""
        args = self._get_schema.model_validate(self).model_dump(exclude_none=True)
        response = httpx.get(
            self.submit_url, params=args, timeout=self._timeout, auth=(self.username, self.shared_secret)
        )
        print(response.url)
        # If the request was successful, parse the response
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
            #            self.__set_error(f"Error: {response.status_code} - {response.text}")
            return False

        # Perform processing of the response
        self._post_process()

        return True

    def validate_get(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        if not self._get_schema.model_validate(self):
            self.status.error("Validation failed.")
            return False
        return True

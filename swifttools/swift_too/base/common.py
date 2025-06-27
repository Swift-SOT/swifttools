import http.cookiejar
import textwrap
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from pydantic import TypeAdapter, ValidationError
from tabulate import tabulate

from ..version import version_tuple
from .status import SwiftTOOStatus

# Make Warnings a little less weird
formatwarning_orig = warnings.formatwarning
warnings.formatwarning = lambda message, category, filename, lineno, line=None: formatwarning_orig(
    message, category, filename, lineno, line=""
)

# Define the API version
api_version = f"{version_tuple[0]}.{version_tuple[1]}"

# Submission URL
API_URL = "https://www.swift.psu.edu/api/v1.2"
# API_URL = "http://localhost:8000/api/v1.2"
COOKIE_JAR_PATH = Path.home() / ".swift_too" / "cookies.txt"
COOKIE_JAR_PATH.parent.mkdir(parents=True, exist_ok=True)

# Create and optionally load cookies
cookie_jar = http.cookiejar.LWPCookieJar(COOKIE_JAR_PATH)
try:
    cookie_jar.load(ignore_discard=True)
except FileNotFoundError:
    pass


def convert_to_dt(dt: Any) -> datetime:
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


class TOOAPIBaseclass:
    """Mixin for TOO API Classes. Most of these are to do with reading and
    writing classes out as JSON/dicts."""

    # Set api_version for all classes
    api_name: str
    api_version: str = api_version
    username: str = "anonymous"
    shared_secret: str = "anonymous"
    # Submission timeout
    _timeout: int = 120  # 2 mins
    # By default all API dates are in Swift Time
    _isutc: bool
    autosubmit: bool = True
    _get_schema: Any = None
    _put_schema: Any = None
    _endpoint: str
    _post_schema: Any = None
    _delete_schema: Any = None

    # Every request gets a status
    status: SwiftTOOStatus = SwiftTOOStatus()

    def __init__(self, *args, **kwargs):
        # Convert positional arguments to keyword arguments
        if len(args) > 0 and hasattr(self, "_get_schema") and hasattr(self._get_schema, "model_fields"):
            for i, key in enumerate(self._get_schema.model_fields.keys()):
                print(i, key)
                if i < len(args):
                    kwargs[key] = args[i]
                else:
                    break
        print(kwargs)
        super().__init__(**kwargs)

    @property
    def _table(self):
        """Table of details of the class"""
        _parameters = self.__class__.model_fields.keys()
        header = ["Parameter", "Value"]
        table = []
        for row in _parameters:
            value = getattr(self, row)
            if value is not None and value != [] and value != "":
                if row == "status" and not isinstance(value, str):
                    table.append([row, value.status])
                elif isinstance(value, list):
                    table.append([row, "\n".join([f"{le}" for le in value])])
                else:
                    table.append([row, "\n".join(textwrap.wrap(f"{value}"))])
        return header, table

    def _repr_html_(self):
        if hasattr(self, "status") and self.status.status == "Rejected" and self.status.api_name == "Swift_TOO_Status":
            return "<b>Rejected with the following error(s): </b>" + " ".join(self.status.errors)
        else:
            header, table = self._table
            if len(table) > 0:
                return _tablefy(table, header)
            else:
                return "No data"

    def __str__(self):
        if hasattr(self, "status") and self.status.status == "Rejected" and self.status.api_name == "Swift_TOO_Status":
            return "Rejected with the following error(s): " + " ".join(self.status.errors)
        else:
            header, table = self._table
            if len(table) > 0:
                return tabulate(table, header, tablefmt="pretty", stralign="right")
            else:
                return "No data"

    def __repr__(self):
        args = ",".join(
            [
                f"{row}='{getattr(self, row)}'"
                for row in self._parameters
                if getattr(self, row) is not None and getattr(self, row) != []
            ]
        )
        return f"{self.api_name}({args})"

    def __set_status(self, newstatus):
        if hasattr(self, "status"):
            if isinstance(self.status, str):
                self.status = newstatus
            else:
                self.status.status = newstatus
        else:
            print(f"STATUS: {newstatus}")

    def __set_error(self, newerror):
        if hasattr(self, "status"):
            if isinstance(self.status, str):
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
        """
        Post-initialization hook for Pydantic models. The behavior of this
        is to perform a GET request on instantiation of the class, if the
        status is "Pending" and the class has a `_get_schema` attribute.
        """
        if self.status.status == "Pending" and hasattr(self, "_get_schema") and self.autosubmit is True:
            if self.validate_get(set_error=False):
                self.submit_get()

    def submit(self):
        """
        Submit the API request to the server. Right now it determines if the
        submission type is GET or POST, based on existance of the `_get_schema`
        or `_post_schema` attributes. If neither exist, it will return False.
        If the request is successful, it will update the class with the
        response data.

        Returns
        -------
        bool
            Was submission successful?
        """
        if self.status.status == "Pending":
            if hasattr(self, "_get_schema"):
                if self.validate_get():
                    return self.submit_get()
                return False
            elif hasattr(self, "_post_schema"):
                if self.validate_post():
                    return self.submit_post()
                return False
        return False

    def login(self, client: httpx.Client) -> bool:
        """
        Login to the server and set the session cookie.

        Parameters
        ----------
        client : httpx.Client
            The HTTP client to use for the request.
        """
        # Log into the API server using the username and shared secret.
        resp = client.post(f"{API_URL}/login", json={"username": self.username, "password": self.shared_secret})
        if resp.status_code != 200:
            return False
        return True

    def submit_get(self) -> bool:
        """Perform an API GET request to the server."""
        args = self._get_schema.model_validate(self.model_dump()).model_dump(exclude_none=True)

        with httpx.Client(cookies=cookie_jar) as client:
            # Login if no valid session cookie exists
            if not any(c.name == "session" and not c.is_expired() for c in cookie_jar) and self.username != "anonymous":
                if not self.login(client):
                    self.__set_error("Login failed. Please check your username and shared_secret.")
                    return False
                # Save the cookies to the cookie jar
                cookie_jar.save(ignore_discard=True)

            # Perform the GET request
            response = client.get(
                self.submit_url,
                params=args,
                timeout=self._timeout,
                follow_redirects=True,
            )

        print(response.url, response)
        # If the request was successful, parse the response
        if response.status_code == 200:
            pass
        elif response.status_code >= 400 and response.status_code < 500:
            # Assume that errors codes in the 400s will return status
            print("Sad trombone: ", response.status_code, response.text)
        else:
            # Catch all other errors
            print("Sad trombone: ", response.status_code, response.text)
            self.__set_error(f"Error: {response.status_code} - {response.text}")
            return False

        # Parse the response and update the class attributes
        try:
            data = self.model_validate(response.json())
            for key, value in data:
                setattr(self, key, value)
        except Exception as e:
            self.__set_error(f"Error validating response: {e}")
            return False

        # Perform processing of the response
        self._post_process()
        return True

    def submit_post(self):
        """Perform an API POST request to the server."""
        args = self._post_schema.model_validate(self.model_dump()).model_dump(exclude_none=True)

        with httpx.Client(cookies=cookie_jar) as client:
            # Login if no valid session cookie exists
            if not any(c.name == "session" and not c.is_expired() for c in cookie_jar) and self.username != "anonymous":
                if not self.login(client):
                    self.__set_error("Login failed. Please check your username and shared_secret.")
                    return False
                # Save the cookies to the cookie jar
                cookie_jar.save(ignore_discard=True)

            # Perform the POST request
            response = client.post(
                self.submit_url,
                json=args,
                timeout=self._timeout,
                follow_redirects=True,
            )
        print(response.url)
        # If the request was successful, parse the response
        if response.status_code == 200:
            try:
                data = self.model_validate(response.json())
                for key, value in dict(data).items():
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

    def validate_get(self, set_error=True):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """

        try:
            self._get_schema.model_validate(self)
        except ValidationError as e:
            if set_error:
                # Set error message if validation fails
                self.__set_error(f"Validation failed: {e}")
            return False
        return True

    def validate_post(self, set_error=True):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """

        try:
            self._post_schema.model_validate(self)
        except ValidationError as e:
            if set_error:
                # Set error message if validation fails
                self.__set_error(f"Validation failed: {e}")
            return False
        return True

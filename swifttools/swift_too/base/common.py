import http.cookiejar
import warnings
from pathlib import Path
from typing import Any

import httpx
from pydantic import ValidationError

from ..version import version_tuple
from .repr import TOOAPIReprMixin

# Always show deprecation warnings
warnings.simplefilter("always", DeprecationWarning)


# Make Warnings a little less weird
formatwarning_orig = warnings.formatwarning
warnings.formatwarning = lambda message, category, filename, lineno, line=None: formatwarning_orig(
    message, category, filename, lineno, line=""
)

# Define the API version
API_VERSION = f"{version_tuple[0]}.{version_tuple[1]}"

# Submission URL
API_URL = f"https://www.swift.psu.edu/api/v{API_VERSION}"

# Create and optionally load cookies
COOKIE_JAR_PATH = Path.home() / ".swift_too" / "cookies.txt"
COOKIE_JAR_PATH.parent.mkdir(parents=True, exist_ok=True)
cookie_jar = http.cookiejar.LWPCookieJar(COOKIE_JAR_PATH)
try:
    cookie_jar.load(ignore_discard=True)
except FileNotFoundError:
    pass


class TOOAPIBaseclass(TOOAPIReprMixin):
    """Mixin for TOO API Classes. Most of these are to do with reading and
    writing classes out as JSON/dicts."""

    username: str = "anonymous"
    shared_secret: str = "anonymous"
    # Submission timeout
    _timeout: int = 120  # 2 mins
    # By default all API dates are in Swift Time
    _isutc: bool
    autosubmit: bool = True
    _get_schema: Any
    _put_schema: Any
    _endpoint: str
    _post_schema: Any
    _delete_schema: Any

    # Provide backward compatibility for some arguments passed as kwargs
    _back_compat_args: dict = {
        "obs_id": ["obsnum", "obsid"],
        "target_id": ["targetid", "targid", "target_ID"],
        "target_name": ["targetname", "targname", "source_name"],
        "uvot_mode": ["uvotmode"],
        "xrt_mode": ["xrtmode"],
        "bat_mode": ["batmode"],
    }

    def __init__(self, *args, **kwargs):
        # Check if any of the arguments are in the back compatibility list, and
        # convert them to the correct keyword arguments.
        for key, values in self._back_compat_args.items():
            for value in values:
                if value in kwargs:
                    if key not in kwargs:
                        kwargs[key] = kwargs[value]
                    del kwargs[value]

        # Convert positional arguments to keyword arguments
        if (
            len(args) > 0
            and hasattr(self.__class__, "_get_schema")
            and hasattr(self.__class__._get_schema.default, "model_fields")
        ):
            for i, key in enumerate(self.__class__._get_schema.default.model_fields.keys()):
                if i < len(args):
                    kwargs[key] = args[i]
                else:
                    break
        print(kwargs)
        super().__init__(**kwargs)

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

        # If, ands and buts...
        if (
            hasattr(self, "status")
            and hasattr(self.status, "status")
            and not isinstance(self.status, str)
            and self.status.status == "Pending"
            and hasattr(self, "_get_schema")
            and self.autosubmit is True
        ):
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
        assert hasattr(self, "_schema"), "GET schema not defined for this API class."
        assert hasattr(self, "model_dump"), "Not a Pydantic model."
        args = self._get_schema.model_validate(self.model_dump(exclude={"__pydantic_extra__"})).model_dump(
            exclude_none=True
        )
        # Remove status from the arguments, as it is not needed for the GET request
        args.pop("status", None)

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
        print(response.url)
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
            data = self._schema.model_validate(response.json())
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
        args = self._post_schema.model_validate(self.model_dump(exclude={"__pydantic_extra__"})).model_dump(
            exclude_none=True
        )

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


class TOOAPIBackCompat:
    """Mixin to provide backward compatibility for some property names."""

    @property
    def targname(self) -> Any:
        if hasattr(self, "target_name"):
            return self.target_name
        return None

    @property
    def obsid(self) -> Any:
        if hasattr(self, "obs_id"):
            return self.obs_id
        return None

    @property
    def obsnum(self) -> Any:
        if hasattr(self, "obs_id"):
            return self.obs_id
        return None

    @property
    def source_name(self) -> Any:
        if hasattr(self, "target_name"):
            return self.target_name
        return None

    @property
    def uvotmode(self) -> Any:
        if hasattr(self, "uvot_mode"):
            return self.uvot_mode
        return None

    @property
    def xrtmode(self) -> Any:
        if hasattr(self, "xrt_mode"):
            return self.xrt_mode
        return None

    @property
    def batmode(self) -> Any:
        if hasattr(self, "bat_mode"):
            return self.bat_mode
        return None

    @property
    def xrt(self) -> Any:
        if hasattr(self, "xrt_mode"):
            return self.xrt_mode
        return None

    @property
    def uvot(self) -> Any:
        if hasattr(self, "uvot_mode"):
            return self.uvot_mode
        return None

    @property
    def bat(self) -> Any:
        if hasattr(self, "bat_mode"):
            return self.bat_mode
        return None

    @property
    def seg(self) -> Any:
        if hasattr(self, "segment"):
            return self.segment
        return None

    @property
    def ra_point(self) -> Any:
        if hasattr(self, "ra_object"):
            warnings.warn("ra_point is deprecated, please use ra_object instead.", DeprecationWarning, stacklevel=2)
            return self.ra_object
        return None

    @property
    def dec_point(self) -> Any:
        if hasattr(self, "dec_object"):
            warnings.warn("dec_point is deprecated, please use dec_object instead.", DeprecationWarning, stacklevel=2)
            return self.dec_object
        return None

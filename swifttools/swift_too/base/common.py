import http.cookiejar
import warnings
from typing import Any, Optional, Type

import httpx
from pydantic import BaseModel, ValidationError

from ..base.constants import (
    API_URL,
    COOKIE_JAR_PATH,
    HTTP_BAD_REQUEST,
    HTTP_OK,
    HTTP_SERVER_ERROR,
    SESSION_COOKIE_NAME,
    STATUS_PENDING,
)
from .repr import TOOAPIReprMixin

# Always show deprecation warnings
warnings.simplefilter("always", DeprecationWarning)


# Make Warnings a little less weird
formatwarning_orig = warnings.formatwarning
warnings.formatwarning = lambda message, category, filename, lineno, line=None: formatwarning_orig(
    message, category, filename, lineno, line=""
)

# Ensure cookie jar directory exists, and set up cookie jar
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
    # API base URL
    _api_base: str = API_URL
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
        # Handle backward compatibility and positional arguments
        kwargs = self._handle_back_compat_args(kwargs)
        kwargs = self._convert_positional_args(args, kwargs)
        super().__init__(**kwargs)

    def _handle_back_compat_args(self, kwargs: dict) -> dict:
        """Convert deprecated argument names to current names."""
        for key, deprecated_names in self._back_compat_args.items():
            for deprecated in deprecated_names:
                if deprecated in kwargs and key not in kwargs:
                    kwargs[key] = kwargs.pop(deprecated)
                elif deprecated in kwargs:
                    kwargs.pop(deprecated)
        return kwargs

    def _convert_positional_args(self, args: tuple, kwargs: dict) -> dict:
        """Convert positional arguments to keyword arguments based on schema."""
        if not args:
            return kwargs

        schema = self._get_schema_for_init()
        if schema and hasattr(schema, "model_fields"):
            field_names = list(schema.model_fields.keys())
            for i, arg in enumerate(args):
                if i < len(field_names):
                    field_name = field_names[i]
                    if field_name not in kwargs:
                        kwargs[field_name] = arg
        return kwargs

    def _get_schema_for_init(self) -> Optional[Type[BaseModel]]:
        """Get the appropriate schema for initialization."""
        schema_attr = getattr(self.__class__, "_get_schema", None) or getattr(self.__class__, "_post_schema", None)
        if hasattr(schema_attr, "default"):
            return schema_attr.default  # type: ignore[union-attr]
        return schema_attr

    def __set_error(self, newerror):
        if hasattr(self, "status"):
            if isinstance(self.status, str):
                self.error(newerror)
            else:
                self.status.error(newerror)
        else:
            print(f"ERROR: {newerror}")

    @staticmethod
    def _format_validation_error(error: ValidationError) -> str:
        """Format a Pydantic ValidationError into a concise message.

        Parameters
        ----------
        error : ValidationError
            The validation error to format.

        Returns
        -------
        str
            A concise error message.
        """
        errors = error.errors()
        if len(errors) == 1:
            err = errors[0]
            field = " -> ".join(str(loc) for loc in err["loc"]) if err["loc"] else "root"
            msg = err["msg"]
            return f"{field}: {msg}"
        else:
            # Multiple errors - list them concisely
            error_msgs = []
            for err in errors[:5]:  # Limit to first 5 errors
                field = " -> ".join(str(loc) for loc in err["loc"]) if err["loc"] else "root"
                error_msgs.append(f"{field}: {err['msg']}")
            result = "; ".join(error_msgs)
            if len(errors) > 5:
                result += f" (and {len(errors) - 5} more)"
            return result

    @property
    def submit_url(self):
        """Generate a URL that submits the TOO API request"""
        url = f"{self._api_base}{self._endpoint}"
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
        if self._should_autosubmit():
            if self.validate_get(set_error=False):
                self.submit_get()

    def _should_autosubmit(self) -> bool:
        """Check if automatic submission should occur."""
        if not self.autosubmit or not hasattr(self, "_get_schema"):
            return False
        if not hasattr(self, "status") or isinstance(self.status, str):
            return False
        return hasattr(self.status, "status") and self.status.status == STATUS_PENDING  # type: ignore[attr-defined]

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

    def _ensure_authenticated(self, client: httpx.Client) -> bool:
        """
        Ensure the client is authenticated. Login if needed.

        Parameters
        ----------
        client : httpx.Client
            The HTTP client to use for the request.

        Returns
        -------
        bool
            True if authenticated successfully, False otherwise.
        """
        # Skip login for anonymous users
        if self.username == "anonymous":
            return True

        # Check if we have a valid session cookie
        if any(c.name == SESSION_COOKIE_NAME and not c.is_expired() for c in cookie_jar):
            return True

        # Perform login
        try:
            resp = client.post(f"{API_URL}/login", json={"username": self.username, "password": self.shared_secret})
            if resp.status_code == HTTP_OK:
                cookie_jar.save(ignore_discard=True)
                return True
        except Exception as e:
            self.__set_error(f"Login failed: {e}")
            return False

        self.__set_error(f"Login failed with status code: {resp.status_code}")
        return False

    def submit_get(self) -> bool:
        """Perform an API GET request to the server."""
        assert hasattr(self, "_get_schema"), "GET schema not defined for this API class."
        assert hasattr(self, "model_dump"), "Not a Pydantic model."

        # Prepare request arguments
        args = self._get_schema.model_validate(self.model_dump(exclude={"__pydantic_extra__"})).model_dump(
            exclude_none=True
        )
        args.pop("status", None)

        with httpx.Client(cookies=cookie_jar) as client:
            if not self._ensure_authenticated(client):
                return False

            try:
                response = client.get(
                    self.submit_url,
                    params=args,
                    timeout=self._timeout,
                    follow_redirects=True,
                )
            except Exception as e:
                self.__set_error(f"Request failed: {e}")
                return False

        return self._handle_response(response)

    def submit_post(self) -> bool:
        """Perform an API POST request to the server."""
        assert hasattr(self, "_post_schema"), "POST schema not defined for this API class."
        assert hasattr(self, "model_dump"), "Not a Pydantic model."

        # Prepare request arguments
        args = self._post_schema.model_validate(self.model_dump(exclude={"__pydantic_extra__"})).model_dump(
            exclude_none=True
        )

        with httpx.Client(cookies=cookie_jar) as client:
            if not self._ensure_authenticated(client):
                return False

            try:
                response = client.post(
                    self.submit_url,
                    json=args,
                    timeout=self._timeout,
                    follow_redirects=True,
                )
            except Exception as e:
                self.__set_error(f"Request failed: {e}")
                return False

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> bool:
        """Handle API response and update object state.

        Parameters
        ----------
        response : httpx.Response
            The HTTP response to process.

        Returns
        -------
        bool
            True if response was handled successfully, False otherwise.
        """
        if response.status_code == HTTP_OK:
            try:
                data = self.model_validate(response.json())  # type: ignore[attr-defined]
                for key, value in dict(data).items():
                    setattr(self, key, value)
                self._post_process()
                return True
            except RecursionError:
                self.__set_error("Error validating response: maximum recursion depth exceeded")
            except Exception as e:
                self.__set_error(f"Error validating response: {e}")
        elif HTTP_BAD_REQUEST <= response.status_code < HTTP_SERVER_ERROR:
            self.__set_error(f"Client error {response.status_code}: {response.text}")
        else:
            self.__set_error(f"Server error {response.status_code}: {response.text}")

        return False

    def _validate_with_schema(self, schema: Type[BaseModel], set_error: bool = True) -> bool:
        """Validate data against a schema.

        Parameters
        ----------
        schema : Type[BaseModel]
            The Pydantic schema to validate against.
        set_error : bool, optional
            Whether to set error message on validation failure.

        Returns
        -------
        bool
            True if validation succeeded, False otherwise.
        """
        try:
            schema.model_validate(self.model_dump())  # type: ignore[attr-defined]
            return True
        except ValidationError as e:
            if set_error:
                concise_error = self._format_validation_error(e)
                self.__set_error(concise_error)
            return False

    def validate_get(self, set_error: bool = True) -> bool:
        """Validate for GET request.

        Parameters
        ----------
        set_error : bool, optional
            Whether to set error message on validation failure.

        Returns
        -------
        bool
            True if validation succeeded, False otherwise.
        """
        return self._validate_with_schema(self._get_schema, set_error)

    def validate_post(self, set_error: bool = True) -> bool:
        """Validate for POST request.

        Parameters
        ----------
        set_error : bool, optional
            Whether to set error message on validation failure.

        Returns
        -------
        bool
            True if validation succeeded, False otherwise.
        """
        return self._validate_with_schema(self._post_schema, set_error)

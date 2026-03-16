import http.cookiejar
import threading
import time
import warnings
from http import HTTPStatus
from typing import Any, Optional

import httpx
from pydantic import BaseModel, ValidationError

from ..base.constants import (
    API_URL,
    COOKIE_JAR_PATH,
    SESSION_COOKIE_NAME,
    STATUS_PENDING,
)
from .repr import TOOAPIReprMixin

# Always show deprecation warnings
warnings.simplefilter("always", DeprecationWarning)


def _parse_422_error(response_text: str) -> list[str]:
    """
    Parse a 422 Unprocessable Entity response into clean error messages.

    The API typically returns validation errors in JSON format with a 'detail' field
    containing an array of error objects with 'loc', 'msg', and 'type' fields.

    Parameters
    ----------
    response_text : str
        The raw response text from the API.

    Returns
    -------
    list[str]
        A list of formatted error messages.
    """
    import json

    try:
        data = json.loads(response_text)
        errors = []

        # Handle FastAPI/Pydantic validation error format
        if isinstance(data, dict) and "detail" in data:
            detail = data["detail"]

            # If detail is a string, return it directly
            if isinstance(detail, str):
                return [detail]

            # If detail is a list of validation errors
            if isinstance(detail, list):
                for error in detail:
                    if isinstance(error, dict):
                        # Extract field location (e.g., ['body', 'field_name'])
                        loc = error.get("loc", [])
                        # Get the field name (usually the last item in loc)
                        field = loc[-1] if loc else "unknown field"
                        # Get the error message
                        msg = error.get("msg", "validation error")

                        # Format as "field: message"
                        errors.append(f"{field}: {msg}")
                    else:
                        errors.append(str(error))

                return errors if errors else ["Validation error"]

        # Fallback: return the whole response as a single error
        return [response_text]

    except (json.JSONDecodeError, KeyError, IndexError):
        # If we can't parse it, return the raw text
        return [response_text]


def _format_422_errors(errors: list[str]) -> str:
    """
    Format a list of 422 validation errors into a readable string.

    Parameters
    ----------
    errors : list[str]
        List of error messages.

    Returns
    -------
    str
        Formatted error string.
    """
    if not errors:
        return "Validation error"

    if len(errors) == 1:
        return errors[0]

    # Multiple errors: format as a bulleted list
    return "Validation errors:\n" + "\n".join(f"  • {err}" for err in errors)


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
        object.__setattr__(self, "complete", False)

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

    def _schema_payload(self, schema: type[BaseModel]) -> dict[str, Any]:
        """Build a schema-limited payload including class attributes.

        Some request attributes (e.g., username/shared_secret) are declared on
        mixins and may not be Pydantic model fields. Include those values when
        the schema expects them.
        """
        assert hasattr(self, "model_dump"), "Not a Pydantic model."

        field_names = set(schema.model_fields.keys())
        payload = self.model_dump(include=field_names, exclude_none=True)  # type: ignore[attr-defined]

        # Ensure fields declared outside the Pydantic schema hierarchy are
        # still considered when required by the target schema.
        for field_name in field_names:
            if field_name in payload:
                continue
            value = getattr(self, field_name, None)
            if value is not None:
                payload[field_name] = value

        return payload

    def _get_schema_for_init(self) -> Optional[type[BaseModel]]:
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
            field = " -> ".join(str(loc) for loc in err["loc"]) if err["loc"] else "argument"
            msg = err["msg"]
            return f"{field}: {msg}"
        else:
            # Multiple errors - list them concisely
            error_msgs = []
            for err in errors[:5]:  # Limit to first 5 errors
                field = " -> ".join(str(loc) for loc in err["loc"]) if err["loc"] else "argument"
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

        # Check if data validates against the get schema
        if hasattr(self, "_get_schema"):
            try:
                self._get_schema.model_validate(self.model_dump(exclude={"__pydantic_extra__"}))  # type: ignore[attr-defined]
            except (ValidationError, TypeError):
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

    def queue(self):
        """
        Queue the API request to the server asynchronously. This method returns
        immediately after starting the request in a background thread. Once the
        response arrives, the object is updated with the results and the `complete`
        property is set to True.

        Returns
        -------
        bool
            True if the request was queued successfully, False otherwise.
        """
        if self.status.status == "Pending":
            if hasattr(self, "_get_schema"):
                if self.validate_get():
                    threading.Thread(target=self._submit_get_async, daemon=True).start()
                    threading.Thread(target=self._queue_watchdog, daemon=True).start()
                    return True
                return False
            elif hasattr(self, "_post_schema"):
                if self.validate_post():
                    threading.Thread(target=self._submit_post_async, daemon=True).start()
                    threading.Thread(target=self._queue_watchdog, daemon=True).start()
                    return True
                return False
        return False

    def _queue_watchdog(self) -> None:
        """Ensure queued async requests cannot block forever.

        If a background request does not set `complete` within a bounded
        interval, mark it complete and store a timeout error.
        """
        wait_seconds = max(int(self._timeout) + 5, 30)
        time.sleep(wait_seconds)
        if not getattr(self, "complete", False):
            self.__set_error(f"Asynchronous request timed out after {wait_seconds} seconds")
            object.__setattr__(self, "complete", True)

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
            if resp.status_code == HTTPStatus.OK:
                cookie_jar.save(ignore_discard=True)
                return True
        except Exception as e:
            self.__set_error(f"Login failed: {e}")
            return False

        self.__set_error("Login failed with status code. Please check your credentials.")
        return False

    def submit_get(self) -> bool:
        """Perform an API GET request to the server."""
        assert hasattr(self, "_get_schema"), "GET schema not defined for this API class."
        assert hasattr(self, "model_dump"), "Not a Pydantic model."

        # Prepare request arguments
        args = self._get_schema.model_validate(self._schema_payload(self._get_schema)).model_dump(exclude_none=True)
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
        payload = self._schema_payload(self._post_schema)
        args = self._post_schema.model_validate(payload).model_dump(exclude_none=True, mode="json")
        if not args:
            self.__set_error("Refusing to submit an empty POST payload.")
            return False
        with httpx.Client(cookies=cookie_jar) as client:
            if not self._ensure_authenticated(client):
                return False

            try:
                response = client.post(
                    self.submit_url,
                    data=args,
                    timeout=self._timeout,
                    follow_redirects=True,
                )
            except Exception as e:
                self.__set_error(f"Request failed: {e}")
                return False

        return self._handle_response(response)

    def _submit_get_async(self) -> None:
        """Perform an asynchronous API GET request to the server."""
        assert hasattr(self, "_get_schema"), "GET schema not defined for this API class."
        assert hasattr(self, "model_dump"), "Not a Pydantic model."

        # Prepare request arguments
        args = self._get_schema.model_validate(self._schema_payload(self._get_schema)).model_dump(exclude_none=True)
        args.pop("status", None)

        with httpx.Client(cookies=cookie_jar) as client:
            if not self._ensure_authenticated(client):
                object.__setattr__(self, "complete", True)
                return

            try:
                response = client.get(
                    self.submit_url,
                    params=args,
                    timeout=self._timeout,
                    follow_redirects=True,
                )
            except Exception as e:
                self.__set_error(f"Request failed: {e}")
                object.__setattr__(self, "complete", True)
                return
        self._handle_response_async(response)

    def _submit_post_async(self) -> None:
        """Perform an asynchronous API POST request to the server."""
        assert hasattr(self, "_post_schema"), "POST schema not defined for this API class."
        assert hasattr(self, "model_dump"), "Not a Pydantic model."

        # Prepare request arguments
        payload = self._schema_payload(self._post_schema)
        args = self._post_schema.model_validate(payload).model_dump(exclude_none=True, mode="json")
        if not args:
            self.__set_error("Refusing to submit an empty POST payload.")
            object.__setattr__(self, "complete", True)
            return
        with httpx.Client(cookies=cookie_jar) as client:
            if not self._ensure_authenticated(client):
                object.__setattr__(self, "complete", True)
                return

            try:
                response = client.post(
                    self.submit_url,
                    data=args,
                    timeout=self._timeout,
                    follow_redirects=True,
                )
            except Exception as e:
                self.__set_error(f"Request failed: {e}")
                object.__setattr__(self, "complete", True)
                return

        self._handle_response_async(response)

    def _handle_response_async(self, response: httpx.Response):
        """Handle API response asynchronously and update object state.

        Parameters
        ----------
        response : httpx.Response
            The HTTP response to process.
        """
        self._handle_response(response)
        object.__setattr__(self, "complete", True)

    @staticmethod
    def _normalize_response_payload(payload: Any) -> Any:
        """Normalize API response payloads for model validation.

        Some endpoints return a bare string in ``status`` (e.g., "Validated")
        instead of a full status object. Convert that into a dict shape expected
        by models using ``TOOStatus``.
        """
        if not isinstance(payload, dict):
            return payload

        status_value = payload.get("status")
        if not isinstance(status_value, str):
            return payload

        normalized = dict(payload)
        status_payload: dict[str, Any] = {"status": status_value}

        # Preserve common status fields when the API returns them at top level.
        for key in ("errors", "warnings", "too_id", "jobnumber"):
            value = normalized.get(key)
            if value is not None:
                status_payload[key] = value

        normalized["status"] = status_payload
        return normalized

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
        if (
            isinstance(response.status_code, int)
            and HTTPStatus.OK <= response.status_code < HTTPStatus.MULTIPLE_CHOICES
        ):
            try:
                payload = self._normalize_response_payload(response.json())
                data = self.model_validate(payload)  # type: ignore[attr-defined]
                # Merge only fields explicitly returned by the API response.
                # This prevents partial responses (e.g., validate-only status
                # payloads) from wiping request fields back to defaults.
                if isinstance(payload, dict):
                    for field_name, field_info in data.__class__.model_fields.items():  # type: ignore[attr-defined]
                        if field_name in payload or (field_info.alias and field_info.alias in payload):
                            object.__setattr__(self, field_name, getattr(data, field_name))
                else:
                    for field_name in data.model_fields_set:  # type: ignore[attr-defined]
                        object.__setattr__(self, field_name, getattr(data, field_name))
                self._post_process()
                return True
            except Exception as e:
                self.__set_error(f"Error validating response: {e}")
        elif response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
            # Parse 422 validation errors into clean format
            errors = _parse_422_error(response.text)
            error_msg = _format_422_errors(errors)
            self.__set_error(error_msg)
        elif response.status_code == HTTPStatus.UNAUTHORIZED:
            self.__set_error("Authentication failed: Invalid username or shared secret.")
        elif (
            isinstance(response.status_code, int)
            and HTTPStatus.BAD_REQUEST <= response.status_code < HTTPStatus.INTERNAL_SERVER_ERROR
        ):
            self.__set_error(f"Client error {response.status_code}: {response.text}")
        elif isinstance(response.status_code, int):
            self.__set_error(f"Server error {response.status_code}: {response.text}")
        else:
            # Handle non-integer status codes (e.g., mocks)
            self.__set_error(f"Error: {response.text}")

        return False

    def _validate_with_schema(self, schema: type[BaseModel], set_error: bool = True) -> bool:
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
            schema.model_validate(self._schema_payload(schema))
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

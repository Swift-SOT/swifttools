import datetime as dt
from datetime import datetime
from unittest.mock import patch

import pytest
from mock import MagicMock
from pydantic import BaseModel

from swifttools.swift_too.base.common import TOOAPIBaseclass
from swifttools.swift_too.base.functions import _tablefy
from swifttools.swift_too.base.status import TOOStatus
from swifttools.swift_too.swift.schemas import BaseSchema


# Fixtures for datetime tests
@pytest.fixture
def dt_naive():
    return datetime(2023, 1, 15, 12, 30, 45)


@pytest.fixture
def dt_str():
    return "2023-01-15T12:30:45"


@pytest.fixture
def dt_tzaware():
    return datetime(2023, 1, 15, 12, 30, 45, tzinfo=dt.timezone.utc)


# Fixtures for tablefy tests
@pytest.fixture
def table_with_header():
    return [["row1col1", "row1col2"], ["row2col1", "row2col2"]]


@pytest.fixture
def header():
    return ["Header1", "Header2"]


@pytest.fixture
def table_no_header():
    return [["data1", "data2"]]


@pytest.fixture
def table_with_newlines():
    return [["line1\nline2", "single"]]


# Fixtures for HTTP response mocks
@pytest.fixture
def mock_response_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"field1": "updated_value", "field2": 200}
    mock_response.url = "http://test.com/api"
    return mock_response


@pytest.fixture
def mock_response_500():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.url = "http://test.com/api"
    return mock_response


@pytest.fixture
def mock_response_400():
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_response.url = "http://test.com/api"
    return mock_response


@pytest.fixture
def mock_response_invalid_json():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"invalid": "data"}
    mock_response.url = "http://test.com/api"
    return mock_response


# Fixtures for simple schema classes
@pytest.fixture
def simple_get_schema():
    class SimpleGetSchema(BaseSchema):
        field1: str = "default1"
        field2: int = 42

    return SimpleGetSchema


@pytest.fixture
def simple_post_schema():
    class SimplePostSchema(BaseSchema):
        field1: str = "default1"
        field2: int = 42

    return SimplePostSchema


class TestTablefy:
    def test_tablefy_with_header(self, table_with_header, header):
        """Test _tablefy with header and data."""
        result = _tablefy(table_with_header, header)

        assert "<table>" in result
        assert "<thead>" in result
        assert "<th style='text-align: left;'>Header1</th>" in result
        assert "<th style='text-align: left;'>Header2</th>" in result
        assert "<td style='text-align: left;'>row1col1</td>" in result

    def test_tablefy_without_header(self, table_no_header):
        """Test _tablefy without header."""
        result = _tablefy(table_no_header)

        assert "<table>" in result
        assert "<thead>" not in result
        assert "<td style='text-align: left;'>data1</td>" in result

    def test_tablefy_with_newlines(self, table_with_newlines):
        """Test _tablefy replaces newlines with <br>."""
        result = _tablefy(table_with_newlines)

        assert "line1<br>line2" in result


class TestTOOAPIBaseclassInit:
    def test_init_with_no_args(self):
        """Test __init__ with no arguments."""

        class MockTOOAPI(TOOAPIBaseclass, BaseModel):
            field1: str = "default1"
            field2: int = 42
            status: TOOStatus = TOOStatus()

        instance = MockTOOAPI()
        assert instance.field1 == "default1"
        assert instance.field2 == 42

    def test_init_with_positional_args(self, simple_get_schema):
        """Test __init__ converts positional arguments to keyword arguments."""

        class MockTOOAPIGetSchema(simple_get_schema):
            pass

        class MockTOOAPI(TOOAPIBaseclass, BaseModel):
            field1: str = "default1"
            field2: int = 42
            _get_schema = MockTOOAPIGetSchema
            _endpoint: str = "/mock/endpoint"

        instance = MockTOOAPI("test_value", 100, autosubmit=False)
        assert instance.field1 == "test_value"
        assert instance.field2 == 100

    def test_init_with_mixed_args_and_kwargs(self, simple_get_schema):
        """Test __init__ with both positional and keyword arguments."""

        class MockTOOAPIGetSchema(simple_get_schema):
            field3: str = "default3"
            _get_schema = None

        class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
            _get_schema = MockTOOAPIGetSchema

        instance = MockTOOAPI("pos_value", field3="kwarg_value", autosubmit=False)
        assert instance.field1 == "pos_value"
        assert instance.field2 == 42  # default value
        assert instance.field3 == "kwarg_value"

    def test_init_with_excess_positional_args(self, simple_get_schema):
        """Test __init__ ignores excess positional arguments."""

        class MockTOOAPIGetSchema(simple_get_schema):
            pass

        class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
            _get_schema = MockTOOAPIGetSchema

        # Provide more positional args than fields
        instance = MockTOOAPI("value1", 100, "excess_arg", 999, autosubmit=False)
        assert instance.field1 == "value1"
        assert instance.field2 == 100


class TestTOOAPIBaseclassSubmitPost:
    def test_submit_post_success(self, mock_response_success):
        """Test successful POST submission."""
        with patch("swifttools.swift_too.base.common.httpx.post", return_value=mock_response_success) as mock_post:

            class MockTOOAPIPostSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIPostSchema):
                _post_schema = MockTOOAPIPostSchema
                _endpoint: str = "/mock/endpoint"

            instance = MockTOOAPI("test_value", 100, autosubmit=False)

            result = instance.submit_post()

            assert result is True
            mock_post.assert_called_once()

    def test_submit_post_http_error(self, mock_response_500):
        """Test POST submission with HTTP error."""
        with patch("swifttools.swift_too.base.common.httpx.post", return_value=mock_response_500) as mock_post:

            class MockTOOAPIPostSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIPostSchema):
                _post_schema = MockTOOAPIPostSchema
                _endpoint: str = "/mock/endpoint"

            instance = MockTOOAPI("test_value", 100, autosubmit=False)

            result = instance.submit_post()

            assert result is False
            mock_post.assert_called_once()

    def test_submit_post_validation_error(self, mock_response_invalid_json):
        """Test POST submission with validation error in response."""
        with patch("swifttools.swift_too.base.common.httpx.post", return_value=mock_response_invalid_json) as mock_post:

            class MockTOOAPIPostSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIPostSchema):
                _post_schema = MockTOOAPIPostSchema
                _endpoint: str = "/mock/endpoint"

                def model_validate(self):
                    """Mock validation method that raises an exception."""
                    raise Exception("Validation error")

            instance = MockTOOAPI("test_value", 100, autosubmit=False)

            result = instance.submit_post()

            assert result is False
            mock_post.assert_called_once()

    def test_submit_post_calls_post_process(self, mock_response_success):
        """Test that submit_post calls _post_process on success."""
        with patch("swifttools.swift_too.base.common.httpx.post", return_value=mock_response_success):

            class MockTOOAPIPostSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIPostSchema):
                _post_schema = MockTOOAPIPostSchema
                _endpoint: str = "/mock/endpoint"

            instance = MockTOOAPI("test_value", 100, autosubmit=False)

            result = instance.submit_post()

            assert result is True

    def test_submit_post_uses_correct_parameters(self, mock_response_success):
        with patch("swifttools.swift_too.base.common.httpx.post", return_value=mock_response_success) as mock_post:

            class MockTOOAPIPostSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIPostSchema):
                _post_schema = MockTOOAPIPostSchema
                _endpoint: str = "/mock/endpoint"

            instance = MockTOOAPI(
                field1="test_value", field2=100, autosubmit=False, username="testuser", shared_secret="testsecret"
            )

            _ = instance.submit_post()

            expected_url = "http://localhost:8000/api/v1.2/mock/endpoint"
            expected_json = {"field1": "test_value", "field2": 100}

            mock_post.assert_called_once_with(
                expected_url, json=expected_json, timeout=120, auth=("testuser", "testsecret")
            )


class TestTOOAPIBaseclassSubmit:
    def test_submit_get_with_pending_status_and_valid_data(self):
        """Test submit calls submit_get when status is Pending and _get_schema exists."""

        class MockTOOAPIGetSchema(BaseSchema):
            field1: str = "default1"
            field2: int = 42
            _validate_get_called: bool = False
            _submit_get_called: bool = False

        class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
            _schema = MockTOOAPIGetSchema
            _endpoint: str = "/mock/endpoint"
            status: TOOStatus = TOOStatus()

            def validate_get(self, set_error=True):
                """Mock validation method that always returns True."""
                self._validate_get_called = True
                return True

            def submit_get(self):
                """Mock submit_get method that always returns True."""
                self._submit_get_called = True
                return True

        instance = MockTOOAPI("test_value", 100, autosubmit=False)

        result = instance.submit()

        assert instance._validate_get_called
        assert instance._submit_get_called
        assert result is True

    def test_submit_get_with_validation_failure(self):
        """Test submit returns False when GET validation fails."""

        class MockTOOAPIGetSchema(BaseSchema):
            field1: str = "default1"
            field2: int = 42
            _validate_get_called: bool = False
            _submit_get_called: bool = False

        class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
            _schema = MockTOOAPIGetSchema
            _endpoint: str = "/mock/endpoint"
            status: TOOStatus = TOOStatus()

            def validate_get(self, set_error=True):
                """Mock validation method that always returns False."""
                self._validate_get_called = True
                return False

            def submit_get(self):
                """Mock submit_get method that should not be called."""
                self._submit_get_called = True
                return True

        instance = MockTOOAPI("test_value", 100, autosubmit=False)

        result = instance.submit()

        assert instance._validate_get_called
        assert not instance._submit_get_called
        assert result is False

    def test_submit_post_with_pending_status_and_valid_data(self):
        """Test submit calls submit_post when status is Pending and _post_schema exists."""

        class MockTOOAPIPostSchema(BaseSchema):
            field1: str = "default1"
            field2: int = 42
            _validate_post_called: bool = False
            _submit_post_called: bool = False

        class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIPostSchema):
            _post_schema = MockTOOAPIPostSchema
            _endpoint: str = "/mock/endpoint"
            status: TOOStatus = TOOStatus()

            def validate_post(self, set_error=True):
                """Mock validation method that always returns True."""
                self._validate_post_called = True
                return True

            def submit_post(self):
                """Mock submit_post method that always returns True."""
                self._submit_post_called = True
                return True

        instance = MockTOOAPI("test_value", 100, autosubmit=False)
        result = instance.submit()

        assert instance._validate_post_called
        assert instance._submit_post_called
        assert result is True

    def test_submit_post_with_validation_failure(self):
        """Test submit returns False when POST validation fails."""

        class MockTOOAPIPostSchema(BaseSchema):
            field1: str = "default1"
            field2: int = 42

        class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIPostSchema):
            _post_schema = MockTOOAPIPostSchema
            _endpoint: str = "/mock/endpoint"
            status: TOOStatus = TOOStatus()

        instance = MockTOOAPI("test_value", 100, autosubmit=False)

        with patch(
            "swifttools.swift_too.base.common.TOOAPIBaseclass.validate_post", return_value=False
        ) as mock_validate:
            with patch("swifttools.swift_too.base.common.TOOAPIBaseclass.submit_post") as mock_submit_post:
                result = instance.submit()

                mock_validate.assert_called_once()
                mock_submit_post.assert_not_called()
                assert result is False

    def test_submit_with_non_pending_status(self):
        """Test submit returns False when status is not Pending."""

        with (
            patch(
                "swifttools.swift_too.base.common.TOOAPIBaseclass.validate_get", return_value=True
            ) as mock_validate_get,
            patch(
                "swifttools.swift_too.base.common.TOOAPIBaseclass.validate_post", return_value=True
            ) as mock_validate_post,
            patch("swifttools.swift_too.base.common.TOOAPIBaseclass.submit_get", return_value=True) as mock_submit_get,
            patch(
                "swifttools.swift_too.base.common.TOOAPIBaseclass.submit_post", return_value=True
            ) as mock_submit_post,
        ):

            class MockTOOAPIGetSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
                _schema = MockTOOAPIGetSchema
                _get_schema = MockTOOAPIGetSchema
                _endpoint: str = "/mock/endpoint"
                status: TOOStatus = TOOStatus(status="Completed")

            instance = MockTOOAPI("test_value", 100, autosubmit=False)
            result = instance.submit()
            mock_validate_get.assert_not_called()
            mock_validate_post.assert_not_called()
            mock_submit_get.assert_not_called()
            mock_submit_post.assert_not_called()
            assert result is False

    def test_submit_without_schema(self):
        """Test submit returns False when neither _get_schema nor _post_schema exist."""

        class MockTOOAPI(TOOAPIBaseclass, BaseModel):
            field1: str = "default1"
            field2: int = 42
            status: TOOStatus = TOOStatus()

        instance = MockTOOAPI("test_value", 100, autosubmit=False)

        result = instance.submit()
        assert result is False

    def test_submit_prefers_get_over_post(self, simple_get_schema, simple_post_schema):
        """Test submit prefers GET when both _get_schema and _post_schema exist."""

        class MockTOOAPIGetSchema(simple_get_schema):
            pass

        class MockTOOAPIPostSchema(simple_post_schema):
            pass

        class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
            _schema = MockTOOAPIGetSchema
            _get_schema = MockTOOAPIGetSchema
            _post_schema = MockTOOAPIPostSchema
            _endpoint: str = "/mock/endpoint"
            status: TOOStatus = TOOStatus()

        instance = MockTOOAPI("test_value", 100, autosubmit=False)

        with (
            patch(
                "swifttools.swift_too.base.common.TOOAPIBaseclass.validate_get", return_value=True
            ) as mock_validate_get,
            patch("swifttools.swift_too.base.common.TOOAPIBaseclass.validate_post") as mock_validate_post,
            patch("swifttools.swift_too.base.common.TOOAPIBaseclass.submit_get", return_value=True) as mock_submit_get,
            patch(
                "swifttools.swift_too.base.common.TOOAPIBaseclass.submit_post", return_value=True
            ) as mock_submit_post,
        ):
            result = instance.submit()

            mock_validate_get.assert_called_once()
            mock_validate_post.assert_not_called()
            mock_submit_get.assert_called_once()
            mock_submit_post.assert_not_called()
            assert result is True

    def test_submit_get_client_error(self, mock_response_400):
        """Test GET submission with 4xx client error."""
        with patch("swifttools.swift_too.base.common.httpx.get", return_value=mock_response_400) as mock_get:

            class MockTOOAPIGetSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
                _schema = MockTOOAPIGetSchema
                _get_schema = MockTOOAPIGetSchema
                _endpoint: str = "/mock/endpoint"
                status: TOOStatus = TOOStatus()

            instance = MockTOOAPI("test_value", 100, autosubmit=False)

            result = instance.submit_get()

            assert result is False
            mock_get.assert_called_once()

    def test_submit_get_server_error(self, mock_response_500):
        """Test GET submission with 5xx server error."""
        with patch("swifttools.swift_too.base.common.httpx.get", return_value=mock_response_500) as mock_get:

            class MockTOOAPIGetSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
                _schema = MockTOOAPIGetSchema
                _get_schema = MockTOOAPIGetSchema
                _endpoint: str = "/mock/endpoint"
                status: TOOStatus = TOOStatus()

            instance = MockTOOAPI("test_value", 100, autosubmit=False)

            result = instance.submit_get()

            assert result is False
            mock_get.assert_called_once()

    def test_submit_get_validation_error(self, mock_response_invalid_json):
        """Test GET submission with validation error in response."""
        with patch("swifttools.swift_too.base.common.httpx.get", return_value=mock_response_invalid_json) as mock_get:

            class MockTOOAPIGetSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
                _schema = MockTOOAPIGetSchema
                _get_schema = MockTOOAPIGetSchema
                _endpoint: str = "/mock/endpoint"
                status: TOOStatus = TOOStatus()

                def model_validate(self, data):
                    """Mock validation method that raises an exception."""
                    raise Exception("Validation error")

            instance = MockTOOAPI("test_value", 100, autosubmit=False)

            result = instance.submit_get()

            assert result is False
            mock_get.assert_called_once()

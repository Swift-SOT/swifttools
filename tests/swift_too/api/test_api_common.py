import datetime as dt
from datetime import datetime
from unittest.mock import patch

from mock import MagicMock
from pydantic import BaseModel

from swifttools.swift_too.api_common import TOOAPIBaseclass, _tablefy, convert_to_dt
from swifttools.swift_too.swift_schemas import BaseSchema


class TestConvertToDt:
    def test_convert_to_dt_with_datetime(self):
        """Test that convert_to_dt handles datetime objects."""
        dt = datetime(2023, 1, 15, 12, 30, 45)
        result = convert_to_dt(dt)
        assert result == datetime(2023, 1, 15, 12, 30, 45)
        assert result.tzinfo is None

    def test_convert_to_dt_with_string(self):
        """Test that convert_to_dt handles string representations."""
        dt_str = "2023-01-15T12:30:45"
        result = convert_to_dt(dt_str)
        assert result == datetime(2023, 1, 15, 12, 30, 45)

    def test_convert_to_dt_with_timezone_aware(self):
        """Test that convert_to_dt removes timezone info."""
        tz_aware = datetime(2023, 1, 15, 12, 30, 45, tzinfo=dt.timezone.utc)
        result = convert_to_dt(tz_aware)
        assert result.tzinfo is None


class TestTablefy:
    def test_tablefy_with_header(self):
        """Test _tablefy with header and data."""
        table = [["row1col1", "row1col2"], ["row2col1", "row2col2"]]
        header = ["Header1", "Header2"]
        result = _tablefy(table, header)

        assert "<table>" in result
        assert "<thead>" in result
        assert "<th style='text-align: left;'>Header1</th>" in result
        assert "<th style='text-align: left;'>Header2</th>" in result
        assert "<td style='text-align: left;'>row1col1</td>" in result

    def test_tablefy_without_header(self):
        """Test _tablefy without header."""
        table = [["data1", "data2"]]
        result = _tablefy(table)

        assert "<table>" in result
        assert "<thead>" not in result
        assert "<td style='text-align: left;'>data1</td>" in result

    def test_tablefy_with_newlines(self):
        """Test _tablefy replaces newlines with <br>."""
        table = [["line1\nline2", "single"]]
        result = _tablefy(table)

        assert "line1<br>line2" in result


class TestTOOAPIBaseclassInit:
    def test_init_with_no_args(self):
        """Test __init__ with no arguments."""
        # Create a mock class that inherits from TOOAPIBaseclass

        class MockTOOAPI(TOOAPIBaseclass, BaseModel):
            field1: str = "default1"
            field2: int = 42

        instance = MockTOOAPI()
        assert instance.field1 == "default1"
        assert instance.field2 == 42

    def test_init_with_positional_args(self):
        """Test __init__ converts positional arguments to keyword arguments."""

        class MockTOOAPIGetSchema(BaseSchema):
            field1: str = "default1"
            field2: int = 42

        class MockTOOAPI(TOOAPIBaseclass, BaseModel):
            field1: str = "default1"
            field2: int = 42
            _get_schema = MockTOOAPIGetSchema
            _endpoint: str = "/mock/endpoint"

        instance = MockTOOAPI("test_value", 100, autosubmit=False)
        assert instance.field1 == "test_value"
        assert instance.field2 == 100

    def test_init_with_mixed_args_and_kwargs(self):
        """Test __init__ with both positional and keyword arguments."""

        # Create a mock class that inherits from TOOAPIBaseclass
        class MockTOOAPIGetSchema(BaseSchema):
            field1: str = "default1"
            field2: int = 42
            field3: str = "default3"
            _get_schema = None

        class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
            _get_schema = MockTOOAPIGetSchema

        instance = MockTOOAPI("pos_value", field3="kwarg_value", autosubmit=False)
        assert instance.field1 == "pos_value"
        assert instance.field2 == 42  # default value
        assert instance.field3 == "kwarg_value"

    def test_init_with_excess_positional_args(self):
        """Test __init__ ignores excess positional arguments."""

        class MockTOOAPIGetSchema(BaseSchema):
            field1: str = "default1"
            field2: int = 42

        class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIGetSchema):
            _get_schema = MockTOOAPIGetSchema

        # Provide more positional args than fields
        instance = MockTOOAPI("value1", 100, "excess_arg", 999, autosubmit=False)
        assert instance.field1 == "value1"
        assert instance.field2 == 100


class TestTOOAPIBaseclassSubmitPost:
    def test_submit_post_success(self):
        """Test successful POST submission."""
        # Mock requests.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"field1": "updated_value", "field2": 200}
        mock_response.url = "http://test.com/api"
        with patch("swifttools.swift_too.api_common.requests.post", return_value=mock_response) as mock_post:

            class MockTOOAPIPostSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIPostSchema):
                _post_schema = MockTOOAPIPostSchema
                _endpoint: str = "/mock/endpoint"

            instance = MockTOOAPI("test_value", 100, autosubmit=False)

            # Mock model_validate to return a dict-like object
            mock_validate = patch.object(instance, "model_validate")
            mock_validate.return_value = {"field1": "updated_value", "field2": 200}

            result = instance.submit_post()

            assert result is True
            mock_post.assert_called_once()
            assert instance.field1 == "updated_value"
            assert instance.field2 == 200

    def test_submit_post_http_error(self):
        """Test POST submission with HTTP error."""
        # Mock requests.post
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.url = "http://test.com/api"
        with patch("swifttools.swift_too.api_common.requests.post", return_value=mock_response) as mock_post:

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

    def test_submit_post_validation_error(self):
        """Test POST submission with validation error in response."""
        # Mock requests.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "data"}
        mock_response.url = "http://test.com/api"
        with patch("swifttools.swift_too.api_common.requests.post", return_value=mock_response) as mock_post:

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

    def test_submit_post_calls_post_process(self):
        """Test that submit_post calls _post_process on success."""
        # Mock requests.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"field1": "updated_value", "field2": 200}
        mock_response.url = "http://test.com/api"
        with patch("swifttools.swift_too.api_common.requests.post", return_value=mock_response):

            class MockTOOAPIPostSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIPostSchema):
                _post_schema = MockTOOAPIPostSchema
                _endpoint: str = "/mock/endpoint"

            instance = MockTOOAPI("test_value", 100, autosubmit=False)

            # Mock model_validate and _post_process
            mock_validate = patch.object(instance, "model_validate")
            mock_validate.return_value = {"field1": "updated_value", "field2": 200}

            result = instance.submit_post()

            assert result is True

    def test_submit_post_uses_correct_parameters(self):
        """Test that submit_post uses correct URL, auth, and JSON data."""
        # Mock requests.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"field1": "updated_value", "field2": 200}
        mock_response.url = "http://test.com/api"
        with patch("swifttools.swift_too.api_common.requests.post", return_value=mock_response) as mock_post:

            class MockTOOAPIPostSchema(BaseSchema):
                field1: str = "default1"
                field2: int = 42

            class MockTOOAPI(TOOAPIBaseclass, MockTOOAPIPostSchema):
                _post_schema = MockTOOAPIPostSchema
                _endpoint: str = "/mock/endpoint"

            instance = MockTOOAPI(
                field1="test_value", field2=100, autosubmit=False, username="testuser", shared_secret="testsecret"
            )

            # Mock model_validate
            # mock_validate = patch.object(instance, "model_validate")
            # mock_validate.return_value = {"field1": "updated_value", "field2": 200}

            _ = instance.submit_post()

            # Verify the POST request was made with correct parameters
            expected_url = "http://localhost:8000/api/v1.2/mock/endpoint"
            expected_json = {"field1": "test_value", "field2": 100}

            mock_post.assert_called_once_with(
                expected_url, json=expected_json, timeout=120, auth=("testuser", "testsecret")
            )

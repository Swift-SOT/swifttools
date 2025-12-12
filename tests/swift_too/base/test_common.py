from unittest.mock import Mock, patch

from pydantic import BaseModel, ValidationError

from swifttools.swift_too.base.common import (
    API_URL,
    TOOAPIBaseclass,
)
from swifttools.swift_too.base.status import TOOStatus


class MockSchema(BaseModel):
    """Mock schema for testing"""

    field1: str = "default"
    field2: int = 42


class TestTOOAPIBaseclass:
    """Tests for TOOAPIBaseclass"""

    def test_init_with_backward_compat_args(self):
        """Test backward compatibility argument conversion"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            target_id: int = 0
            target_name: str = ""
            status: TOOStatus = TOOStatus()

        obj = TestAPI(targid=123, targetname="Test", autosubmit=False)
        assert obj.target_id == 123
        assert obj.target_name == "Test"

    def test_init_removes_old_args(self):
        """Test that old backward compat args are removed from kwargs"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            target_id: int = 0
            status: TOOStatus = TOOStatus()

        obj = TestAPI(obsnum=456, target_id=123, autosubmit=False)
        assert obj.target_id == 123

    def test_init_with_positional_args(self):
        """Test conversion of positional arguments to keyword arguments"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            field1: str
            field2: int
            status: TOOStatus = TOOStatus()
            _get_schema: type = MockSchema

        obj = TestAPI("test", 99, autosubmit=False)
        assert obj.field1 == "test"
        assert obj.field2 == 99

    def test_submit_url_property(self):
        """Test submit_url property generates correct URL"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            _endpoint: str = "/test"
            status: TOOStatus = TOOStatus()

        obj = TestAPI(autosubmit=False)
        assert obj.submit_url == f"{API_URL}/test"

    def test_set_error_with_status_string(self, capsys):
        """Test error setting when status is a string"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            status: TOOStatus = TOOStatus()

        obj = TestAPI(autosubmit=False)
        obj.status.error("Initial error")

        assert "Initial error" in obj.status.errors

    def test_set_error_with_status_object(self):
        """Test error setting when status is an object"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            status: TOOStatus = TOOStatus()

        obj = TestAPI(autosubmit=False)
        obj._TOOAPIBaseclass__set_error("Test error")
        assert "Test error" in obj.status.errors

    def test_set_error_without_status(self, capsys):
        """Test error setting when no status attribute exists"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            pass

        obj = TestAPI(autosubmit=False)
        obj._TOOAPIBaseclass__set_error("Test error")
        captured = capsys.readouterr()
        assert "ERROR: Test error" in captured.out

    @patch("httpx.Client")
    def test_login_success(self, mock_client):
        """Test successful login"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            username: str = "testuser"
            shared_secret: str = "testsecret"
            status: TOOStatus = TOOStatus()

        obj = TestAPI(autosubmit=False)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client_instance = mock_client.return_value.__enter__.return_value
        mock_client_instance.post.return_value = mock_response

        result = obj.login(mock_client_instance)
        assert result is True
        mock_client_instance.post.assert_called_once()

    @patch("httpx.Client")
    def test_login_failure(self, mock_client):
        """Test failed login"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            username: str = "testuser"
            shared_secret: str = "wrongsecret"
            status: TOOStatus = TOOStatus()

        obj = TestAPI(autosubmit=False)
        mock_response = Mock()
        mock_response.status_code = 401
        mock_client_instance = mock_client.return_value.__enter__.return_value
        mock_client_instance.post.return_value = mock_response

        result = obj.login(mock_client_instance)
        assert result is False

    def test_validate_get_success(self):
        """Test successful GET validation"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            field1: str = "test"
            status: TOOStatus = TOOStatus()
            _get_schema: type = MockSchema
            _schema = MockSchema

        obj = TestAPI(autosubmit=False)
        result = obj.validate_get()
        assert obj.status.errors == []
        assert result is True

    def test_validate_get_failure(self):
        """Test failed GET validation"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            field1: str = "test"
            status: TOOStatus = TOOStatus()
            _get_schema: type = MockSchema

        obj = TestAPI(autosubmit=False)
        with patch.object(MockSchema, "model_validate", side_effect=ValidationError.from_exception_data("test", [])):
            result = obj.validate_get()
            assert result is False

    def test_validate_post_success(self):
        """Test successful POST validation"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            field1: str = "test"
            status: TOOStatus = TOOStatus()
            _post_schema: type = MockSchema

        obj = TestAPI(autosubmit=False)
        result = obj.validate_post()
        assert result is True

    def test_validate_post_failure(self):
        """Test failed POST validation"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            field1: str = "test"
            status: TOOStatus = TOOStatus()
            _post_schema: type = MockSchema

        obj = TestAPI(autosubmit=False)
        with patch.object(MockSchema, "model_validate", side_effect=ValidationError.from_exception_data("test", [])):
            result = obj.validate_post()
            assert result is False

    def test_submit_calls_submit_get_when_get_schema_exists(self):
        """Test submit calls submit_get when _get_schema exists"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            status: TOOStatus = TOOStatus()
            _get_schema: type = MockSchema

        obj = TestAPI(autosubmit=False)
        with (
            patch.object(TestAPI, "validate_get", return_value=True),
            patch.object(TestAPI, "submit_get", return_value=True) as mock_submit,
        ):
            result = obj.submit()
            mock_submit.assert_called_once()
            assert result is True

    def test_submit_calls_submit_post_when_post_schema_exists(self):
        """Test submit calls submit_post when _post_schema exists"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            status: TOOStatus = TOOStatus()
            _post_schema: type = MockSchema

        obj = TestAPI(autosubmit=False)
        with (
            patch.object(TestAPI, "validate_post", return_value=True),
            patch.object(TestAPI, "submit_post", return_value=True) as mock_submit,
        ):
            result = obj.submit()
            mock_submit.assert_called_once()
            assert result is True

    def test_submit_returns_false_when_status_not_pending(self):
        """Test submit returns False when status is not Pending"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            status: TOOStatus = TOOStatus(status="Accepted")

        obj = TestAPI(autosubmit=False)
        result = obj.submit()
        assert result is False

    def test_post_process_placeholder(self):
        """Test _post_process is a placeholder method"""

        class TestAPI(TOOAPIBaseclass, BaseModel):
            status: TOOStatus = TOOStatus()

        obj = TestAPI(autosubmit=False)
        # Should not raise any exceptions
        obj._post_process()

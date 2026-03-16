from typing import ClassVar, Optional
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel, ValidationError

from swifttools.swift_too.base.back_compat import TOOAPIBackCompat
from swifttools.swift_too.base.common import API_URL, TOOAPIBaseclass
from swifttools.swift_too.base.status import TOOStatus


class MockSchema(BaseModel):
    obs_id: Optional[int] = None
    username: str = "anonymous"


class MockTOOAPIBaseclass(BaseModel, TOOAPIBaseclass):
    """Mock class for testing TOOAPIBaseclass"""

    _endpoint: ClassVar[str] = "/test"
    _api_base: str = API_URL
    _schema: ClassVar[Mock] = Mock()
    _get_schema: ClassVar[MockSchema] = MockSchema
    _post_schema: ClassVar[Mock] = Mock()
    status: TOOStatus = TOOStatus()
    obs_id: Optional[int] = None
    # username, shared_secret, autosubmit inherited from TOOAPIBaseclass

    def __init__(self, **kwargs):
        # Back compat
        for key, values in self._back_compat_args.items():
            for value in values:
                if value in kwargs:
                    if key not in kwargs:
                        kwargs[key] = kwargs[value]
                    del kwargs[value]
        super().__init__(**kwargs)


@pytest.fixture
def mock_base_class():
    return MockTOOAPIBaseclass(username="testuser", shared_secret="testsecret")


@pytest.fixture
def mock_client():
    with patch("httpx.Client") as mock:
        yield mock


@pytest.fixture
def mock_cookie_jar():
    with patch("swifttools.swift_too.base.common.cookie_jar") as mock:
        yield mock


class TestMockTOOAPIBaseclass:
    def test_init_with_back_compat_args_obs_id(self, mock_base_class):
        obj = MockTOOAPIBaseclass(obsnum=123)
        assert obj.obs_id == 123

    def test_submit_url_property(self, mock_base_class):
        expected_url = f"{API_URL}/test"
        assert mock_base_class.submit_url == expected_url

    # Note: login method was refactored into _ensure_authenticated
    # and is tested indirectly through submit_get/submit_post tests

    def test_submit_get_success(self, mock_cookie_jar, mock_client, mock_base_class):
        # Mock the schema validation
        mock_validated = Mock()
        mock_validated.model_dump.return_value = {"param": "value"}
        with patch.object(MockSchema, "model_validate", return_value=mock_validated):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}

            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value.post.return_value = Mock(status_code=200)

            # Mock model_validate
            def mock_model_validate(data):
                mock_base_class.status.status = "success"
                return mock_base_class

            with patch.object(MockTOOAPIBaseclass, "model_validate", side_effect=mock_model_validate):
                result = mock_base_class.submit_get()
                assert result is True

    def test_submit_get_400_error(self, mock_cookie_jar, mock_client, mock_base_class):
        # Mock the schema validation
        mock_validated = Mock()
        mock_validated.model_dump.return_value = {"param": "value"}
        with patch.object(MockSchema, "model_validate", return_value=mock_validated):
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value.post.return_value = Mock(status_code=200)

            result = mock_base_class.submit_get()
            assert result is False

    def test_submit_get_other_error(self, mock_cookie_jar, mock_client, mock_base_class):
        # Mock the schema validation
        mock_validated = Mock()
        mock_validated.model_dump.return_value = {"param": "value"}
        with patch.object(MockSchema, "model_validate", return_value=mock_validated):
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value.post.return_value = Mock(status_code=200)

            result = mock_base_class.submit_get()
            assert result is False

    def test_handle_response_normalizes_string_status(self, mock_base_class):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "Validated"}

        captured = {}

        def mock_model_validate(data):
            captured["payload"] = data
            return mock_base_class

        with patch.object(MockTOOAPIBaseclass, "model_validate", side_effect=mock_model_validate):
            result = mock_base_class._handle_response(mock_response)

        assert result is True
        assert captured["payload"]["status"] == {"status": "Validated"}

    def test_handle_response_201_created_is_success(self, mock_base_class):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "status": "Accepted",
            "too_id": 22682,
            "jobnumber": 23472401,
            "errors": [],
            "warnings": [],
        }

        result = mock_base_class._handle_response(mock_response)

        assert result is True
        assert mock_base_class.status.status == "Accepted"
        assert mock_base_class.status.too_id == 22682
        assert mock_base_class.status.jobnumber == 23472401

    def test_handle_response_partial_payload_preserves_existing_fields(self, mock_base_class):
        mock_base_class.obs_id = 424242
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "Validated"}

        result = mock_base_class._handle_response(mock_response)

        assert result is True
        assert mock_base_class.obs_id == 424242
        assert mock_base_class.status.status == "Validated"

    def test_submit_post_400_error(self, mock_cookie_jar, mock_client, mock_base_class):
        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value.model_dump.return_value = {"param": "value"}

            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"

            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            result = mock_base_class.submit_post()
            assert result is False

    def test_submit_post_other_error(self, mock_cookie_jar, mock_client, mock_base_class):
        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_validated = Mock()
            mock_validated.model_dump.return_value = {"param": "value"}
            mock_schema.model_validate.return_value = mock_validated

            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            result = mock_base_class.submit_post()
            assert result is False

    def test_validate_get_success(self, mock_base_class):
        with patch.object(MockSchema, "model_validate", return_value=Mock()):
            result = mock_base_class.validate_get()
            assert result is True

    def test_validate_get_failure(self, mock_base_class):
        with patch.object(MockSchema, "model_validate", side_effect=ValidationError.from_exception_data("test", [])):
            result = mock_base_class.validate_get()
            assert result is False

    def test_validate_post_success(self, mock_base_class):
        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value = Mock()
            result = mock_base_class.validate_post()
            assert result is True

    def test_submit_not_pending(self, mock_base_class):
        mock_base_class.status.status = "Completed"
        result = mock_base_class.submit()
        assert result is False

    def test_set_error_with_status_string_calls_error_method(self, mock_base_class):
        # Use a subclass that defines an 'error' method to avoid pydantic extra-field restrictions
        called = []

        class ErrorClass(MockTOOAPIBaseclass):
            def error(self, msg):
                called.append(msg)

        obj = ErrorClass(username="testuser", shared_secret="testsecret")
        obj.status = "string_state"
        obj._TOOAPIBaseclass__set_error("Test error")
        assert called == ["Test error"]

    def test_set_error_with_status_object_calls_status_error(self, mock_base_class):
        # Replace status with an object that has an error method
        mock_base_class.status = TOOStatus()
        mock_base_class._TOOAPIBaseclass__set_error("New error")
        # Check that the error was added to the errors list
        assert "New error" in mock_base_class.status.errors

    def test_set_error_with_no_status_prints(self, capsys):
        # Define a minimal class without status to ensure print fallback is used
        class NoStatusModel(BaseModel, TOOAPIBaseclass):
            _endpoint: ClassVar[str] = "/test"

        obj = NoStatusModel()
        # Call private method
        obj._TOOAPIBaseclass__set_error("No status error")
        captured = capsys.readouterr()
        assert "ERROR: No status error" in captured.out

    def test_model_post_init_calls_submit_get_when_pending(self, mock_base_class):
        # Ensure model_post_init calls submit_get when pending and autosubmit=True
        class TestModel(TOOAPIBaseclass, BaseModel):
            _get_schema = MockSchema
            status: TOOStatus = TOOStatus()

        m = TestModel(username="testuser", shared_secret="testsecret", autosubmit=False)
        m.status = TOOStatus()
        m.status.status = "Pending"
        m.autosubmit = True
        with patch.object(TestModel, "validate_get", return_value=True):
            with patch.object(TestModel, "submit_get") as mock_submit:
                m.model_post_init({})
                mock_submit.assert_called_once()

    def test_model_post_init_not_calling_when_validate_fails(self, mock_base_class):
        class TestModel(TOOAPIBaseclass, BaseModel):
            _get_schema = MockSchema
            status: TOOStatus = TOOStatus()

        m = TestModel(username="testuser", shared_secret="testsecret", autosubmit=False)
        m.status = TOOStatus()
        m.status.status = "Pending"
        m.autosubmit = True
        with patch.object(TestModel, "validate_get", return_value=False):
            with patch.object(TestModel, "submit_get") as mock_submit:
                m.model_post_init({})
                mock_submit.assert_not_called()

    def test_submit_get_saves_cookie_on_login(self, mock_cookie_jar, mock_client):
        # Ensure cookie_jar.save is called when login is successful and no session cookie exists
        m = MockTOOAPIBaseclass(username="testuser", shared_secret="testsecret")
        m.status.status = "Pending"
        # Ensure cookie jar iterates empty -> no session cookie present
        mock_cookie_jar.__iter__.return_value = []
        # Mock schema validation and model validate to avoid side effects
        mock_validated = Mock()
        mock_validated.model_dump.return_value = {"param": "value"}
        with patch.object(MockSchema, "model_validate", return_value=mock_validated):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            # Mock both GET and POST responses (POST is for login)
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            login_response = Mock(status_code=200)
            mock_client.return_value.__enter__.return_value.post.return_value = login_response
            # Don't patch _ensure_authenticated - let it run and call save
            m.submit_get()
            mock_cookie_jar.save.assert_called_with(ignore_discard=True)

    # The positional-argument-to-keyword mapping is exercised indirectly by
    # other tests and classes; explicit positional-arg conversion tests are
    # difficult to construct with pydantic BaseModel subclasses.

    def test_submit_get_login_failure_returns_false(self, mock_cookie_jar, mock_client):
        m = MockTOOAPIBaseclass(username="testuser", shared_secret="testsecret")
        m.status.status = "Pending"
        # ensure no session cookie
        mock_cookie_jar.__iter__.return_value = []
        # Patch _ensure_authenticated to return False
        with patch.object(MockTOOAPIBaseclass, "_ensure_authenticated", return_value=False):
            # prepare schema validation to pass so logic proceeds to authentication
            mock_validated = Mock()
            mock_validated.model_dump.return_value = {"param": "value"}
            with patch.object(MockSchema, "model_validate", return_value=mock_validated):
                result = m.submit_get()
                assert result is False

    def test_submit_get_validation_failure(self, mock_base_class):
        mock_base_class.status.status = "Pending"
        with (
            patch.object(MockSchema, "model_validate", side_effect=ValidationError.from_exception_data("test", [])),
            patch.object(MockTOOAPIBaseclass, "validate_post", return_value=False),
        ):
            result = mock_base_class.submit()
            assert result is False

    def test_submit_post_validation_failure(self, mock_base_class):
        mock_base_class.status.status = "Pending"
        with (
            patch.object(MockTOOAPIBaseclass, "validate_get", return_value=False),
            patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema,
        ):
            mock_schema.model_validate.side_effect = ValidationError.from_exception_data("test", [])
            result = mock_base_class.submit()
            assert result is False

    def test_queue_get_success(self, mock_cookie_jar, mock_client, mock_base_class):
        import time
        from unittest.mock import patch

        mock_base_class.status.status = "Pending"
        object.__setattr__(mock_base_class, "complete", False)
        assert mock_base_class.complete is False

        # Mock the schema validation
        mock_validated = Mock()
        mock_validated.model_dump.return_value = {"param": "value"}
        with patch.object(MockSchema, "model_validate", return_value=mock_validated):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}

            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value.post.return_value = Mock(status_code=200)

            # Mock model_validate
            def mock_model_validate(data):
                mock_base_class.status.status = "success"
                return mock_base_class

            with patch.object(MockTOOAPIBaseclass, "model_validate", side_effect=mock_model_validate):
                result = mock_base_class.queue()
                assert result is True
                # Wait a bit for the thread to complete
                time.sleep(0.1)
                assert mock_base_class.complete is True


class MockBackCompat(TOOAPIBackCompat):
    def __init__(self):
        self.target_name = "Test Target"
        self.obs_id = 123
        self.uvot_mode = "test_uvot"
        self.xrt_mode = "test_xrt"
        self.bat_mode = "test_bat"
        self.segment = "test_seg"
        self.ra_object = 10.0
        self.dec_object = 20.0


class TestMockBackCompat:
    def test_back_compat_properties_targname(self):
        obj = MockBackCompat()
        assert obj.targname == "Test Target"

    def test_back_compat_properties_obsid(self):
        obj = MockBackCompat()
        assert obj.obsid == 123

    def test_back_compat_properties_obsnum(self):
        obj = MockBackCompat()
        assert obj.obsnum == 123

    def test_back_compat_properties_source_name(self):
        obj = MockBackCompat()
        assert obj.source_name == "Test Target"

    def test_back_compat_properties_uvotmode(self):
        obj = MockBackCompat()
        assert obj.uvotmode == "test_uvot"

    def test_back_compat_properties_xrtmode(self):
        obj = MockBackCompat()
        assert obj.xrtmode == "test_xrt"

    def test_back_compat_properties_batmode(self):
        obj = MockBackCompat()
        assert obj.batmode == "test_bat"

    def test_back_compat_properties_xrt(self):
        obj = MockBackCompat()
        assert obj.xrt == "test_xrt"

    def test_back_compat_properties_uvot(self):
        obj = MockBackCompat()
        assert obj.uvot == "test_uvot"

    def test_back_compat_properties_bat(self):
        obj = MockBackCompat()
        assert obj.bat == "test_bat"

    def test_back_compat_properties_seg(self):
        obj = MockBackCompat()
        assert obj.seg == "test_seg"

    def test_back_compat_properties_ra_point(self):
        obj = MockBackCompat()
        assert obj.ra_point == 10.0

    def test_back_compat_properties_dec_point(self):
        obj = MockBackCompat()
        assert obj.dec_point == 20.0

import importlib
from typing import ClassVar, Optional
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel, ValidationError

import swifttools.swift_too.base.common as common_module
from swifttools.swift_too.base.back_compat import TOOAPIBackCompat
from swifttools.swift_too.base.common import (
    API_URL,
    TOOAPIBaseclass,
    _format_422_errors,
    _parse_422_error,
)
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


class TestMockTOOAPIBaseclass:
    def test_parse_422_error_variants(self):
        assert _parse_422_error('{"detail":"simple"}') == ["simple"]
        assert _parse_422_error('{"detail":[{"loc":["body","field"],"msg":"bad"},"other"]}') == [
            "field: bad",
            "other",
        ]
        assert _parse_422_error('{"other":"value"}') == ['{"other":"value"}']
        assert _parse_422_error("not-json") == ["not-json"]

    def test_format_422_errors_variants(self):
        assert _format_422_errors([]) == "Validation error"
        assert _format_422_errors(["one"]) == "one"
        assert _format_422_errors(["one", "two"]).startswith("Validation errors:\n")

    def test_reload_module_handles_missing_cookie_jar_file(self, monkeypatch):
        original = common_module.http.cookiejar.LWPCookieJar

        class FakeJar:
            def __init__(self, *args, **kwargs):
                pass

            def load(self, ignore_discard=True):
                raise FileNotFoundError

        monkeypatch.setattr(common_module.http.cookiejar, "LWPCookieJar", FakeJar)
        importlib.reload(common_module)
        # Restore by reloading with real jar implementation.
        monkeypatch.setattr(common_module.http.cookiejar, "LWPCookieJar", original)
        importlib.reload(common_module)

    def test_init_with_back_compat_args_obs_id(self, mock_base_class):
        obj = MockTOOAPIBaseclass(obsnum=123)
        assert obj.obs_id == 123

    def test_handle_back_compat_args_drops_duplicate_deprecated_key(self, mock_base_class):
        kwargs = {"obs_id": 1, "obsnum": 2}
        out = mock_base_class._handle_back_compat_args(kwargs)
        assert out["obs_id"] == 1
        assert "obsnum" not in out

    def test_handle_back_compat_args_maps_deprecated_when_primary_missing(self, mock_base_class):
        kwargs = {"obsnum": 2}
        out = mock_base_class._handle_back_compat_args(kwargs)
        assert out["obs_id"] == 2

    def test_convert_positional_args_assigns_schema_fields(self, mock_base_class):
        out = mock_base_class._convert_positional_args((123,), {})
        assert out["obs_id"] == 123

    def test_get_schema_for_init_uses_default_attr(self, mock_base_class):
        class Wrapper:
            default = MockSchema

        original_get = getattr(MockTOOAPIBaseclass, "_get_schema", None)
        original_post = getattr(MockTOOAPIBaseclass, "_post_schema", None)
        MockTOOAPIBaseclass._get_schema = Wrapper
        MockTOOAPIBaseclass._post_schema = Mock()
        try:
            assert mock_base_class._get_schema_for_init() is MockSchema
        finally:
            MockTOOAPIBaseclass._get_schema = original_get
            MockTOOAPIBaseclass._post_schema = original_post

    def test_schema_payload_includes_attr_not_in_model_dump(self, mock_base_class):
        class SchemaExtra(BaseModel):
            obs_id: Optional[int] = None
            username: str = "anonymous"
            shared_secret: Optional[str] = None

        mock_base_class.shared_secret = "secret"
        payload = mock_base_class._schema_payload(SchemaExtra)
        assert payload["shared_secret"] == "secret"

    def test_schema_payload_inserts_non_model_attribute_field(self, mock_base_class):
        class SchemaExtra(BaseModel):
            token: Optional[str] = None

        object.__setattr__(mock_base_class, "token", "abc")
        payload = mock_base_class._schema_payload(SchemaExtra)
        assert payload["token"] == "abc"

    def test_submit_url_property(self, mock_base_class):
        expected_url = f"{API_URL}/test"
        assert mock_base_class.submit_url == expected_url

    # Note: login method was refactored into _ensure_authenticated
    # and is tested indirectly through submit_get/submit_post tests

    def test_submit_get_success(self, mock_cookie_jar, mock_client, mock_base_class, mock_validated_payload):
        with patch.object(MockSchema, "model_validate", return_value=mock_validated_payload):
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

    def test_submit_get_400_error(self, mock_cookie_jar, mock_client, mock_base_class, mock_validated_payload):
        with patch.object(MockSchema, "model_validate", return_value=mock_validated_payload):
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value.post.return_value = Mock(status_code=200)

            result = mock_base_class.submit_get()
            assert result is False

    def test_submit_get_other_error(self, mock_cookie_jar, mock_client, mock_base_class, mock_validated_payload):
        with patch.object(MockSchema, "model_validate", return_value=mock_validated_payload):
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

    def test_handle_response_400_applies_structured_status_errors(self, mock_base_class):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = (
            '{"status":{"username":"anonymous","status":"Rejected","errors":'
            '["The following UVOT filters are not allowed due to a bright star: u, b, v, uvw1, uvw2, uvm2."],'
            '"warnings":[]}}'
        )
        mock_response.json.return_value = {
            "status": {
                "username": "anonymous",
                "status": "Rejected",
                "errors": [
                    "The following UVOT filters are not allowed due to a bright star: u, b, v, uvw1, uvw2, uvm2."
                ],
                "warnings": [],
            }
        }

        result = mock_base_class._handle_response(mock_response)

        assert result is False
        assert mock_base_class.status.status == "Rejected"
        assert mock_base_class.status.errors == [
            "The following UVOT filters are not allowed due to a bright star: u, b, v, uvw1, uvw2, uvm2."
        ]
        assert mock_base_class.status.warnings == []

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

    def test_submit_post_other_error(self, mock_cookie_jar, mock_client, mock_base_class, mock_validated_payload):
        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value = mock_validated_payload

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

    def test_format_validation_error_multiple(self):
        class Req(BaseModel):
            a: int
            b: int

        with pytest.raises(ValidationError) as exc:
            Req.model_validate({})
        msg = TOOAPIBaseclass._format_validation_error(exc.value)
        assert "a:" in msg and "b:" in msg

    def test_format_validation_error_single_and_many(self):
        class SingleReq(BaseModel):
            a: int

        with pytest.raises(ValidationError) as exc_single:
            SingleReq.model_validate({})
        one = TOOAPIBaseclass._format_validation_error(exc_single.value)
        assert one.startswith("a:")

        class ManyReq(BaseModel):
            a: int
            b: int
            c: int
            d: int
            e: int
            f: int

        with pytest.raises(ValidationError) as exc_many:
            ManyReq.model_validate({})
        many = TOOAPIBaseclass._format_validation_error(exc_many.value)
        assert "(and 1 more)" in many

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

    def test_submit_routes_get_and_post(self, mock_base_class, post_only_model_cls):
        mock_base_class.status.status = "Pending"
        with patch.object(MockTOOAPIBaseclass, "validate_get", return_value=True):
            with patch.object(MockTOOAPIBaseclass, "submit_get", return_value=True) as mget:
                assert mock_base_class.submit() is True
                mget.assert_called_once()

        obj = post_only_model_cls(username="u", shared_secret="s", autosubmit=False)
        obj.status.status = "Pending"
        with patch.object(post_only_model_cls, "validate_post", return_value=True):
            with patch.object(post_only_model_cls, "submit_post", return_value=True) as mpost:
                assert obj.submit() is True
                mpost.assert_called_once()

        obj.status.status = "Pending"
        with patch.object(post_only_model_cls, "validate_post", return_value=False):
            assert obj.submit() is False

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

    def test_submit_get_saves_cookie_on_login(self, mock_cookie_jar, mock_client, mock_validated_payload):
        # Ensure cookie_jar.save is called when login is successful and no session cookie exists
        m = MockTOOAPIBaseclass(username="testuser", shared_secret="testsecret")
        m.status.status = "Pending"
        # Ensure cookie jar iterates empty -> no session cookie present
        mock_cookie_jar.__iter__.return_value = []
        with patch.object(MockSchema, "model_validate", return_value=mock_validated_payload):
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

    def test_submit_get_login_failure_returns_false(self, mock_cookie_jar, mock_client, mock_validated_payload):
        m = MockTOOAPIBaseclass(username="testuser", shared_secret="testsecret")
        m.status.status = "Pending"
        # ensure no session cookie
        mock_cookie_jar.__iter__.return_value = []
        # Patch _ensure_authenticated to return False
        with patch.object(MockTOOAPIBaseclass, "_ensure_authenticated", return_value=False):
            with patch.object(MockSchema, "model_validate", return_value=mock_validated_payload):
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

    def test_queue_get_success(self, mock_cookie_jar, mock_client, mock_base_class, mock_validated_payload):
        import time
        from unittest.mock import patch

        mock_base_class.status.status = "Pending"
        object.__setattr__(mock_base_class, "complete", False)
        assert mock_base_class.complete is False

        with patch.object(MockSchema, "model_validate", return_value=mock_validated_payload):
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

    def test_queue_validation_failures(self, mock_base_class, post_only_model_cls):
        mock_base_class.status.status = "Pending"
        with patch.object(MockTOOAPIBaseclass, "validate_get", return_value=False):
            assert mock_base_class.queue() is False

        obj = post_only_model_cls(username="u", shared_secret="s", autosubmit=False)
        obj.status.status = "Pending"
        with patch.object(post_only_model_cls, "validate_post", return_value=False):
            assert obj.queue() is False

    def test_queue_post_success_and_not_pending(self, post_only_model_cls):
        obj = post_only_model_cls(username="u", shared_secret="s", autosubmit=False)
        obj.status.status = "Pending"
        thread_mock = Mock()
        thread_mock.start.return_value = None
        with patch("swifttools.swift_too.base.common.threading.Thread", return_value=thread_mock):
            with patch.object(post_only_model_cls, "validate_post", return_value=True):
                assert obj.queue() is True
                assert thread_mock.start.call_count == 2

        obj.status.status = "Complete"
        assert obj.queue() is False

    def test_queue_watchdog_timeout_sets_error_and_complete(self, mock_base_class):
        mock_base_class._timeout = 0
        object.__setattr__(mock_base_class, "complete", False)
        with patch("swifttools.swift_too.base.common.time.sleep", return_value=None):
            mock_base_class._queue_watchdog()
        assert mock_base_class.complete is True
        assert any("Asynchronous request timed out" in e for e in mock_base_class.status.errors)

    def test_ensure_authenticated_branches(self, mock_base_class, mock_cookie_jar):
        client = Mock()

        mock_base_class.username = "anonymous"
        assert mock_base_class._ensure_authenticated(client) is True

        mock_base_class.username = "user"
        cookie = Mock()
        cookie.name = "session"
        cookie.is_expired.return_value = False
        mock_cookie_jar.__iter__.return_value = [cookie]
        assert mock_base_class._ensure_authenticated(client) is True

        mock_cookie_jar.__iter__.return_value = []
        client.post.side_effect = Exception("boom")
        assert mock_base_class._ensure_authenticated(client) is False
        client.post.side_effect = None
        client.post.return_value.status_code = 403
        assert mock_base_class._ensure_authenticated(client) is False

    def test_should_autosubmit_status_string_and_validation_failure(self, mock_base_class):
        mock_base_class.autosubmit = True
        mock_base_class.status = "not-status-obj"
        assert mock_base_class._should_autosubmit() is False

        mock_base_class.status = TOOStatus()
        mock_base_class.status.status = "Pending"
        with patch.object(MockSchema, "model_validate", side_effect=TypeError("bad")):
            assert mock_base_class._should_autosubmit() is False

    def test_submit_get_exception_and_submit_post_paths(
        self, mock_cookie_jar, mock_client, mock_base_class, mock_validated_payload
    ):
        with patch.object(MockSchema, "model_validate", return_value=mock_validated_payload):
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception("x")
            mock_client.return_value.__enter__.return_value.post.return_value = Mock(status_code=200)
            assert mock_base_class.submit_get() is False

        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value.model_dump.return_value = {}
            assert mock_base_class.submit_post() is False

        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value.model_dump.return_value = {"p": 1}
            mock_client.return_value.__enter__.return_value.post.side_effect = Exception("x")
            assert mock_base_class.submit_post() is False

        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value.model_dump.return_value = {"p": 1}
            with patch.object(MockTOOAPIBaseclass, "_ensure_authenticated", return_value=True):
                mock_client.return_value.__enter__.return_value.post.side_effect = Exception("boom")
                assert mock_base_class.submit_post() is False

        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value.model_dump.return_value = {"p": 1}
            mock_client.return_value.__enter__.return_value.post.side_effect = None
            mock_client.return_value.__enter__.return_value.post.return_value = Mock(status_code=200)
            with patch.object(MockTOOAPIBaseclass, "_ensure_authenticated", return_value=True):
                with patch.object(MockTOOAPIBaseclass, "_handle_response", return_value=True):
                    assert mock_base_class.submit_post() is True

    def test_async_submit_branches(self, mock_cookie_jar, mock_client, mock_base_class, mock_validated_payload):
        with patch.object(MockTOOAPIBaseclass, "_ensure_authenticated", return_value=False):
            with patch.object(MockSchema, "model_validate", return_value=mock_validated_payload):
                object.__setattr__(mock_base_class, "complete", False)
                mock_base_class._submit_get_async()
                assert mock_base_class.complete is True

        with patch.object(MockTOOAPIBaseclass, "_ensure_authenticated", return_value=True):
            with patch.object(MockSchema, "model_validate", return_value=mock_validated_payload):
                mock_client.return_value.__enter__.return_value.get.side_effect = Exception("x")
                object.__setattr__(mock_base_class, "complete", False)
                mock_base_class._submit_get_async()
                assert mock_base_class.complete is True

        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value.model_dump.return_value = {}
            object.__setattr__(mock_base_class, "complete", False)
            mock_base_class._submit_post_async()
            assert mock_base_class.complete is True

        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value.model_dump.return_value = {"p": 1}
            with patch.object(MockTOOAPIBaseclass, "_ensure_authenticated", return_value=False):
                object.__setattr__(mock_base_class, "complete", False)
                mock_base_class._submit_post_async()
                assert mock_base_class.complete is True

        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value.model_dump.return_value = {"p": 1}
            with patch.object(MockTOOAPIBaseclass, "_ensure_authenticated", return_value=True):
                mock_client.return_value.__enter__.return_value.post.side_effect = Exception("x")
                object.__setattr__(mock_base_class, "complete", False)
                mock_base_class._submit_post_async()
                assert mock_base_class.complete is True

        with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
            mock_schema.model_fields = {}
            mock_schema.model_validate.return_value.model_dump.return_value = {"p": 1}
            with patch.object(MockTOOAPIBaseclass, "_ensure_authenticated", return_value=True):
                mock_client.return_value.__enter__.return_value.post.side_effect = None
                mock_client.return_value.__enter__.return_value.post.return_value = Mock(status_code=200)
                with patch.object(MockTOOAPIBaseclass, "_handle_response_async") as m_async:
                    mock_base_class._submit_post_async()
                    m_async.assert_called_once()

    def test_handle_response_remaining_branches(self, mock_base_class):
        # success payload that is not dict -> model_fields_set merge path
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["x"]

        class DataObj:
            model_fields_set = {"status"}
            status = TOOStatus(status="Accepted")

        with patch.object(MockTOOAPIBaseclass, "model_validate", return_value=DataObj()):
            assert mock_base_class._handle_response(mock_response) is True

        # validation exception
        with patch.object(MockTOOAPIBaseclass, "model_validate", side_effect=ValueError("bad")):
            assert mock_base_class._handle_response(mock_response) is False

        # 422 / unauthorized / non-int status
        r422 = Mock(status_code=422, text='{"detail":"x"}')
        assert mock_base_class._handle_response(r422) is False
        runa = Mock(status_code=401, text="unauth")
        assert mock_base_class._handle_response(runa) is False
        rweird = Mock(status_code="oops", text="odd")
        assert mock_base_class._handle_response(rweird) is False

        # 4xx with json parsing failure path
        r400 = Mock(status_code=400, text="bad")
        r400.json.side_effect = ValueError("bad-json")
        assert mock_base_class._handle_response(r400) is False

    def test_apply_status_from_payload_edge_cases(self, mock_base_class):
        assert mock_base_class._apply_status_from_payload("not-dict") is False
        assert mock_base_class._apply_status_from_payload({"status": 1}) is False

        mock_base_class.status = "string-status"
        assert mock_base_class._apply_status_from_payload({"status": "Rejected"}) is False

        mock_base_class.status = TOOStatus()
        payload = {
            "status": {
                "status": "Rejected",
                "errors": ["e1"],
                "warnings": ["w1"],
                "too_id": 12,
                "jobnumber": 34,
            }
        }
        assert mock_base_class._apply_status_from_payload(payload) is True
        assert mock_base_class.status.too_id == 12
        assert mock_base_class.status.jobnumber == 34


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

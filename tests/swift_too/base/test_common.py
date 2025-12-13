from typing import ClassVar, Optional
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel, ValidationError

from swifttools.swift_too.base.common import API_URL, TOOAPIBackCompat, TOOAPIBaseclass
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
    username: str = "anonymous"
    shared_secret: str = "anonymous"
    autosubmit: bool = False

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


def test_init_with_back_compat_args(mock_base_class):
    # Test backward compatibility arguments
    obj = MockTOOAPIBaseclass(obsnum=123)
    assert obj.obs_id == 123


def test_submit_url_property(mock_base_class):
    expected_url = f"{API_URL}/test"
    assert mock_base_class.submit_url == expected_url


@patch("httpx.Client")
def test_login_success(mock_client, mock_base_class):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.return_value.__enter__.return_value.post.return_value = mock_response

    result = mock_base_class.login(mock_client.return_value.__enter__.return_value)
    assert result is True


@patch("httpx.Client")
def test_login_failure(mock_client, mock_base_class):
    mock_response = Mock()
    mock_response.status_code = 401
    mock_client.return_value.__enter__.return_value.post.return_value = mock_response

    result = mock_base_class.login(mock_client.return_value.__enter__.return_value)
    assert result is False


@patch("httpx.Client")
@patch("swifttools.swift_too.base.common.cookie_jar")
def test_submit_get_success(mock_cookie_jar, mock_client, mock_base_class):
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


@patch("httpx.Client")
@patch("swifttools.swift_too.base.common.cookie_jar")
def test_submit_get_400_error(mock_cookie_jar, mock_client, mock_base_class):
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


@patch("httpx.Client")
@patch("swifttools.swift_too.base.common.cookie_jar")
def test_submit_get_other_error(mock_cookie_jar, mock_client, mock_base_class):
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


@patch("httpx.Client")
@patch("swifttools.swift_too.base.common.cookie_jar")
def test_submit_post_400_error(mock_cookie_jar, mock_client, mock_base_class):
    with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
        mock_schema.model_validate.return_value.model_dump.return_value = {"param": "value"}

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        result = mock_base_class.submit_post()
        assert result is False


@patch("httpx.Client")
@patch("swifttools.swift_too.base.common.cookie_jar")
def test_submit_post_other_error(mock_cookie_jar, mock_client, mock_base_class):
    with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
        mock_validated = Mock()
        mock_validated.model_dump.return_value = {"param": "value"}
        mock_schema.model_validate.return_value = mock_validated

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        result = mock_base_class.submit_post()
        assert result is False


def test_validate_get_success(mock_base_class):
    with patch.object(MockSchema, "model_validate", return_value=Mock()):
        result = mock_base_class.validate_get()
        assert result is True


def test_validate_get_failure(mock_base_class):
    with patch.object(MockSchema, "model_validate", side_effect=ValidationError.from_exception_data("test", [])):
        result = mock_base_class.validate_get()
        assert result is False


def test_validate_post_success(mock_base_class):
    with patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema:
        mock_schema.model_validate.return_value = Mock()
        result = mock_base_class.validate_post()
        assert result is True


def test_submit_not_pending(mock_base_class):
    mock_base_class.status.status = "Completed"
    result = mock_base_class.submit()
    assert result is False


def test_submit_get_validation_failure(mock_base_class):
    mock_base_class.status.status = "Pending"
    with (
        patch.object(MockSchema, "model_validate", side_effect=ValidationError.from_exception_data("test", [])),
        patch.object(MockTOOAPIBaseclass, "validate_post", return_value=False),
    ):
        result = mock_base_class.submit()
        assert result is False


def test_submit_post_validation_failure(mock_base_class):
    mock_base_class.status.status = "Pending"
    with (
        patch.object(MockTOOAPIBaseclass, "validate_get", return_value=False),
        patch.object(MockTOOAPIBaseclass, "_post_schema", Mock()) as mock_schema,
    ):
        mock_schema.model_validate.side_effect = ValidationError.from_exception_data("test", [])
        result = mock_base_class.submit()
        assert result is False


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


def test_back_compat_properties():
    obj = MockBackCompat()

    assert obj.targname == "Test Target"
    assert obj.obsid == 123
    assert obj.obsnum == 123
    assert obj.source_name == "Test Target"
    assert obj.uvotmode == "test_uvot"
    assert obj.xrtmode == "test_xrt"
    assert obj.batmode == "test_bat"
    assert obj.xrt == "test_xrt"
    assert obj.uvot == "test_uvot"
    assert obj.bat == "test_bat"
    assert obj.seg == "test_seg"
    assert obj.ra_point == 10.0
    assert obj.dec_point == 20.0

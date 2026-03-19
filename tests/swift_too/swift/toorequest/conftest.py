# Local fixtures for tests/swift_too/swift/toorequest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from swifttools.swift_too.base.common import API_URL
from swifttools.swift_too.swift.toorequest import SwiftTOOFormSchema, SwiftTOORequest


@pytest.fixture
def mock_resolve_default():
    """Pytest fixture to mock SwiftResolve with default values"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 0.0
        mock_resolve_instance.dec = 0.0
        yield mock_resolve_class


@pytest.fixture
def mock_resolve_test_target():
    """Pytest fixture to mock SwiftResolve with test target values"""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve") as mock_resolve_class:
        mock_resolve_instance = mock_resolve_class.return_value
        mock_resolve_instance.status.warnings = []
        mock_resolve_instance.status.errors = []
        mock_resolve_instance.ra = 123.456
        mock_resolve_instance.dec = -45.678
        yield mock_resolve_class


@pytest.fixture
def mock_resolve():
    mock = MagicMock()
    mock.ra = 10.0
    mock.dec = 20.0
    mock.status.warnings = []
    mock.status.errors = []
    return mock


@pytest.fixture
def too_request_base(mock_resolve):
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
        too = SwiftTOORequest(
            ra=10.0,
            dec=20.0,
            science_just="Test justification",
            num_of_visits=1,
            exp_time_per_visit=1000,
            exp_time_just="Test exposure justification",
            obs_type="Spectroscopy",
            instrument="XRT",
            target_name="Test Target",
            target_type="Normal",
            username="testuser",
            shared_secret="testsecret",
            autosubmit=False,
        )
        return too


@pytest.fixture
def too_request_with_decision(mock_resolve):
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
        too = SwiftTOORequest(
            ra=10.0,
            dec=20.0,
            science_just="Test justification",
            num_of_visits=1,
            exp_time_per_visit=1000,
            exp_time_just="Test exposure justification",
            obs_type="Spectroscopy",
            instrument="XRT",
            target_name="Test Target",
            target_type="Normal",
            username="testuser",
            shared_secret="testsecret",
            autosubmit=False,
            decision="Approved",
        )
        return too


@pytest.fixture
def basic_too_request():
    """Basic SwiftTOORequest instance for testing."""
    return SwiftTOORequest(autosubmit=False)


@pytest.fixture
def too_request_for_table(mock_resolve_test_target):
    """SwiftTOORequest instance configured for table property testing."""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve_test_target):
        request = SwiftTOORequest(autosubmit=False)
        request.decision = None
        request.too_id = 12345
        request.target_name = "Test Target"
        request.ra = 123.456
        request.dec = -45.678
        return request


@pytest.fixture
def too_request_with_decision_for_table(mock_resolve_default):
    """SwiftTOORequest instance with decision for table property testing."""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve_default):
        request = SwiftTOORequest(autosubmit=False)
        request.decision = "Approved"
        request.urgency = 2
        request.timestamp = datetime(2023, 1, 1, 12, 0, 0)
        return request


@pytest.fixture
def too_request_submit_success(too_request_base):
    """TOO request with submit dependencies patched to return Accepted + TOO ID."""
    too = too_request_base
    too._api_base = API_URL

    with (
        patch("swifttools.swift_too.base.common.cookie_jar"),
        patch("httpx.Client") as mock_client,
        patch.object(too, "validate_post", return_value=True),
        patch.object(type(too), "_post_schema") as mock_post_schema,
    ):
        mock_response = mock_client.return_value.__enter__.return_value.post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "Accepted", "too_id": 123}
        mock_post_schema.model_validate.return_value.model_dump.return_value = {"param": "value"}
        yield too


@pytest.fixture
def too_request_with_required_fields(too_request_base):
    """TOO request populated with required fields for server_validate tests."""
    too = too_request_base
    too._api_base = API_URL
    object.__setattr__(too, "target_name", "Test Target")
    object.__setattr__(too, "immediate_objective", "Test objective")
    object.__setattr__(too, "uvot_just", "Test UVOT justification")
    return too


@pytest.fixture
def status_validated_response():
    """Standard status-only API response mock."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"status": "Validated"}
    return response


@pytest.fixture
def form_schema_construct_kwargs():
    """Reusable kwargs for direct model_construct setup tests."""
    return {
        "target_name": "Test Target",
        "target_type": "Normal",
        "ra": 10.0,
        "dec": 20.0,
        "obs_type": "Spectroscopy",
        "science_just": "Test justification",
        "immediate_objective": "Test objective",
        "exposure": 1000,
        "exp_time_just": "Test exp justification",
        "xrt_countrate": "1.0",
        "instrument": "XRT",
        "exp_time_per_visit": 500,
        "num_of_visits": 1,
        "monitoring_freq": "1 day",
        "uvot_mode": "0x9999",
        "uvot_just": "",
    }


@pytest.fixture
def constructed_form_schema(form_schema_construct_kwargs):
    """SwiftTOOFormSchema built with model_construct for setup-only branch tests."""
    return SwiftTOOFormSchema.model_construct(**form_schema_construct_kwargs)

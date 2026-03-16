# Local fixtures for tests/swift_too/swift/toorequest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from swifttools.swift_too.swift.toorequest import SwiftTOORequest


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

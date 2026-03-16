# Local fixtures for tests/swift_too/swift/requests
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from swifttools.swift_too.swift.requests import SwiftTOORequests
from swifttools.swift_too.swift.toorequest import SwiftTOORequest


@pytest.fixture
def mock_resolve():
    """Mock SwiftResolve that returns a resolved target."""
    mock = MagicMock()
    mock.ra = 10.0
    mock.dec = 20.0
    mock.status = MagicMock(warnings=[], errors=[])
    return mock


@pytest.fixture
def swift_requests(mock_resolve):
    """SwiftTOORequests instance with mocked resolve."""
    with patch("swifttools.swift_too.swift.resolve.SwiftResolve", return_value=mock_resolve):
        return SwiftTOORequests(autosubmit=False)


@pytest.fixture
def sample_too_request():
    """Sample SwiftTOORequest entry for testing."""
    return SwiftTOORequest(
        too_id=123,
        target_name="Test Target",
        instrument="XRT",
        ra=10.0,
        dec=20.0,
        uvot_mode_approved=0x9999,
        xrt_mode_approved=7,
        timestamp=datetime(2023, 1, 1),
        l_name="Test L",
        urgency=2,  # HIGH
        date_begin=datetime(2023, 1, 1),
        date_end=datetime(2023, 1, 2),
        target_id=456,
        autosubmit=False,
    )

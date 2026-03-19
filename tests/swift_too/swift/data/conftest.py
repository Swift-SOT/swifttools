# Local fixtures for tests/swift_too/swift/data

from unittest.mock import MagicMock, patch

import pytest

from swifttools.swift_too.base.schemas import BaseSchema
from swifttools.swift_too.swift.data import SwiftData, SwiftDataFile, TOOAPIDownloadData


class MockDownloadData(BaseSchema, TOOAPIDownloadData):
    """Mock class to test TOOAPIDownloadData mixin"""

    obs_id: str = "00012345001"


@pytest.fixture
def mock_download_data():
    """Fixture for MockDownloadData instance."""
    return MockDownloadData()


@pytest.fixture
def swift_data_basic():
    """Basic SwiftData instance with autosubmit=False."""
    return SwiftData(obs_id="00012345001", autosubmit=False)


@pytest.fixture
def swift_data_file_basic():
    """Basic SwiftDataFile instance."""
    return SwiftDataFile(filename="test.fits", path="data", url="http://example.com/test.fits", type="BAT")


@pytest.fixture
def swift_data_file_heasarc():
    """SwiftDataFile instance with HEASARC URL."""
    return SwiftDataFile(
        filename="test.fits", path="data", url="https://heasarc.gsfc.nasa.gov/FTP/heasarc/path/test.fits", type="XRT"
    )


@pytest.fixture
def swift_data_with_entries(swift_data_basic, swift_data_file_basic):
    """SwiftData instance with test entries."""
    swift_data_basic.entries = [swift_data_file_basic]
    return swift_data_basic


@pytest.fixture
def swift_data_multiple_entries(swift_data_basic):
    """SwiftData instance with multiple test entries."""
    entries = [
        SwiftDataFile(filename="a.fits", path="p1", url="u1", type="t"),
        SwiftDataFile(filename="b.fits", path="p2", url="u2", type="t"),
        SwiftDataFile(filename="c.fits", path="p1", url="u3", type="t"),
    ]
    swift_data_basic.entries = entries
    return swift_data_basic


@pytest.fixture
def temp_file_with_content(tmp_path):
    """Create a temporary file with some content."""
    file_path = tmp_path / "test.fits"
    file_path.write_bytes(b"test data")
    return file_path


@pytest.fixture
def mock_boto3():
    """Mock boto3 clients."""
    with (
        patch("swifttools.swift_too.swift.data.boto3.client"),
        patch("swifttools.swift_too.swift.data.boto3.session.Session.client"),
    ):
        yield


@pytest.fixture
def mock_httpx_stream():
    """Mock httpx.stream for download tests."""
    mock_response = MagicMock()
    mock_response.headers.get.return_value = "100"
    mock_response.iter_bytes.return_value = [b"test"]
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_response.raise_for_status.return_value = None

    with patch("swifttools.swift_too.swift.data.httpx.stream") as mock_stream:
        mock_stream.return_value = mock_response
        yield mock_stream

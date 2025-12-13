import os
import tempfile
from unittest.mock import MagicMock, patch

from swifttools.swift_too.base.schemas import BaseSchema
from swifttools.swift_too.swift.data import SwiftData, SwiftDataFile, TOOAPIDownloadData


class MockDownloadData(BaseSchema, TOOAPIDownloadData):
    """Mock class to test TOOAPIDownloadData mixin"""

    obs_id: str = "00012345001"


def test_swift_data_init():
    """Test SwiftData initialization"""
    data = SwiftData(obs_id="00012345001", autosubmit=False)
    assert data.obs_id == "00012345001"


def test_swift_data_all_property():
    """Test the 'all' property"""
    data = SwiftData(autosubmit=False)
    assert data.all is False
    data.xrt = True
    data.uvot = True
    data.bat = True
    data.log = True
    data.auxil = True
    data.tdrss = True
    assert data.all is True


def test_swift_data_all_setter():
    """Test the 'all' property setter"""
    data = SwiftData(autosubmit=False)
    data.all = True
    assert data.xrt is True
    assert data.uvot is True
    assert data.bat is True
    assert data.log is True
    assert data.auxil is True
    assert data.tdrss is True


def test_swift_data_getitem():
    """Test indexing"""
    data = SwiftData(autosubmit=False)
    data.entries = ["file1", "file2"]
    assert data[0] == "file1"
    assert data[1] == "file2"


def test_swift_data_table_property():
    """Test _table property"""
    data = SwiftData(autosubmit=False)
    data.entries = []
    header, table = data._table
    assert header == ["Path", "Filename", "Description"]
    assert table == []


def test_swift_data_file_size():
    """Test SwiftDataFile size property"""
    file_obj = SwiftDataFile(filename="test.fits", path="data", url="http://example.com/test.fits", type="BAT")
    assert file_obj.size is None

    # Mock localpath
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp.flush()  # Ensure data is written
        file_obj.localpath = tmp.name
        assert file_obj.size == len(b"test data")
        os.unlink(tmp.name)


@patch("swifttools.swift_too.swift.data.boto3.client")
@patch("swifttools.swift_too.swift.data.boto3.session.Session.client")
def test_swift_data_post_process_aws(mock_session_client, mock_client):
    """Test _post_process with AWS setup"""
    data = SwiftData(obs_id="00012345001", uksdc=False, itsdc=False, aws=True, autosubmit=False)
    data._post_process()
    # Should have set up S3 client
    assert data._s3 is not None


@patch("swifttools.swift_too.swift.data.os.path.exists")
@patch("swifttools.swift_too.swift.data.os.makedirs")
def test_swift_data_download_file(mock_makedirs, mock_exists):
    """Test SwiftDataFile download method"""
    mock_exists.return_value = True

    file_obj = SwiftDataFile(filename="test.fits", path="data", url="http://example.com/test.fits", type="BAT")

    with patch("swifttools.swift_too.swift.data.httpx.stream") as mock_stream:
        mock_response = MagicMock()
        mock_response.headers.get.return_value = "100"
        mock_response.iter_bytes.return_value = [b"test"]
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_response.raise_for_status.return_value = None
        mock_stream.return_value = mock_response

        with patch("builtins.open", create=True):
            result = file_obj.download(outdir="/tmp")
            assert result is True


def test_swift_data_download_no_files():
    """Test download with no files"""
    data = SwiftData(obs_id="00012345001", autosubmit=False)
    data.entries = []
    result = data.download()
    assert result is False


@patch("swifttools.swift_too.swift.data.os.path.exists")
@patch("swifttools.swift_too.swift.data.os.path.expanduser")
@patch("swifttools.swift_too.swift.data.os.path.expandvars")
@patch("swifttools.swift_too.swift.data.os.path.abspath")
def test_swift_data_download_setup(mock_abspath, mock_expandvars, mock_expanduser, mock_exists):
    """Test download path setup"""
    mock_abspath.return_value = "/absolute/path"
    mock_expandvars.return_value = "/expanded/path"
    mock_expanduser.return_value = "/user/path"
    mock_exists.return_value = True

    data = SwiftData(obs_id="00012345001", outdir="~/data", autosubmit=False)
    data.entries = [SwiftDataFile(filename="test.fits", path="data", url="http://example.com/test.fits", type="BAT")]
    data.download()


def test_tooapi_download_data_download():
    """Test TOOAPIDownloadData download method"""
    mock_obj = MockDownloadData()
    with patch("swifttools.swift_too.swift.data.SwiftData") as mock_swift_data:
        mock_instance = MagicMock()
        mock_swift_data.return_value = mock_instance
        mock_instance.submit.return_value = None
        mock_instance.fetch = True
        mock_instance.download.return_value = None

        result = mock_obj.download()
        assert result == mock_instance

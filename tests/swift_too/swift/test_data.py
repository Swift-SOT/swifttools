import os
import tempfile
from unittest.mock import MagicMock, patch

import httpx
import pytest

from swifttools.swift_too.base.schemas import BaseSchema
from swifttools.swift_too.swift.data import SwiftData, SwiftDataFile, TOOAPIDownloadData


class MockDownloadData(BaseSchema, TOOAPIDownloadData):
    """Mock class to test TOOAPIDownloadData mixin"""

    obs_id: str = "00012345001"


@pytest.fixture
def swift_data():
    return SwiftData(autosubmit=False)


@pytest.fixture
def mock_boto3():
    with (
        patch("swifttools.swift_too.swift.data.boto3.client"),
        patch("swifttools.swift_too.swift.data.boto3.session.Session.client"),
    ):
        yield


class TestSwiftData:
    def test_init(self):
        """Test SwiftData initialization"""
        data = SwiftData(obs_id="00012345001", autosubmit=False)
        assert data.obs_id == "00012345001"

    def test_all_property(self, swift_data):
        """Test the 'all' property"""
        data = swift_data
        assert data.all is False
        data.xrt = True
        data.uvot = True
        data.bat = True
        data.log = True
        data.auxil = True
        data.tdrss = True
        assert data.all is True

    def test_all_setter(self, swift_data):
        """Test the 'all' property setter"""
        data = swift_data
        data.all = True
        assert data.xrt is True
        assert data.uvot is True
        assert data.bat is True
        assert data.log is True
        assert data.auxil is True
        assert data.tdrss is True

    def test_getitem(self, swift_data):
        """Test indexing"""
        data = swift_data
        # Use SwiftDataFile instances for entries
        file1 = SwiftDataFile(filename="file1", path="/", url="http://example.com/file1", type="file")
        file2 = SwiftDataFile(filename="file2", path="/", url="http://example.com/file2", type="file")
        data.entries = [file1, file2]
        assert data[0].filename == "file1"
        assert data[1].filename == "file2"

    def test_table_property(self, swift_data):
        """Test _table property"""
        data = swift_data
        data.entries = []
        _, table = data._table
        assert table == []

    @pytest.mark.usefixtures("mock_boto3")
    def test_post_process_aws(self):
        """Test _post_process with AWS setup"""
        data = SwiftData(obs_id="00012345001", uksdc=False, itsdc=False, aws=True, autosubmit=False)
        data._post_process()
        # Should have set up S3 client
        assert data._s3 is not None

    def test_download_no_files(self):
        """Test download with no files"""
        data = SwiftData(obs_id="00012345001", autosubmit=False)
        data.entries = []
        result = data.download()
        assert result is False

    @patch("swifttools.swift_too.swift.data.os.path.exists")
    @patch("swifttools.swift_too.swift.data.os.path.expanduser")
    @patch("swifttools.swift_too.swift.data.os.path.expandvars")
    @patch("swifttools.swift_too.swift.data.os.path.abspath")
    def test_download_setup(self, mock_abspath, mock_expandvars, mock_expanduser, mock_exists):
        """Test download path setup"""
        mock_abspath.return_value = "/absolute/path"
        mock_expandvars.return_value = "/expanded/path"
        mock_expanduser.return_value = "/user/path"
        mock_exists.return_value = True

        data = SwiftData(obs_id="00012345001", outdir="~/data", autosubmit=False, clobber=True)
        data.entries = [
            SwiftDataFile(filename="test.fits", path="data", url="http://example.com/test.fits", type="BAT")
        ]

        # Mock the download method to avoid actual network calls
        with patch.object(SwiftDataFile, "download", return_value=True):
            result = data.download()
            assert result is True

    def test_post_process_match_filtering(self):
        data = SwiftData(obs_id="00012345001", autosubmit=False, fetch=False)
        data.entries = [
            SwiftDataFile(filename="a.fits", path="p1", url="u1", type="t"),
            SwiftDataFile(filename="b.fits", path="p2", url="u2", type="t"),
            SwiftDataFile(filename="c.fits", path="p1", url="u3", type="t"),
        ]
        # single match string
        data.match = "p1/*"
        data._post_process()
        assert len(data.entries) == 2

    def test_post_process_fetch_calls_download(self):
        data = SwiftData(obs_id="00012345001", autosubmit=False, fetch=True)
        # Add a dummy entry so download doesn't return early
        file_obj = SwiftDataFile(filename="test.fits", path="data", url="http://example.com/test.fits", type="t")
        data.entries = [file_obj]
        # patch download to ensure it's called
        with patch.object(SwiftData, "download", return_value=True) as mock_download:
            data._post_process()
            assert mock_download.called is True

    def test_download_success_and_quiet_true(self, tmp_path):
        data = SwiftData(obs_id="00012345001", autosubmit=False)
        file_obj = SwiftDataFile(filename="test.fits", path="data", url="http://example.com/test.fits", type="t")
        data.entries = [file_obj]
        data.outdir = str(tmp_path)
        data.quiet = True
        data.clobber = False

        # make download return True
        with patch.object(SwiftDataFile, "download", return_value=True):
            _ = data.download()
        _, table = data._table
        print(f"Table: {table}")
        assert len(table) == 1  # We have 1 entry
        assert table[0][0] == "data"  # First file shows full path

    def test_download_existing_file_warns_and_localpath_indexing(self, tmp_path):
        out = tmp_path / "data"
        out.mkdir()
        file_path = out / "test.fits"
        file_path.write_bytes(b"abc")

        data = SwiftData(obs_id="00012345001", autosubmit=False)
        data.outdir = str(tmp_path)
        data.entries = [SwiftDataFile(filename="test.fits", path="data", url="u", type="t")]
        data.clobber = False
        data.quiet = False
        # index existing files should set localpath
        data.download()
        assert data.entries[0].localpath is not None

    def test_download_existing_file_warning(self, tmp_path):
        out = tmp_path / "data"
        out.mkdir()
        file_path = out / "test.fits"
        file_path.write_bytes(b"abc")

        data = SwiftData(obs_id="00012345001", autosubmit=False)
        data.outdir = str(tmp_path)
        data.entries = [SwiftDataFile(filename="test.fits", path="data", url="u", type="t")]
        # ensure existing file is detected and warning issued
        data.quiet = False
        data.clobber = False
        # Call download; should warn and not attempt download
        data.download()
        # No exception and method completes

    def test_download_file_download_failure(self, monkeypatch, tmp_path):
        data = SwiftData(obs_id="00012345001", autosubmit=False)
        file_obj = SwiftDataFile(filename="test.fits", path="data", url="http://example.com/test.fits", type="t")
        data.entries = [file_obj]
        data.outdir = str(tmp_path)

        # Make file_obj.download return False
        with patch.object(SwiftDataFile, "download", return_value=False):
            res = data.download()
            assert res is False
            assert data.status.status == "Rejected"


class TestSwiftDataFile:
    def test_size(self):
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

    @patch("swifttools.swift_too.swift.data.os.path.exists")
    def test_download_file(self, mock_exists):
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

    def test_download_heasarc_s3(self, tmp_path, monkeypatch):
        # heasarc url with s3 client download_file called
        file_obj = SwiftDataFile(
            filename="test.fits",
            path="data",
            url="https://heasarc.gsfc.nasa.gov/FTP/heasarc/path/test.fits",
            type="XRT",
        )
        s3 = MagicMock()
        # ensure directory creation works
        outdir = str(tmp_path)

        # Call download with s3; should call s3.download_file and return True
        res = file_obj.download(outdir=outdir, s3=s3)
        assert res is True
        # key name should be url replaced prefix
        key_name = file_obj.url.replace("https://heasarc.gsfc.nasa.gov/FTP/", "")
        s3.download_file.assert_called_once_with(
            "nasa-heasarc", key_name, os.path.join(outdir, file_obj.path, file_obj.filename)
        )

    def test_download_http_error(self, monkeypatch):
        file_obj = SwiftDataFile(filename="test.fits", path="data", url="http://example.com/test.fits", type="BAT")

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def raise_for_status(self):
                raise httpx.HTTPStatusError("error", request=MagicMock(), response=MagicMock())

        monkeypatch.setattr("swifttools.swift_too.swift.data.httpx.stream", lambda *a, **k: FakeResp())

        res = file_obj.download(outdir="/tmp")
        assert res is False

    def test_makedirs_and_s3_download(self, monkeypatch, tmp_path):
        # Ensure os.makedirs is called when fulldir doesn't exist and s3 branch used
        file_obj = SwiftDataFile(
            filename="test.fits",
            path="data",
            url="https://heasarc.gsfc.nasa.gov/FTP/heasarc/path/test.fits",
            type="XRT",
        )
        s3 = MagicMock()

        # simulate directory doesn't exist
        monkeypatch.setattr("swifttools.swift_too.swift.data.os.path.exists", lambda p: False)
        called = {"makedirs": False}

        def fake_makedirs(p):
            called["makedirs"] = True

        monkeypatch.setattr("swifttools.swift_too.swift.data.os.makedirs", fake_makedirs)

        res = file_obj.download(outdir=str(tmp_path), s3=s3)
        assert res is True
        assert called["makedirs"] is True

    def test_stream_zero_content_length(self, monkeypatch, tmp_path):
        file_obj = SwiftDataFile(filename="test.fits", path="data", url="http://example.com/test.fits", type="BAT")
        outdir = str(tmp_path)

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def raise_for_status(self):
                return None

            @property
            def headers(self):
                return {}

            def iter_bytes(self, chunk_size=8192):
                yield b"a"
                yield b"b"

        monkeypatch.setattr("swifttools.swift_too.swift.data.httpx.stream", lambda *a, **k: FakeResp())

        res = file_obj.download(outdir=outdir)
        assert res is True
        assert file_obj.localpath is not None


class TestTOOAPIDownloadData:
    def test_download(self):
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

    def test_download_does_not_call_download_twice(self):
        """TOOAPIDownloadData should not manually call download after submit."""
        mock_obj = MockDownloadData()
        with patch("swifttools.swift_too.swift.data.SwiftData") as mock_swift_data:
            mock_instance = MagicMock()
            mock_swift_data.return_value = mock_instance
            mock_instance.submit.return_value = None
            mock_instance.fetch = True

            _ = mock_obj.download()

            mock_instance.submit.assert_called_once()
            mock_instance.download.assert_not_called()

    def test_positional_and_anonymous_username(self):
        class HasObsNoUser(BaseSchema, TOOAPIDownloadData):
            obs_id: str = "000"

        obj = HasObsNoUser()
        with patch("swifttools.swift_too.swift.data.SwiftData") as mock_swift_data:
            inst = MagicMock()
            mock_swift_data.return_value = inst
            # Set up the mock to have _parameters and _local
            inst._parameters = [
                "username",
                "obsid",
                "quicklook",
                "auxil",
                "bat",
                "xrt",
                "uvot",
                "subthresh",
                "log",
                "tdrss",
                "uksdc",
                "itsdc",
            ]
            inst._local = [
                "outdir",
                "clobber",
                "obs_id",
                "targetid",
                "target_id",
                "seg",
                "segment",
                "shared_secret",
                "fetch",
                "match",
                "quiet",
                "aws",
            ]
            inst.fetch = True
            inst.download.return_value = None
            inst.submit.return_value = None

            obj.download("argval")
            mock_swift_data.assert_called_once()
            # positional arg should set obsid on instance
            assert getattr(inst, "obsid") == "argval"
            # username should be anonymous when not provided
            assert inst.username == "anonymous"

    def test_unexpected_kwarg_raises(self):
        class HasObs(BaseSchema, TOOAPIDownloadData):
            obs_id: str = "000"

        obj = HasObs()
        with pytest.raises(TypeError):
            obj.download(nonexistent=True)

    def test_sets_params_and_username(self):
        class HasObs(BaseSchema, TOOAPIDownloadData):
            obs_id: str = "000"
            username: str = "u"
            shared_secret: str = "s"

        obj = HasObs()
        with patch("swifttools.swift_too.swift.data.SwiftData") as mock_swift_data:
            inst = MagicMock()
            mock_swift_data.return_value = inst
            # Set up the mock to have _parameters and _local
            inst._parameters = [
                "username",
                "obsid",
                "quicklook",
                "auxil",
                "bat",
                "xrt",
                "uvot",
                "subthresh",
                "log",
                "tdrss",
                "uksdc",
                "itsdc",
            ]
            inst._local = [
                "outdir",
                "clobber",
                "obs_id",
                "targetid",
                "target_id",
                "seg",
                "segment",
                "shared_secret",
                "fetch",
                "match",
                "quiet",
                "aws",
            ]
            inst.fetch = True
            inst.download.return_value = None
            inst.submit.return_value = None

            obj.download("argsval", quicklook=True)
            # ensure SwiftData was instantiated and submit/download called
            mock_swift_data.assert_called_once()
            inst.submit.assert_called_once()

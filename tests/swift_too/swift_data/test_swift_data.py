import tempfile
from unittest.mock import MagicMock, Mock, patch

from swifttools.swift_too.swift.data import SwiftData, SwiftDataFile


class TestSwiftData:
    def test_init_with_defaults(self):
        """Test SwiftData initialization with default values."""
        data = SwiftData()
        assert data.auxil is True
        assert data.bat is False
        assert data.xrt is False
        assert data.uvot is False
        assert data.log is False
        assert data.tdrss is False
        assert data.quicklook is False
        assert data.uksdc is False
        assert data.itsdc is False
        assert data.subthresh is False
        assert data.outdir == "."
        assert data.clobber is False
        assert data.fetch is True
        assert data.quiet is False
        assert data.aws is False

    def test_init_with_obs_id(self):
        """Test SwiftData initialization with observation ID."""
        with patch("swifttools.swift_too.swift.data.SwiftData.validate_get") as mock_validate:
            mock_validate.return_value = False
            data = SwiftData(obs_id="00012345001")
            assert data.obs_id == "00012345001"

    def test_all_property_getter(self):
        """Test the all property getter returns True when all instruments are enabled."""
        data = SwiftData(xrt=True, uvot=True, bat=True, log=True, auxil=True, tdrss=True)
        assert data.all is True

    def test_all_property_getter_false(self):
        """Test the all property getter returns False when not all instruments are enabled."""
        data = SwiftData(xrt=True, uvot=False, bat=True, log=True, auxil=True, tdrss=True)
        assert data.all is False

    def test_all_property_setter(self):
        """Test the all property setter enables all instruments."""
        data = SwiftData()
        data.all = True
        assert data.xrt is True
        assert data.uvot is True
        assert data.bat is True
        assert data.log is True
        assert data.auxil is True
        assert data.tdrss is True

    def test_getitem(self):
        """Test accessing entries by index."""
        data = SwiftData()
        mock_file = SwiftDataFile(filename="test.fits", path="/test", url="http://test.com", type="test")
        data.entries = [mock_file]
        assert data[0] == mock_file

    def test_table_property(self):
        """Test the _table property returns correct format."""
        data = SwiftData()
        file1 = SwiftDataFile(filename="test1.fits", path="/path1", url="http://test.com", type="XRT")
        file2 = SwiftDataFile(filename="test2.fits", path="/path1", url="http://test.com", type="UVOT")
        file3 = SwiftDataFile(filename="test3.fits", path="/path2", url="http://test.com", type="BAT")
        data.entries = [file1, file2, file3]

        header, tabdata = data._table
        assert header == ["Path", "Filename", "Description"]
        assert len(tabdata) == 3
        assert tabdata[0] == ["/path1", "test1.fits", "XRT"]
        assert tabdata[1] == ["''", "test2.fits", "UVOT"]
        assert tabdata[2] == ["/path2", "test3.fits", "BAT"]

    @patch("boto3.client")
    def test_post_process_with_aws(self, mock_boto_client):
        """Test _post_process sets up S3 client when aws=True."""
        mock_s3_client = Mock()
        mock_boto_client.return_value = mock_s3_client

        data = SwiftData(aws=True, uksdc=False, itsdc=False)
        data._post_process()

        assert data._s3 == mock_s3_client
        mock_boto_client.assert_called_once()

    def test_post_process_with_match_filter(self):
        """Test _post_process filters files based on match pattern."""
        data = SwiftData(match="*.fits")
        file1 = SwiftDataFile(filename="test1.fits", path="/path", url="http://test.com", type="XRT")
        file2 = SwiftDataFile(filename="test2.txt", path="/path", url="http://test.com", type="LOG")
        file3 = SwiftDataFile(filename="test3.fits", path="/path", url="http://test.com", type="UVOT")
        data.entries = [file1, file2, file3]

        data._post_process()

        assert len(data.entries) == 2
        assert data.entries[0].filename == "test1.fits"
        assert data.entries[1].filename == "test3.fits"

    def test_post_process_with_multiple_match_patterns(self):
        """Test _post_process with multiple match patterns."""
        data = SwiftData(match=["*.fits", "*.log"])
        file1 = SwiftDataFile(filename="test1.fits", path="/path", url="http://test.com", type="XRT")
        file2 = SwiftDataFile(filename="test2.txt", path="/path", url="http://test.com", type="TEXT")
        file3 = SwiftDataFile(filename="test3.log", path="/path", url="http://test.com", type="LOG")
        data.entries = [file1, file2, file3]

        data._post_process()

        assert len(data.entries) == 2
        assert data.entries[0].filename == "test1.fits"
        assert data.entries[1].filename == "test3.log"

    def test_download_with_outdir_parameter(self):
        """Test download accepts outdir parameter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data = SwiftData()
            mock_file = Mock()
            mock_file.download.return_value = True
            mock_file.path = "test"
            mock_file.filename = "test.fits"
            data.entries = [mock_file]

            result = data.download(outdir=temp_dir)

            assert result is True
            assert data.outdir == temp_dir

    @patch("os.path.exists")
    def test_download_sets_localpath_for_existing_files(self, mock_exists):
        """Test download sets localpath for files that already exist."""
        mock_exists.return_value = True

        data = SwiftData(outdir="/test")
        mock_file = Mock()
        mock_file.path = "subdir"
        mock_file.filename = "test.fits"
        mock_file.download.return_value = True
        data.entries = [mock_file]

        data.download()

        assert mock_file.localpath == "/test/subdir/test.fits"

    @patch("warnings.warn")
    @patch("os.path.exists")
    def test_download_warns_on_existing_file_without_clobber(self, mock_exists, mock_warn):
        """Test download warns when file exists and clobber is False."""
        mock_exists.return_value = True

        data = SwiftData(outdir="/test", clobber=False, quiet=False)
        mock_file = Mock()
        mock_file.path = "subdir"
        mock_file.filename = "test.fits"
        mock_file.download.return_value = True
        data.entries = [mock_file]

        data.download()

        mock_warn.assert_called_once()

    def test_download_with_quiet_mode(self):
        """Test download doesn't use tqdm progress bar in quiet mode."""
        with patch("swifttools.swift_too.swift.data.tqdm") as mock_tqdm:
            data = SwiftData(quiet=True)
            mock_file = Mock()
            mock_file.download.return_value = True
            mock_file.path = "test"
            mock_file.filename = "test.fits"
            data.entries = [mock_file]

            data.download()

            mock_tqdm.assert_not_called()

    def test_download_handles_file_download_error(self):
        """Test download handles individual file download errors."""
        data = SwiftData()
        mock_file = Mock()
        mock_file.download.return_value = False
        mock_file.filename = "test.fits"
        mock_file.path = "test"
        data.entries = [mock_file]

        result = data.download()

        assert result is False


class TestSwiftDataFile:
    def test_init(self):
        """Test SwiftDataFile initialization."""
        file = SwiftDataFile(filename="test.fits", path="/test", url="http://test.com", type="XRT")
        assert file.filename == "test.fits"
        assert file.path == "/test"
        assert file.url == "http://test.com"
        assert file.type == "XRT"
        assert file.quicklook is False
        assert file.localpath is None

    @patch("os.path.getsize")
    def test_size_property_with_localpath(self, mock_getsize):
        """Test size property when file has been downloaded."""
        mock_getsize.return_value = 1024

        file = SwiftDataFile(
            filename="test.fits", path="/test", url="http://test.com", type="XRT", localpath="/local/test.fits"
        )

        assert file.size == 1024
        mock_getsize.assert_called_once_with("/local/test.fits")

    def test_size_property_without_localpath(self):
        """Test size property when file hasn't been downloaded."""
        file = SwiftDataFile(filename="test.fits", path="/test", url="http://test.com", type="XRT")

        assert file.size is None

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("requests.get")
    def test_download_success(self, mock_get, mock_exists, mock_makedirs):
        """Test successful file download."""
        mock_exists.return_value = False
        mock_response = Mock()
        mock_response.ok = True
        mock_response.raw.read.return_value = b"test data"
        mock_get.return_value = mock_response

        file = SwiftDataFile(filename="test.fits", path="subdir", url="http://test.com/test.fits", type="XRT")

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            result = file.download(outdir="/output")

            assert result is True
            mock_makedirs.assert_called_once_with("/output/subdir")
            mock_get.assert_called_once_with("http://test.com/test.fits", stream=True, allow_redirects=True)
            mock_file.write.assert_called_once_with(b"test data")

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("requests.get")
    def test_download_failure(self, mock_get, mock_exists, mock_makedirs):
        """Test file download failure."""
        mock_exists.return_value = False
        mock_response = Mock()
        mock_response.ok = False
        mock_get.return_value = mock_response

        file = SwiftDataFile(filename="test.fits", path="subdir", url="http://test.com/test.fits", type="XRT")

        result = file.download(outdir="/output")

        assert result is False

    @patch("os.makedirs")
    @patch("os.path.exists")
    def test_download_with_s3_heasarc_url(self, mock_exists, mock_makedirs):
        """Test download with HEASARC URL using S3."""
        mock_exists.return_value = False
        mock_s3 = Mock()
        mock_s3.download_file.return_value = None

        file = SwiftDataFile(
            filename="test.fits",
            path="subdir",
            url="https://heasarc.gsfc.nasa.gov/FTP/swift/data/test.fits",
            type="XRT",
            quicklook=False,
        )

        result = file.download(outdir="/output", s3=mock_s3)

        assert result is True
        mock_s3.download_file.assert_called_once_with(
            "nasa-heasarc", "swift/data/test.fits", "/output/subdir/test.fits"
        )

    @patch("os.path.exists")
    def test_download_creates_directories(self, mock_exists):
        """Test download creates necessary directories."""
        mock_exists.return_value = False

        file = SwiftDataFile(filename="test.fits", path="deep/nested/path", url="http://test.com/test.fits", type="XRT")

        with patch("os.makedirs") as mock_makedirs, patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.raw.read.return_value = b"test"
            mock_get.return_value = mock_response

            with patch("builtins.open", create=True):
                file.download(outdir="/output")

                mock_makedirs.assert_called_once_with("/output/deep/nested/path")

import os
import warnings
from fnmatch import fnmatch
from typing import Any, Optional

import boto3  # type: ignore[import-untyped]
import boto3.session  # type: ignore[import-untyped]
import requests
from botocore import UNSIGNED  # type: ignore[import-untyped]
from botocore.client import Config  # type: ignore[import-untyped]
from pydantic import Field
from tqdm.auto import tqdm  # type: ignore[import-untyped]

from .api_common import TOOAPIBaseclass
from .swift_schemas import BaseSchema


class SwiftDataGetSchema(BaseSchema):
    # username: str = "anonymous"
    obsid: str
    auxil: bool = True
    bat: bool = False
    xrt: bool = False
    uvot: bool = False
    log: bool = False
    tdrss: bool = False
    quicklook: bool = Field(default=False, description="If true, only quicklook data will be returned")
    uksdc: bool = False
    itsdc: bool = False
    subthresh: bool = False


class SwiftDataFile(BaseSchema):
    filename: str
    path: str
    url: str
    quicklook: bool = False
    type: str
    localpath: Optional[str] = None

    @property
    def size(self):
        if self.localpath is not None:
            return os.path.getsize(self.localpath)
        else:
            return None

    def download(
        self,
        outdir: str = ".",
        s3: Optional[Any] = None,
    ):
        """Download the file into a given `outdir`"""
        #        if outdir is not None:
        #            self.outdir = outdir
        # Make the directories for the full path if they don't exist
        fulldir = os.path.join(outdir, self.path)
        if not os.path.exists(fulldir):
            os.makedirs(fulldir)

        # Download the data
        fullfilepath = os.path.join(outdir, self.path, self.filename)

        if "heasarc" in self.url and self.quicklook is False and s3 is not None and hasattr(s3, "download_file"):
            # Download HEASARC hosted data from AWS
            key_name = self.url.replace("https://heasarc.gsfc.nasa.gov/FTP/", "")
            s3.download_file("nasa-heasarc", key_name, fullfilepath)
        else:
            r = requests.get(self.url, stream=True, allow_redirects=True)
            if r.ok:
                filedata = r.raw.read()
                with open(fullfilepath, "wb") as outfile:
                    outfile.write(filedata)
                self.localpath = fullfilepath
            else:
                return False

        return True


class SwiftDataSchema(BaseSchema):
    obsid: Optional[str] = None
    auxil: bool = True
    bat: bool = False
    xrt: bool = False
    uvot: bool = False
    log: bool = False
    tdrss: bool = False
    quicklook: bool = Field(default=False, description="If true, only quicklook data will be returned")
    uksdc: bool = False
    itsdc: bool = False
    subthresh: bool = False
    entries: list[SwiftDataFile] = []


class SwiftData(TOOAPIBaseclass, SwiftDataSchema):
    """
    Class to download Swift data from the UK or US SDC for a given observation
    ID.

    Attributes
    ----------
    obsid : str / int
        the observation ID of the data to download. Can be in SDC or spacecraft
        format. Note: can also use target_id and segment, but must supply both.
    auxil : boolean
        Set to True to download Auxillary data (default = True)
    bat : boolean
        Set to True to download BAT data.
    xrt : boolean
        Set to True to download XRT data.
    uvot : boolean
        Set to True to download UVOT data.
    log : boolean
        Set to True to download SDC processing logs.
    all : boolean
        Set to True to download all data products.
    quicklook : boolean
        Set to True to only search Quicklook data. Default searches archive,
        then quicklook if the data are not there. If data are known to be recent
        this may speed up result.
    clobber : boolean
        overwrite existing data on disk (default: False)
    outdir : str
        Directory where data should be downloaded to.
    fetch : boolean
        Download the data straight away (default: True).
    quiet  : boolean
        When downloading, don't print anything out. (default: False)
    entries : list
        List of files associated with data (')
    username : str
        username for TOO API (default 'anonymous')
    shared_secret : str
        shared secret for TOO API (default 'anonymous')
    status : TOOStatus
        Status of API request
    """

    # Core API definitions
    api_name: str = "Swift_Data"
    _schema = SwiftDataSchema
    _get_schema = SwiftDataGetSchema
    _endpoint = "/swift/data"

    # Local arguments
    outdir: str = "."
    clobber: bool = False
    fetch: bool = True
    match: Optional[str] = None
    quiet: bool = False
    aws: bool = False
    _s3: Optional[boto3.session.Session.client] = None

    def __getitem__(self, i):
        return self.entries[i]

    @property
    def _table(self):
        header = ["Path", "Filename", "Description"]
        tabdata = []
        lastpath = ""
        for file in self.entries:
            if file.path != lastpath:
                path = file.path
                lastpath = path
            else:
                path = "''"
            tabdata.append([path, file.filename, file.type])
        return header, tabdata

    @property
    def all(self):
        if self.xrt and self.uvot and self.bat and self.log and self.auxil and self.tdrss:
            return True
        return False

    @all.setter
    def all(self, bool):
        if self.all is not None:
            self.xrt = self.bat = self.uvot = self.log = self.auxil = self.tdrss = bool

    def _post_process(self):
        """A place to do things to API results after they have been fetched."""
        # Filter out files that don't match `match` expression
        if not self.uksdc and not self.itsdc and self.aws is True:
            # Set up S3 stuff
            config = Config(
                connect_timeout=5,
                retries={"max_attempts": 0},
                signature_version=UNSIGNED,
            )
            self._s3 = boto3.client("s3", config=config)

        if self.match is not None:
            if type(self.match) is str:
                self.match = [self.match]
            i = 0
            while i < len(self.entries):
                keep = False
                for match in self.match:
                    if fnmatch(f"{self.entries[i].path}/{self.entries[i].filename}", match):
                        keep = True
                if not keep:
                    del self.entries[i]
                else:
                    i += 1

    def download(self, outdir=None):
        """Download Swift data for selected instruments to `outdir`"""
        # If outdir is passed as an argument, update the value
        if outdir is not None:
            self.outdir = outdir

        # If no files, return error
        if len(self.entries) == 0:
            self.status.error(f"No data found for {self.obsid}.")
            self.status.status = "Rejected"
            return False

        # Translate any ~, "." and $ENV in the output path
        if self.outdir == "" or self.outdir is None:
            self.outdir = "."
        self.outdir = os.path.expanduser(self.outdir)
        self.outdir = os.path.expandvars(self.outdir)
        self.outdir = os.path.abspath(self.outdir)

        # Index any existing files
        for i in range(len(self.entries)):
            fullfilepath = os.path.join(self.outdir, self.entries[i].path, self.entries[i].filename)
            if os.path.exists(fullfilepath):
                self.entries[i].localpath = fullfilepath

        # Download files to outdir
        if self.quiet:
            dfiles = self.entries
        else:
            dfiles = tqdm(self.entries, desc="Downloading files", unit="files")
        for dfile in dfiles:
            # Don't re-download a file unless clobber=True
            localfile = f"{self.outdir}/{dfile.path}/{dfile.filename}"
            if not self.clobber and os.path.exists(localfile) and not self.quiet:
                warnings.warn(f"{dfile.filename} exists and not overwritten (set clobber=True to override this).")
            elif not dfile.download(outdir=self.outdir, s3=self._s3):
                self.status.error(f"Error downloading {dfile.filename}")
                return False

        # Everything worked we assume so return True
        return True


class TOOAPI_DownloadData:
    """Mixin to add add download method to any class that has an associated obsid."""

    def download(self, *args, **kwargs):
        """Download data from SDC"""
        # Set up the Data class
        data = SwiftData()
        params = SwiftData._parameters + SwiftData._local
        # Read in arguments
        for i in range(len(args)):
            setattr(data, params[i + 1], args[i])
        # Parse argument keywords
        for key in kwargs.keys():
            if key in params + self._local:
                setattr(data, key, kwargs[key])
            else:
                raise TypeError(f"{self.api_name} got an unexpected keyword argument '{key}'")
        # Set up and download data
        data.obsid = self.obsid
        data.username = self.username
        data.shared_secret = self.shared_secret
        data.submit()
        if data.fetch:
            data.download()
        # Return the Swift_Data class on completion
        return data


# Shorthand Aliases for better PEP8 compliant and future compat
Data = SwiftData
DataFile = SwiftDataFile
Swift_Data_File = SwiftDataFile
Swift_DataFile = SwiftDataFile
Swift_Data = SwiftData

from .api_common import TOOAPI_Baseclass
from .swift_obsid import TOOAPI_ObsID
from .api_status import TOOStatus
import requests
import os
from fnmatch import fnmatch

try:
    from tqdm.auto import tqdm
except ImportError:

    def tqdm(*args, **kwargs):
        """A real simple replacement for tqdm if it's not locally installed"""
        if "display" in kwargs.keys() and kwargs["display"] is not False:
            print(f"Downloading {len(args[0])} files...")
        return args[0]


class Swift_DataFile(TOOAPI_Baseclass):
    """Class containing information about a swift data file that can be
    downloaded from the Swift Science Data Center

    Attributes:
    ----------
    filename : str
        filename
    path : str
        path to file
    url : str
        URL where file exists
    type : str
        Text description of file type
    localpath : str
        full path of file on disk
    size : int
        size of file in bytes
    outdir : str
        local directory in which to download file (default '.')
    """

    # API name
    api_name = "Swift_Data_File"
    # Attributes
    filename = None
    path = None
    url = None
    quicklook = None
    type = None
    localpath = None
    outdir = "."
    # Core API definitions
    _parameters = ["filename", "path", "url", "quicklook", "type"]
    _attributes = ["size", "localpath"]

    @property
    def size(self):
        if self.localpath is not None:
            return os.path.getsize(self.localpath)
        else:
            return None

    def download(self, outdir=None):
        """Download the file into a given `outdir`"""
        if outdir is not None:
            self.outdir = outdir
        # Make the directories for the full path if they don't exist
        fulldir = os.path.join(self.outdir, self.path)
        if not os.path.exists(fulldir):
            os.makedirs(fulldir)

        # Download the data
        fullfilepath = os.path.join(self.outdir, self.path, self.filename)
        r = requests.get(self.url, stream=True, allow_redirects=True)
        if r.ok:
            filedata = r.raw.read()
            with open(fullfilepath, "wb") as outfile:
                outfile.write(filedata)
            self.localpath = fullfilepath
        else:
            return False

        return True


class Swift_Data(TOOAPI_Baseclass, TOOAPI_ObsID):
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
    api_name = "Swift_Data"
    # Classes used by this class
    _subclasses = [Swift_DataFile, TOOStatus]
    # Values to send and return through the API
    _parameters = [
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
    # Local and alias parameters
    _local = [
        "outdir",
        "clobber",
        "obsnum",
        "targetid",
        "target_id",
        "seg",
        "segment",
        "shared_secret",
        "fetch",
        "match",
        "quiet",
    ]
    _attributes = ["entries", "status"]

    def __init__(self, *args, **kwargs):
        """
        Construct the Swift_Data class, and download data if required parameters
        are supplied.

        Parameters
        ----------
        obsid : str / int
            the observation ID of the data to download. Can be in SDC or
            spacecraft format. Note: can also use target_id and segment, but
            must supply both.
        auxil : boolean
            Set to True to download Auxillary data (default = True)
        bat : boolean
            Set to True to download BAT data.
        xrt : boolean
            Set to True to download XRT data.
        uvot : boolean
            Set to True to download UVOT data.
        subthresh : boolean
            Set to True to download BAT Subthreshold trigger data
        log : boolean
            Set to True to download SDC processing logs.
        all : boolean
            Set to True to download all data products.
        uksdc : boolean
            Set to True to download from the UK Swift SDC
        itsdc : boolean
            Set to True to download from the Italian Swift SDC
        quicklook : boolean
            Set to True to only search Quicklook data. Default searches archive,
            then quicklook if the data are not there. If data are known to be
            recent this may speed up result.
        clobber : boolean
            overwrite existing data on disk (default: False)
        outdir : str
            Directory where data should be downloaded to.
        fetch : boolean
            Download the data straight away (default: True).
        quiet : boolean
            When downloading, don't print anything out. (default: False)
        match : str / list
            Only download files matching this filename pattern (e.g.
            "*xrt*pc*"). If multiple templates are given as a list, files
            matching any of filename patterns will be downloaded. Uses standard
            UNIX style filename pattern matching with Python `fnmatch` module.
        username : str
            username for TOO API (default 'anonymous')
        shared_secret : str
            shared secret for TOO API (default 'anonymous')
        """
        # Parameters
        self.username = "anonymous"
        self.obsid = None
        # Only look in quicklook
        self.quicklook = False
        # Download from UK SDC
        self.uksdc = None
        # Download from the Italian SDC
        self.itsdc = None
        # Data types to download. Always download auxil as default
        self.auxil = True
        self.bat = None
        self.uvot = None
        self.xrt = None
        self.tdrss = None
        self.subthresh = None
        self.log = None
        # Should we display anything when downloading
        self.quiet = False
        # Download data straight away
        self.fetch = True
        # Only download files matching this expression
        self.match = None
        # Default to not overwrite existing data
        self.clobber = False
        # Directory to save data
        self.outdir = "."
        # Parse argument keywords
        self._parseargs(*args, **kwargs)

        # The resultant data
        self.entries = list()
        self.status = TOOStatus()

        # See if we pass validation from the constructor, but don't record
        # errors if we don't
        if self.validate():
            self.submit()
            # ...and if requested, download the data
            if self.fetch:
                self.download()
        else:
            self.status.clear()

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
        if (
            self.xrt
            and self.uvot
            and self.bat
            and self.log
            and self.auxil
            and self.tdrss
        ):
            return True
        return False

    @all.setter
    def all(self, bool):
        if self.all is not None:
            self.xrt = self.bat = self.uvot = self.log = self.auxil = self.tdrss = bool

    def _post_process(self):
        """A place to do things to API results after they have been fetched."""
        # Filter out files that don't match `match` expression
        if self.match is not None:
            if type(self.match) is str:
                self.match = [self.match]
            i = 0
            while i < len(self.entries):
                keep = False
                for match in self.match:
                    if fnmatch(
                        f"{self.entries[i].path}/{self.entries[i].filename}", match
                    ):
                        keep = True
                if not keep:
                    del self.entries[i]
                else:
                    i += 1

    def validate(self):
        """Validate API submission before submit

        Returns
        -------
        bool
            Was validation successful?
        """
        if self.uksdc is True and self.itsdc is True:
            self.status.error("Cannot download from UK and Italian SDC")
        if self.obsid is None:
            self.status.error("Must supply Observation ID")
        if (
            self.auxil is not True
            and self.xrt is not True
            and self.log is not True
            and self.bat is not True
            and self.uvot is not True
            and self.subthresh is not True
        ):
            self.status.error("No data products selected")
            self.status.status = "Rejected"
        if len(self.status.errors) > 0:
            return False
        else:
            return True

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
            fullfilepath = os.path.join(
                self.outdir, self.entries[i].path, self.entries[i].filename
            )
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
            if not self.clobber and os.path.exists(localfile):
                print(
                    f"WARNING: {dfile.filename} exists and not overwritten (set clobber=True to override this)."
                )
            elif not dfile.download(outdir=self.outdir):
                self.status.error(f"Error downloading {dfile.filename}")
                return False

        # Everything worked we assume so return True
        return True


# Shorthand Aliases for better PEP8 compliant and future compat
Data = Swift_Data
DataFile = Swift_DataFile
Swift_Data_File = Swift_DataFile


class TOOAPI_DownloadData:
    """Mixin to add add download method to any class that has an associated obsid."""

    def download(self, *args, **kwargs):
        """Download data from SDC"""
        # Set up the Data class
        data = Swift_Data()
        params = Swift_Data._parameters + Swift_Data._local
        # Read in arguments
        for i in range(len(args)):
            setattr(data, params[i + 1], args[i])
        # Parse argument keywords
        for key in kwargs.keys():
            if key in params + self._local:
                setattr(data, key, kwargs[key])
            else:
                raise TypeError(
                    f"{self.api_name} got an unexpected keyword argument '{key}'"
                )
        # Set up and download data
        data.obsid = self.obsid
        data.username = self.username
        data.shared_secret = self.shared_secret
        data.submit()
        if data.fetch:
            data.download()
        # Return the Swift_Data class on completion
        return data

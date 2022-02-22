from .common import TOOAPI_Baseclass, TOOAPI_ObsID
from .too_server import Swift_TOO_User
from .swift_status import Swift_TOO_Status
from .swift_afst import Swift_AFST
import requests
from bs4 import BeautifulSoup
import os


class Swift_Data_File(TOOAPI_Baseclass):
    def __init__(self, filename=None, url=None, quicklook=None, fullpath=None, path=None):
        TOOAPI_Baseclass.__init__(self)
        self.filename = filename
        self.path = path
        self.fullpath = fullpath
        self.url = url
        self.quicklook = quicklook
        self._size = None
        self._type = None
        self.rows = ['filename', 'path', 'url', 'quicklook', 'type']
        self.extrarows = []

    @property
    def type(self):
        if 'xrt' in self.path:
            inst = 'XRT'
        elif 'bat' in self.path:
            inst = 'BAT'
        elif 'uvot' in self.path:
            inst = 'UVOT'
        elif 'auxil' in self.path:
            inst = 'Auxillary'
        elif 'log' in self.path:
            inst = "Log"

        if "po_" in self.filename:
            acs = "pointed"
        elif "sl_" in self.filename:
            acs = "slew"
        elif "st_" in self.filename:
            acs = "settling"
        elif "sp_" in self.filename:
            acs = "slew/point"
        else:
            acs = ''

        if "_uf" in self.filename:
            filter = "unfiltered"
        elif "_cl" in self.filename:
            filter = "cleaned"
        elif "_ex" in self.filename:
            filter = "exposure map"
        elif "_sk" in self.filename or "skim" in self.filename:
            filter = "sky"
        elif "_rw" in self.filename:
            filter = "raw"
        else:
            filter = ''

        if "xpc" in self.filename:
            mode = 'PC'
        elif 'xwt' in self.filename:
            mode = 'WT'
        elif 'xim' in self.filename:
            mode = 'Image'
        elif 'uuu' in self.filename:
            mode = 'u'
        elif 'uvv' in self.filename:
            mode = 'v'
        elif 'ubb' in self.filename:
            mode = 'b'
        elif 'uw1' in self.filename:
            mode = 'uvw1'
        elif 'uw2' in self.filename:
            mode = 'uvw2'
        elif 'um2' in self.filename:
            mode = 'uvm2'
        elif 'uwh' in self.filename:
            mode = 'white'
        else:
            mode = ''

        if 'hk' in self.path:
            dtype = 'housekeeping'
        elif 'event' in self.path:
            dtype = 'event'
        # elif 'image' in self.path:
        #    dtype = 'image'
        # elif 'products' in self.path:
        #    dtype = 'products'
        elif 'rate' in self.path:
            dtype = 'rate'
        elif 'masktag' in self.path:
            dtype = 'mask tagged'
        elif 'survey' in self.path:
            dtype = 'survey'
        else:
            dtype = ''

        if 'gif' in self.filename:
            filetype = 'GIF preview'
        elif 'lc' in self.filename:
            filetype = 'lightcurve'
        elif 'dph' in self.filename:
            filetype = 'DPH'
        elif 'hk' in self.filename and dtype != 'housekeeping':
            filetype = 'housekeeping'
        elif '.cat' in self.filename:
            filetype = 'catalog'
        elif 'img' in self.filename:
            filetype = 'image'
        elif 'at.fits' in self.filename:
            filetype = 'attitude file'
        else:
            filetype = 'file'
        return f"{inst} {acs} {filter} {mode} {dtype} {filetype}".strip().replace("  ", " ")

    @property
    def fullpath(self):
        return os.path.join(self.path, self.filename)

    @fullpath.setter
    def fullpath(self, fp):
        if fp is not None:
            self.path, self.filename = os.path.split(fp)

    @property
    def size(self):
        if self._size is None:
            self._size = int(requests.get(
                self.url, stream=True).headers['Content-length'])
        return self._size


class Swift_Data(TOOAPI_Baseclass, TOOAPI_ObsID):
    '''
    Class to download Swift data from the UK or US SDC for a given observation ID.
    '''

    # obsid=None,bat=None,xrt=None,uvot=None,uksdc=False,quicklook=False,outdir=".",all=None,clobber=False):
    def __init__(self, **kwargs):
        '''
        Construct the Swift_Data class, and download data if required parameters
        are supplied.

        Parameters
        ----------
            obsid : str / int
                the observation ID of the data to download. Can be in SDC or
                spacecraft format. Note: can also parse target_id and segment.
            auxil : boolean
                set to True to download Auxil data (default = True)
            bat : boolean
                set to True to download BAT data
            xrt : boolean
                set to True to download XRT data
            uvot : boolean
                set to True to download UVOT data
            log : boolean
                set to True to download SDC processing logs
            all : boolean
                set to True to download all data products
            quicklook : boolean
                set to True to only search Quicklook data. Default searches archive,
                then quicklook
            clobber : boolean
                overwrite existing data on disk (default: False)
            outdir : str
                directory where data should be downloaded to
        '''
        TOOAPI_Baseclass.__init__(self)
        TOOAPI_ObsID.__init__(self)
        self.obsid = None
        # Only look in quicklook
        self.quicklook = False
        self.uksdc = None
        # Two data locations "obs" = archive, "ql" = quicklook
        # Data types to download. Always download auxil as default
        self.auxil = True
        self.bat = None
        self.uvot = None
        self.xrt = None
        self.log = None
        self.clobber = False
        self.outdir = "."
        # Parse keywords
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
        # The files downloaded and the directories they live in
        self._files = list()
        self.directories = None
        self.datadir = None
        self.year = None
        self.month = None
        if self.obsid is not None:
            self.download()
        self.fileobj = []
        self.username = None
        self.subclasses = [Swift_Data_File]
        self.rows = ['username', 'obsid', 'quicklook',
                     'auxil', 'bat', 'xrt', 'uvot', 'log', 'uksdc']
        self.extrarows = ['entries', 'status']
        self.status = Swift_TOO_Status()
        self.user = Swift_TOO_User()

    def __getitem__(self, i):
        return self.entries[i]

    @property
    def table(self):
        header = ['Path', 'Filename', 'Size', 'Description']
        tabdata = []
        lastpath = ''
        for file in self.entries:
            if file.path != lastpath:
                path = file.path
                lastpath = path
            else:
                path = "''"
            tabdata.append([path, file.filename, file.size, file.type])
        return header, tabdata

    @property
    def all(self):
        if self.xrt and self.uvot and self.bat and self.log:
            return True
        return False

    @all.setter
    def all(self, bool):
        if self.all is not None:
            self.xrt = self.bat = self.uvot = self.log = self.auxil = bool

    def __find_latest_ql(self):
        '''For US SDC, look for the latest version of data available'''
        qldataurl = "https://swift.gsfc.nasa.gov/data/swift/"
        qldata = requests.get(qldataurl)
        ql = BeautifulSoup(qldata.text, 'html.parser')
        available = ql.find_all('pre')[0].text
        for line in available.splitlines():
            if self.obsid in line:
                return line.strip()
        return False

    @property
    def __datatype(self):
        '''For UK SDC, this is the difference between QL and Archive data'''
        if self.quicklook:
            return 'ql'
        else:
            return 'obs'

    @property
    def __top_dirs(self):
        '''Return the directories we want to download, based on requested'''
        dirs = []
        if self.auxil:
            dirs.append('auxil/')
        if self.xrt:
            dirs.append('xrt/')
        if self.bat:
            dirs.append('bat/')
        if self.uvot:
            dirs.append('uvot/')
        if self.log:
            dirs.append('log/')
        return dirs

    @property
    def dataurl(self):
        '''The URL for data, depending on which SDC you selected'''
        if self.uksdc:
            # UK SDC URLs are simples
            dataurl = f"http://www.swift.ac.uk/archive/{self.__datatype}/{self.obsid}"
            return dataurl
        else:
            # US SDC URLs are not
            if self.quicklook:
                # Quicklook data has different versions - figure out which version we need.
                if self.datadir is None:
                    self.datadir = self.__find_latest_ql()
                if self.datadir is False:
                    return False
                else:
                    # If we found the data, construct the URL and return it
                    dataurl = f"https://swift.gsfc.nasa.gov/data/swift/{self.datadir}"
                    return dataurl
            else:
                # US SDC puts data in directories by month, so we have to figure out what directory it's
                # going to be in first
                if self.year is None:
                    afst = Swift_AFST(obsnum=self.obsid)
                    afst.query()
                    if len(afst.entries) > 0:
                        self.year, self.month = afst.entries[0].begin.year, afst.entries[0].begin.month
                    else:
                        return False
                # Return the base URL for the data
                dataurl = f"https://heasarc.gsfc.nasa.gov/FTP/swift/data/obs/{self.year}_{self.month:02d}/{self.obsid}"
                return dataurl

    def scanfiles(self):
        '''Make a list of the available files and directories'''
        directories = self.__top_dirs

        if self.dataurl is False:
            return False
        # Scan through SDC web pages looking for files associated with ObsID
        i = 0
        subdir = requests.get(self.dataurl)
        while(i < len(directories)):
            url = f"{self.dataurl}/{directories[i]}"

            subdir = requests.get(url)

            if "Error 404" not in subdir.text and "Sorry" not in subdir.text:
                soup = BeautifulSoup(subdir.text, 'html.parser')
                links = soup.find_all('a')
                newdirs = [ld.text.strip() for ld in links if "/" in ld.text]
                newfiles = [lf.text.strip() for lf in links if "/" not in lf.text]
                [directories.append(f"{directories[i]}{ddir}")
                 for ddir in newdirs if ddir not in directories]
                self._files += [Swift_Data_File(fullpath=os.path.join(self.obsid, directories[i], dfile),
                                                url=f"{url}{dfile}", quicklook=self.quicklook) for dfile in newfiles if 'SWIFT_TLE_ARCHIVE' in dfile or self.obsid in dfile]
            i += 1

        self.directories = directories
        if len(self._files) > 0:
            return len(self._files)
        else:
            # Return False if nothing was found
            return False

    @property
    def files(self):
        '''A list of files associated with this obsid data'''
        # If no files, run scanfiles.
        if len(self._files) == 0:
            if not self.scanfiles() and self.quicklook is False:
                # If no files found in scan, and quicklook is not set, look in quicklook
                self.quicklook = True
                self.scanfiles()
        return self._files

    def validate(self):
        if self.obsid is None:
            self.status.error("Must supply Observation ID")
        if self.auxil is not True and self.xrt is not True and self.log is not True and self.bat is not True and self.uvot is not True:
            self.status.error("No data products selected")
        if len(self.status.errors) > 0:
            return False
        else:
            return True

    def query(self):
        if self.validate():
            self.entries = self.files
            if len(self.entries) == 0:
                self.status.error(
                    f"No data found for observation ID {self.obsid}")
            self.status.status = 'Accepted'
        else:
            self.status.status = 'Rejected'
